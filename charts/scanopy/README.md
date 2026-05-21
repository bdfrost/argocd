# Scanopy placeholder

This chart is intentionally empty.

Scanopy was removed from the cluster, but the Argo CD Application still points at `charts/scanopy`. Keeping this empty chart allows Argo CD to render the application and prune any old Scanopy resources instead of failing with `app path does not exist`.
