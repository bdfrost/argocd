# argocd: home lab GitOps

This repo is the single source of truth for my home Kubernetes cluster. ArgoCD watches it, and every workload, operator and piece of cluster plumbing below is declared here. Nothing is applied by hand. A merge to `main` is a deploy.

## How it works

```
apps/                     Helm chart that renders one ArgoCD Application per workload
  templates/app-of-apps.yaml   root Application → points ArgoCD at apps/
  templates/<app>.yaml         child Application → points at charts/<app>
charts/<app>/             per-app config: wrapper charts, local charts or kustomize
scripts/                  helpers for sealing secrets
renovate.json             automated dependency updates
```

- **App of apps:** one root `Application` renders a child `Application` for each service. Every app syncs automatically with `prune` and `selfHeal`, so drift is reverted and deleting a file removes the workload.
- **Three packaging styles, chosen per app:**
  - Wrapper charts that pin an upstream Helm chart and add local templates such as ingress or secrets (kube-prometheus-stack, immich, kagent).
  - Hand-written charts for apps that ship no chart (tracearr, which includes its own TimescaleDB and Redis StatefulSets).
  - Plain kustomize for small manifests (cert-manager, cleanuparr).
- **Starting point for new apps:** `apps/templates/_boilerplate` and `charts/boilerplate` scaffold a new service.

## Secrets

The repo is public, so no plaintext secrets are committed. All credentials are [Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets): they are encrypted with the cluster's public key, and only the in-cluster controller can decrypt them. `scripts/generate-secret.sh` and `scripts/seal-release-notify-webhook.sh` handle sealing. Config files that need tokens (for example `charts/kometa/config.yaml`) use placeholders that get filled in from sealed secrets at runtime.

## Platform

| Concern | Implementation |
|---|---|
| CNI | Flannel |
| Ingress | ingress-nginx; Cloudflare Tunnel (`cloudflared`) for selected external access |
| TLS | cert-manager with Let's Encrypt DNS-01 via Cloudflare |
| DNS | external-dns → Technitium over RFC2136 (TSIG) |
| Storage | Synology CSI (iSCSI) for dynamic PVs |
| Observability | kube-prometheus-stack (Alertmanager → Slack), Loki, Dozzle, Uptime Kuma with AutoKuma, custom *arr Prometheus exporters |
| Cluster hygiene | descheduler, Stakater Reloader, metrics-server |
| GPU | NVIDIA GPU Operator |
| Dashboard | Homepage, using in-cluster service discovery |

## AI / LLM

- **Ollama and Open WebUI:** self-hosted LLM inference on the NVIDIA GPU.
- **kagent:** Kubernetes-native AI agents, with a Postgres backend on Synology storage.

## Workloads

Media (Plex, Sonarr, Radarr, Prowlarr, Bazarr, SABnzbd, Tautulli, Seerr, Kometa, Maintainerr, Cleanuparr, Configarr, Tracearr), photos (Immich), plus utilities such as changedetection.io, speedtest-tracker and BirdNET-Go.

## Dependency management

Renovate scans every chart and manifest in the repo:

- Patch, minor and digest updates auto-merge through GitHub native automerge, and ArgoCD rolls them out.
- Major updates wait for manual review.
- A custom regex versioning rule handles Plex's `<version>-<git-hash>` image tags, which Renovate's default Docker versioning would otherwise silently skip.
