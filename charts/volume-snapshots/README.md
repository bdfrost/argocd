# volume-snapshots

Nightly CSI snapshots of the Synology iSCSI PVCs.

- `snapshot-controller` (piraeus chart) owns the VolumeSnapshot CRDs and binds
  VolumeSnapshots to the Synology CSI snapshotter sidecar in `synology-csi`.
- `snapscheduler` (backube) creates a VolumeSnapshot per PVC on each schedule and
  expires the oldest past `maxCount`.
- This chart runs `volume-snapshots-sync`, an hourly CronJob that:
  1. finds every PVC on a `synology-csi-iscsi-*` StorageClass, cluster-wide;
  2. applies the `nightly` SnapshotSchedule (from the `snapshotschedule`
     ConfigMap) into each of those namespaces, so new apps are covered with no
     edits and schedule changes in `values.yaml` roll out within the hour;
  3. audits that each PVC has a ready snapshot younger than
     `maxSnapshotAgeHours`. If not, the job fails and `KubeJobFailed` fires to
     Slack; its logs list the stale PVCs.

  The `nightly` schedules are created by the job, not by Argo, so they don't
  show in the Argo app. Each snapshot is a LUN snapshot on the NAS (visible in
  DSM under Snapshot Replication > LUN).

Snapshots are crash-consistent and live on the same NAS volume as the data: they
cover bad upgrades and deletions, not NAS loss.

## Check

```sh
kubectl get snapshotschedule -A
kubectl get volumesnapshot -A    # READYTOUSE should be true
kubectl -n volume-snapshots logs job/$(kubectl -n volume-snapshots get job -o name | tail -1 | cut -d/ -f2)
```

## Restore a PVC

Restoring creates a new PVC from the snapshot; the original is left untouched
until you delete it.

1. Pick a snapshot: `kubectl -n <ns> get volumesnapshot`.
2. Create the restored PVC (same size or larger than the source):

   ```yaml
   apiVersion: v1
   kind: PersistentVolumeClaim
   metadata:
     name: <pvc>-restore
     namespace: <ns>
   spec:
     storageClassName: synology-csi-iscsi-delete
     accessModes: [ReadWriteOnce]
     resources:
       requests:
         storage: <size>
     dataSource:
       apiGroup: snapshot.storage.k8s.io
       kind: VolumeSnapshot
       name: <snapshot>
   ```

3. Point the workload at it: change `claimName` in the chart to `<pvc>-restore`
   and commit. For a one-off file recovery instead, mount it in a throwaway pod
   and copy what you need.
4. Once the app is healthy on the restored PVC, remove the old PVC from the chart.

For an in-place rollback without changing the chart, scale the workload to 0
and use DSM: Snapshot Replication > Snapshots > LUN > Snapshot List > Restore.
