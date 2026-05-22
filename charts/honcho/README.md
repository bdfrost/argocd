# Honcho

This chart deploys self-hosted Honcho into the `honcho` namespace via Argo CD.

Components:
- Honcho API (`ghcr.io/plastic-labs/honcho`)
- Honcho deriver worker (`python -m src.deriver`)
- pgvector Postgres (`pgvector/pgvector:pg15`)
- Redis cache/queue
- nginx Ingress at `honcho.frost.haus`

Before enabling auth or real memory derivation, create a sealed secret named
`honcho-env-secrets` in the `honcho` namespace. Common keys:

```bash
kubectl create secret generic honcho-env-secrets   --namespace honcho   --from-literal=LLM_OPENAI_API_KEY=...   --from-literal=AUTH_JWT_SECRET=...   --dry-run=client -o yaml > honcho-env-secrets.yaml
kubeseal -f honcho-env-secrets.yaml -o yaml -w charts/honcho/templates/sealedsecret.yaml
rm honcho-env-secrets.yaml
```

If you enable `config.auth.useAuth`, `AUTH_JWT_SECRET` is required.
