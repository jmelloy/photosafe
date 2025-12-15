#!/bin/sh

export GIT_SHA=$(git rev-parse --short HEAD)
docker compose build