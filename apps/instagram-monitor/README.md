# Instagram Monitor

A Kubernetes CronJob that monitors an Instagram profile by checking its HTTP availability.

## Overview

This application runs on a configurable schedule and checks whether an Instagram profile is accessible. It exits with code 0 if the profile returns HTTP 200, or code 1 otherwise (enabling monitoring/alerting on failures).

## Configuration

| Environment Variable | Description | Default |
|---------------------|-------------|---------|
| `INSTAGRAM_USERNAME` | Instagram username to monitor | Required |
| `HTTP_TIMEOUT` | HTTP request timeout duration | `30s` |

## Building the Docker Image

```bash
# Standard build
docker build -t ghcr.io/bdfrost/instagram-monitor:latest apps/instagram-monitor/

# Multi-arch build (requires docker buildx)
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/bdfrost/instagram-monitor:latest \
  -f apps/instagram-monitor/Dockerfile.multi \
  --push apps/instagram-monitor/
```

## Deployment

Deployed via ArgoCD from `apps/templates/instagram-monitor.yaml`. The Helm chart at `charts/instagram-monitor/` creates a CronJob resource.

## Secret

The `INSTAGRAM_USERNAME` is sourced from `instagram-monitor-secret`. Create this as a SealedSecret before deployment.
