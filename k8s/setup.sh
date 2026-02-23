#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="photosafe"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BASE_DIR="${SCRIPT_DIR}/base"

echo "=== PhotoSafe Kubernetes Setup ==="
echo ""

# ── Pre-flight checks ────────────────────────────────────────────────
command -v kubectl >/dev/null 2>&1 || { echo "Error: kubectl not found"; exit 1; }

if ! kubectl cluster-info >/dev/null 2>&1; then
    echo "Error: cannot connect to a Kubernetes cluster"
    echo "Make sure your kubeconfig is set up correctly."
    exit 1
fi

# ── Resolve image owner ──────────────────────────────────────────────
REPO="${GITHUB_REPOSITORY:-}"
if [ -z "$REPO" ]; then
    REMOTE_URL=$(git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null || true)
    if [ -n "$REMOTE_URL" ]; then
        REPO=$(echo "$REMOTE_URL" | sed -E 's|.*github\.com[:/]||; s|\.git$||' | tr '[:upper:]' '[:lower:]')
    fi
fi

if [ -n "$REPO" ]; then
    echo "Detected repo: ${REPO}"
    echo "Images:  ghcr.io/${REPO}-backend / ghcr.io/${REPO}-frontend"
else
    echo "Warning: could not detect GitHub repo. OWNER placeholders will remain."
    echo "Set GITHUB_REPOSITORY=owner/repo and re-run, or edit the manifests manually."
fi

IMAGE_TAG="${IMAGE_TAG:-latest}"
echo "Tag:     ${IMAGE_TAG}"
echo ""

# ── Generate secrets if not already set ──────────────────────────────
SECRETS_FILE="${BASE_DIR}/secret.yaml"
if grep -q "CHANGE_ME" "$SECRETS_FILE"; then
    echo "Generating secrets..."
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    SECRET_KEY=$(openssl rand -hex 32)

    GENERATED_SECRETS=$(mktemp)
    sed \
        -e "s/POSTGRES_PASSWORD: \"CHANGE_ME\"/POSTGRES_PASSWORD: \"${POSTGRES_PASSWORD}\"/" \
        -e "s/SECRET_KEY: \"CHANGE_ME\"/SECRET_KEY: \"${SECRET_KEY}\"/" \
        "$SECRETS_FILE" > "$GENERATED_SECRETS"

    echo "  POSTGRES_PASSWORD and SECRET_KEY generated."
    echo "  (Stored in temporary file; originals in git are unchanged.)"
    echo ""
else
    GENERATED_SECRETS=""
fi

# ── Build manifests in a temp dir so we don't modify tracked files ───
WORK_DIR=$(mktemp -d)
trap 'rm -rf "$WORK_DIR"' EXIT

cp "$BASE_DIR"/*.yaml "$WORK_DIR/"

# Swap in generated secrets if we created them
if [ -n "$GENERATED_SECRETS" ]; then
    cp "$GENERATED_SECRETS" "$WORK_DIR/secret.yaml"
    rm "$GENERATED_SECRETS"
fi

# Replace OWNER placeholder with actual repo
if [ -n "$REPO" ]; then
    sed -i "s|ghcr.io/OWNER/photosafe-backend|ghcr.io/${REPO}-backend|g" "$WORK_DIR"/*.yaml
    sed -i "s|ghcr.io/OWNER/photosafe-frontend|ghcr.io/${REPO}-frontend|g" "$WORK_DIR"/*.yaml
fi

# Set image tag in kustomization
if [ -n "$REPO" ]; then
    sed -i "s|newTag: latest|newTag: ${IMAGE_TAG}|g" "$WORK_DIR/kustomization.yaml"
fi

# ── Apply ─────────────────────────────────────────────────────────────
echo "Applying manifests..."
kubectl apply -k "$WORK_DIR"
echo ""

# ── Wait for postgres first (backend depends on it) ──────────────────
echo "Waiting for postgres to be ready..."
kubectl rollout status statefulset/postgres -n "$NAMESPACE" --timeout=120s
echo ""

echo "Waiting for backend rollout..."
kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=300s
echo ""

echo "Waiting for frontend rollout..."
kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=180s
echo ""

# ── Summary ───────────────────────────────────────────────────────────
echo "=== Deployment complete ==="
echo ""
kubectl get pods -n "$NAMESPACE"
echo ""
kubectl get svc -n "$NAMESPACE"
echo ""
kubectl get ingress -n "$NAMESPACE" 2>/dev/null || true
