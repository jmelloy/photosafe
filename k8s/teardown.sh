#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="photosafe"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="${SCRIPT_DIR}/base"

echo "=== PhotoSafe Kubernetes Teardown ==="
echo ""

command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl not found"; exit 1; }

if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "Error: cannot connect to a Kubernetes cluster"
    exit 1
fi

# Check if the namespace even exists
if ! kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
    echo "Namespace '${NAMESPACE}' does not exist. Nothing to tear down."
    exit 0
fi

# ── Show what's running ───────────────────────────────────────────────
echo "Current resources in namespace '${NAMESPACE}':"
echo ""
kubectl get all -n "$NAMESPACE" 2>/dev/null || true
echo ""
kubectl get pvc -n "$NAMESPACE" 2>/dev/null || true
echo ""

# ── Confirm ───────────────────────────────────────────────────────────
DELETE_DATA="${DELETE_DATA:-}"
if [ "$DELETE_DATA" != "yes" ]; then
    read -r -p "Delete all PhotoSafe resources? This will remove running services. [y/N] " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
fi

# ── Scale down gracefully ─────────────────────────────────────────────
echo ""
echo "Scaling down deployments..."
kubectl scale deployment/backend deployment/frontend --replicas=0 -n "$NAMESPACE" 2>/dev/null || true

echo "Scaling down statefulsets..."
kubectl scale statefulset/postgres --replicas=0 -n "$NAMESPACE" 2>/dev/null || true

# ── Delete resources via kustomize ────────────────────────────────────
echo ""
echo "Deleting Kubernetes resources..."
kubectl delete -k "$BASE_DIR" --ignore-not-found 2>/dev/null || true

# ── Handle PVCs (StatefulSet PVCs aren't managed by kustomize) ────────
PVCS=$(kubectl get pvc -n "$NAMESPACE" -o name 2>/dev/null || true)
if [ -n "$PVCS" ]; then
    echo ""
    echo "Remaining PersistentVolumeClaims:"
    kubectl get pvc -n "$NAMESPACE"
    echo ""

    if [ "$DELETE_DATA" = "yes" ]; then
        delete_pvcs="y"
    else
        read -r -p "Delete PVCs? THIS WILL DESTROY ALL DATA (database + uploads). [y/N] " delete_pvcs
    fi

    if [[ "$delete_pvcs" =~ ^[Yy]$ ]]; then
        echo "Deleting PVCs..."
        kubectl delete pvc --all -n "$NAMESPACE"
    else
        echo "PVCs preserved. Data will be available on next setup."
    fi
fi

# ── Delete namespace ──────────────────────────────────────────────────
echo ""
if [ "$DELETE_DATA" = "yes" ]; then
    delete_ns="y"
else
    read -r -p "Delete the '${NAMESPACE}' namespace? [y/N] " delete_ns
fi

if [[ "$delete_ns" =~ ^[Yy]$ ]]; then
    echo "Deleting namespace..."
    kubectl delete namespace "$NAMESPACE" --ignore-not-found
else
    echo "Namespace preserved."
fi

echo ""
echo "=== Teardown complete ==="
