# CLAUDE.md

GitOps repo for a home Kubernetes cluster. ArgoCD syncs `main` automatically, so **a merge to `main` is a deploy**. The repo is public: never commit plaintext secrets, kubeconfigs or `.kube/` cache.

## Layout

- `apps/`: Helm chart that renders one ArgoCD `Application` per workload. `apps/templates/app-of-apps.yaml` is the root; `apps/values.yaml` holds the shared repoURL, targetRevision and destination server.
- `charts/<app>/`: the config for each app.
- `scripts/`: helpers for sealing secrets.
- `renovate.json`: automated dependency updates. Patch, minor and digest updates automerge; majors wait for review.

## Adding a new app

Do it all in one commit, modelled on the most similar existing app.

### 1. Application: `apps/templates/<app>.yaml`

Copy `apps/templates/_boilerplate` and replace `boilerplate` with the app name.

- `metadata.namespace: argocd`
- `source.path: charts/<app>`
- Destination namespace is the app name.
- `repoURL`, `targetRevision` and `server` come from `{{ .Values.spec.* }}`.
- Keep the standard sync policy: automated `prune` + `selfHeal`, syncOptions `CreateNamespace=true`, `PrunePropagationPolicy=foreground`, `PruneLast=true`, and an empty `managedNamespaceMetadata:`.
- Add anything else only when needed, with a comment explaining why. Examples: `ServerSideApply=true` for CRDs over the 256KB annotation limit (kagent, loki, kube-prometheus-stack); `ignoreDifferences` scoped to a field that changes at runtime (plex).

### 2. Chart: `charts/<app>/`

Pick the lightest style that fits.

- **Hand-written chart** (default for single-container apps; start from `charts/boilerplate`):
  - `values.yaml`: `name`, `targetPort`, `puid`/`pgid`, `image.{repository,tag,pullPolicy}`.
  - Deployment: `strategy: Recreate`, label `app: <name>`, `TZ=America/Chicago`.
  - Config PVC `<name>-config-pvc` on `synology-csi-iscsi-delete` (ReadWriteOnce, 2Gi unless the app needs more), mounted at `/config`.
  - Media apps (arr family) also mount NFS `192.168.100.250:/volume1/media` at `/data`, with PUID 1026 and PGID 100 so permissions work on the Synology.
  - Service: ClusterIP, port 80 named `http`, pointing at `targetPort`.
- **Wrapper chart**: list the upstream chart under `dependencies:` in `Chart.yaml` and nest overrides under the subchart's key in `values.yaml`. Put our own ingress or SealedSecret in `templates/` when the upstream chart's don't fit. Examples: immich, tautulli, seerr, kagent, kube-prometheus-stack. If upstream publishes no chart artifact, vendor it and document re-vendoring in a README (tracearr).
- **Plain kustomize**: `kustomization.yaml` plus manifests, for small sets like Prometheus exporters (exportarr + Service + ServiceMonitor) and CronJobs.

### 3. Ingress

- Host `<app>.frost.haus`, `ingressClassName: nginx`, `pathType: ImplementationSpecific`, path `/`, backend port name `http`.
- Annotations: `cert-manager.io/cluster-issuer: letsencrypt` and `external-dns.alpha.kubernetes.io/host: <app>.frost.haus`.
- TLS: `secretName: <app>-cert`.

### 4. Secrets

- Only SealedSecrets, committed in `templates/sealedsecret.yaml` (cluster-wide scope). Seal values with `scripts/generate-secret.sh`.
- Don't use Helm `rand`/autogenerate helpers: they regenerate on every render and fight self-heal.
- If the pod has to restart when a secret changes, add `reloader.stakater.com/auto: "true"` to the pod template annotations.

### 5. Homepage card

In `charts/homepage/templates/cm.yaml`, add an entry to the right group (for example Media Management) with `icon`, `href: https://<app>.frost.haus` and `description`.

### 6. Uptime monitor

In `charts/uptime-kuma/templates/autokuma-configmap.yaml`, add a key `<app>.json` holding an `http` monitor: `name`, `url: https://<app>.frost.haus`, `interval: 60`, `max_retries: 2`, `accepted_statuscodes: ["200-299"]`, `notification_names: ["slack"]`.

AutoKuma uses the key (minus `.json`) as the monitor's id, so keys can be added, removed or reordered freely. Removing a key deletes that monitor in Kuma. Renaming a key recreates the monitor and loses its history.

## Conventions

- Pin exact image tags; never use `latest`. Use `pullPolicy: IfNotPresent`.
- Add a `# renovate: datasource=docker depName=<image>` comment above the tag when Renovate can't infer the image. Add `versioning=loose` for non-semver tags.
- Comment any non-obvious workaround inline, saying why it exists. Examples in the repo: `ARR_MCP_PORT` being clobbered by service-link env vars; the initContainer that seeds config from a secret.
- Nothing is applied by hand with `kubectl apply`. Every change goes through git.
- Monitoring: Prometheus reads ServiceMonitors and PodMonitors from every namespace, so a chart's own `serviceMonitor.enabled` is enough (no `release` label). PrometheusRules still need `release: kube-prometheus-stack`.
- Grafana dashboards are JSON files in `charts/kube-prometheus-stack/dashboards/`; each becomes a ConfigMap in the Homelab folder. Build or edit in Grafana, export the JSON (keep the `uid`), and commit it there. UI edits to provisioned dashboards don't persist.
- Don't commit dependency tgz files under `charts/<app>/charts/` (gitignored). ArgoCD runs `helm dependency build` from `Chart.lock`; a committed tgz wins silently, so Renovate's bumps stop deploying (kube-prometheus-stack, immich and kagent sat on old versions this way until Nov 2026). tautulli and uptime-kuma still track theirs, at the locked version.
- Commit messages use conventional commits: `feat(<app>): add …`, `fix(<app>): …`, `chore(<app>): …`. For new apps, the body is a bullet list of each file group and the reasoning behind it.
