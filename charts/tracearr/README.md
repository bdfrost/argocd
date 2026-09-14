# Tracearr

Helm chart for [Tracearr](https://github.com/connorgallopo/Tracearr) — real-time
monitoring / account-sharing detection for Plex (with Jellyfin and Emby support),
a Tautulli alternative. Fastify + Socket.io server with TimescaleDB (PostgreSQL 18)
and Redis backing stores.

## Provenance — vendored upstream chart

`templates/` and `Chart.yaml` are vendored **verbatim** from the upstream chart
shipped in the app repo (it is not published as an OCI artifact):

- Source: <https://github.com/connorgallopo/Tracearr/tree/v2.2.3/docker/helm/tracearr>
- Vendored: 2026-09-14, chart version `2.2.3`
- Upstream files unmodified. The only local addition is
  `templates/sealedsecret.yaml` (cluster convention: SealedSecrets live with
  the chart). **Everything else cluster-specific belongs in `values.yaml`**
  (mirrors how `charts/tautulli` / `charts/seerr` track upstream charts while
  keeping local values).

### To update

1. Fetch the new upstream templates over this directory, verbatim:
   ```bash
   base="https://raw.githubusercontent.com/connorgallopo/Tracearr/vX.Y.Z/docker/helm/tracearr"
   cd charts/tracearr
   for f in _helpers.tpl deployment.yaml ingress.yaml networkpolicy.yaml \
     pvc-backups.yaml pvc-image-cache.yaml redis-service.yaml redis-statefulset.yaml \
     secret.yaml service.yaml serviceaccount.yaml timescale-service.yaml \
     timescale-statefulset.yaml NOTES.txt; do
     curl -sfL "$base/templates/$f" -o "templates/$f" || echo "FAILED $f"
   done
   ```
   (upstream files only — this leaves `templates/sealedsecret.yaml` in place;
   it has no upstream counterpart and must survive re-vendoring).
2. Bump `version` + `appVersion` in `Chart.yaml` to the release the templates
   came from (upstream syncs the chart version to each release tag).
3. Re-verify the three image tags still exist, and refresh the digest
   comments in `values.yaml` (`tracearr.image.tag` + the two DB/cache tags).
4. `helm lint . && helm template . -n tracearr` and diff the render vs. live.

## Notes (upstream)

The upstream chart ships rolling image tags. Here each image is selected by
human-readable tag (Renovate keeps it current via its `docker` datasource),
with the registry-verified digest recorded in the adjacent comment for audit.

Upstream's `secrets.autoGenerate` rand helper is deliberately not used under
Argo CD self-heal (it would repersist new values on every comparison).
`secrets.existingSecret` is set to `tracearr`; the chart omits its Secret
template when an existingSecret is configured. The Secret is provisioned by
`templates/sealedsecret.yaml` (committed with freshly sealed, randomly
generated values — same convention as `charts/poterie`).

Keys: `JWT_SECRET`, `COOKIE_SECRET`, `DB_PASSWORD` (used by the chart's
secretKeyRefs) and `BETTER_AUTH_SECRET` (injected via `tracearr.extraEnv` —
upstream recommends setting it explicitly so rotating JWT_SECRET does not
silently invalidate mobile-device sessions).

To rotate:

```bash
JWT=*** rand -hex 32); COOKIE=$(openssl rand -hex 32)
AUTH=*** rand -hex 32); DBPASS=$(openssl rand -hex 24)
kubectl create secret generic tracearr -n tracearr \
  --from-literal=JWT_SECRET="$JWT" --from-literal=COOKIE_SECRET="$COOKIE" \
  --from-literal=BETTER_AUTH_SECRET="$AUTH" --from-literal=DB_PASSWORD="$DBPASS" \
  --dry-run=client -o yaml | \
kubeseal --format yaml --scope=strict \
  --controller-name sealed-secrets-controller --controller-namespace kube-system \
  > charts/tracearr/templates/sealedsecret.yaml
```

(this cluster's controller runs as `sealed-secrets-controller` in `kube-system`
— not kubeseal's defaults, hence the explicit flags).

### Storage sizing

The cluster's Synology iSCSI CSI is late-binding and thin-provisioned, so
requests are headroom rather than allocations on the NAS:

| PVC | Size | Purpose |
| --- | ---- | ------- |
| `data-tracearr-timescale-0` (timescale volumeClaimTemplate) | 20Gi | TimescaleDB data |
| `data-tracearr-redis-0` (redis volumeClaimTemplate) | 2Gi | Redis AOF |
| `tracearr-backups` | 2Gi | app pg_dump backups |
| `tracearr-image-cache` | 2Gi | server logo cache |

`backups`/`image-cache` match upstream defaults; upstream's 50Gi database PVC
was right-sized to 20Gi here — watch DB growth after a Tautulli history import
and resize deliberately (CSI `allowVolumeExpansion: true`).
