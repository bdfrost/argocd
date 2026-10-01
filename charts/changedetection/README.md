# changedetection.io

Deploys the official `dgtlmoon/changedetection.io` image with a persistent `/datastore` PVC.

## Access

The app is available on the internal nginx ingress at `https://changedetection.frost.haus`. No Cloudflare Tunnel is configured for this host. changedetection.io does not require a password by default; set one in **Settings → General** if you want application-level authentication on the LAN.

The app stores its watch list, settings, and snapshots in `/datastore` on a 2Gi Synology CSI volume. The PVC survives chart upgrades, but Argo CD will prune it if the application is removed; back up the datastore before uninstalling. Private and reserved IP targets are blocked by default; changing `allowIanaRestrictedAddresses` can expose internal services to server-side request forgery risks.

The base deployment uses changedetection.io's built-in HTTP fetcher. Websites requiring JavaScript rendering need an additional Playwright browser service and `PLAYWRIGHT_DRIVER_URL`; that optional component is not enabled here.
