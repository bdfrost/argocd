# HolmesGPT

Deploys the CNCF HolmesGPT HTTP API from the upstream `robusta/holmes` chart.

## Required secret

Provision this secret in the `holmesgpt` namespace before syncing:

| Secret | Key | Purpose |
|---|---|---|
| `holmesgpt-llm-keys` | `OPENAI_API_KEY` | OpenAI model access |

The chart references the secret with `envFrom`; no credential is stored in Git.

## DNS and TLS

The Ingress requests `holmesgpt.frost.haus` and `holmesgpt-cert`. The public DNS zone for `holmesgpt.frost.haus` is delegated to Gandi, while this cluster's ExternalDNS instance manages only `frost.haus` through RFC2136. Create the `holmesgpt.frost.haus` DNS record at Gandi pointing to the public ingress endpoint, and ensure the ingress endpoint forwards TCP 80/443 to this cluster before syncing. cert-manager will then obtain `holmesgpt-cert` using the existing `letsencrypt` ClusterIssuer.

## API

The Holmes service is available inside the cluster as `holmesgpt-holmes:80`. The chart's HTTP API listens on port 5050 behind that Service. The public endpoint is `https://holmesgpt.frost.haus/api/chat` after DNS and TLS are ready.
