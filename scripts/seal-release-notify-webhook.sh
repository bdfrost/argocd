#!/bin/bash
# Seal the Slack webhook URL for the release-notify cronjob
# Usage: ./scripts/seal-release-notify-webhook.sh <slack-webhook-url>
# Example: ./scripts/seal-release-notify-webhook.sh https://hooks.slack.com/services/xxx/yyy/zzz

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CHART_DIR="${SCRIPT_DIR}/charts/configarr/templates"

if [ $# -ne 1 ]; then
  echo "Usage: $0 <slack-webhook-url>"
  echo "Seals the webhook URL into a SealedSecret for the release-notify cronjob"
  exit 1
fi

WEBHOOK_URL="$1"

# Create a temp secret file
TEMP_SECRET=$(mktemp /tmp/release-notify-secret-XXXXXX.yaml)
cat > "$TEMP_SECRET" <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: release-notify-webhook
  namespace: configarr
type: Opaque
data:
  webhook-url: $(echo -n "$WEBHOOK_URL" | base64 -w0)
EOF

# Seal it
echo "Sealing secret..."
kubeseal --format yaml --scope namespaced -o yaml < "$TEMP_SECRET" > "${CHART_DIR}/sealedsecret-release-notify.yaml"
rm "$TEMP_SECRET"

echo "Done! Sealed secret written to ${CHART_DIR}/sealedsecret-release-notify.yaml"
