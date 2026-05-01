# Lab 15 Report — StatefulSets & Persistent Storage

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Lab Points:** 12.5 pts = 10 + 2.5 bonus  
**Date:** May 1, 2026  

---

## Task 1 — StatefulSet Concepts

### 1.1 StatefulSet Guarantees

StatefulSet provides three key guarantees that Deployments cannot offer:

**Stable, unique network identifiers.** Each pod gets a predictable name
(`<statefulset>-0`, `<statefulset>-1`, ...) and keeps it across restarts
and rescheduling. A headless service enables direct DNS resolution to
individual pods.

**Stable, persistent storage.** Each pod gets its own PersistentVolumeClaim
created from `volumeClaimTemplates`. The PVC follows the pod through
rescheduling -- when a pod dies and restarts, it reattaches the same volume.

**Ordered, graceful deployment and scaling.** Pods start in ascending
order (0, 1, 2...) and terminate in reverse order. This matters for
clustered software where a leader must start first.

### 1.2 Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod naming | Random suffix (`app-5d8f-x7k2j`) | Ordinal index (`app-0`, `app-1`) |
| Storage | Shared PVC (all pods mount one volume) | Per-pod PVC via volumeClaimTemplates |
| Scaling order | Any order, parallel | Ordered: 0 -> 1 -> 2 |
| Network identity | Random, changes on restart | Stable DNS via headless service |
| Rolling updates | Parallel batches | Ordered or partitioned |
| Typical use case | Stateless APIs, web servers | Databases, message queues, clusters |

### 1.3 Headless Services

A headless service (`clusterIP: None`) does not load-balance traffic.
Instead, it creates DNS A records for every pod matching its selector.
This lets clients discover and connect to individual pods directly.

DNS pattern for StatefulSet pods:
```
<pod-name>.<headless-service>.<namespace>.svc.cluster.local
```

---

## Task 2 — Convert Deployment to StatefulSet

### 2.1 New Helm Templates

Created `templates/statefulset.yaml` with:

- `serviceName` pointing to headless service
- `volumeClaimTemplates` for per-pod PVCs (100Mi each, ReadWriteOnce)
- Configurable `podManagementPolicy` (OrderedReady / Parallel)
- Configurable `updateStrategy` (RollingUpdate with partition / OnDelete)
- All the same pod spec as the Deployment (env, probes, volumes, etc.)

Created `templates/headless-service.yaml`:

- `clusterIP: None` -- makes it a headless service
- Same selector labels as the main service
- Only created when `statefulset.enabled: true`

Updated `templates/pvc.yaml`: disabled when statefulset mode is active
(since StatefulSet creates PVCs via `volumeClaimTemplates`).

Updated `templates/deployment.yaml`: disabled when statefulset mode is active.

### 2.2 Values Configuration

Added `statefulset` section to `values.yaml`:

```yaml
statefulset:
  enabled: false
  podManagementPolicy: OrderedReady
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      partition: 0
```

Created `values-statefulset.yaml` for quick deployment:

```bash
helm install lab15-sts . -f values-statefulset.yaml
```

### 2.3 Deployed Resources

```
NAME                                    READY   AGE
statefulset.apps/lab15-sts-app-python   3/3     5m

NAME                         READY   STATUS    RESTARTS   AGE
lab15-sts-app-python-0       1/1     Running   0          5m
lab15-sts-app-python-1       1/1     Running   0          5m
lab15-sts-app-python-2       1/1     Running   0          5m

NAME                                TYPE        CLUSTER-IP      PORT(S)       AGE
lab15-sts-app-python                NodePort    10.105.90.217   80:30087/TCP  5m
lab15-sts-app-python-headless       ClusterIP   None            80/TCP        5m

NAME                                      STATUS   VOLUME                   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
data-lab15-sts-app-python-0               Bound    pvc-c3a43f73-...         100Mi      RWO            standard       5m
data-lab15-sts-app-python-1               Bound    pvc-51c9b5f1-...         100Mi      RWO            standard       5m
data-lab15-sts-app-python-2               Bound    pvc-75530e44-...         100Mi      RWO            standard       5m
```

Pods follow ordered naming (`-0`, `-1`, `-2`), headless service has
`CLUSTER-IP: None`, and each pod owns a dedicated 100Mi PVC.

---

## Task 3 — Headless Service & Pod Identity

### 3.1 DNS Resolution

Tested DNS resolution from pod-0 using Python's socket library:

```
Headless service resolves to all pods:
  ('10.244.1.27', 80)   # pod-0
  ('10.244.1.29', 80)   # pod-1
  ('10.244.1.30', 80)   # pod-2

Pod-1 resolves to:
  ('10.244.1.29', 80)

Pod-0 (self) resolves to:
  ('10.244.1.27', 80)
```

The headless service returns all pod IPs. Individual pod DNS
(`pod-1.headless-service`) resolves to exactly that pod's IP.
This is critical for peer discovery in clustered applications.

### 3.2 Per-Pod Storage Isolation

Wrote unique markers to each pod's `/data/visits` file, then read them back:

```
lab15-sts-app-python-0: pod-0-data-666
lab15-sts-app-python-1: pod-1-data-777
lab15-sts-app-python-2: pod-2-data-888
```

Each pod sees only its own data. With a Deployment using a shared PVC,
all pods would read the same value. StatefulSet's `volumeClaimTemplates`
guarantee complete storage isolation.

### 3.3 Persistence Test

```
Before deletion:
  lab15-sts-app-python-0: pod-0-data-666

$ kubectl delete pod lab15-sts-app-python-0
pod "lab15-sts-app-python-0" deleted

After restart:
  lab15-sts-app-python-0: pod-0-data-666
```

Data survived pod deletion. The PVC outlives the pod -- when the
StatefulSet controller recreates pod-0, it reattaches the same PVC.
This is the fundamental difference from ephemeral pod storage.

---

## Task 4 — Documentation

See `k8s/STATEFULSET.md` for the full documentation covering:

- StatefulSet overview and Deployment comparison
- Resource verification output
- DNS resolution evidence
- Per-pod storage isolation proof
- Persistence test results
- Bonus: update strategy demonstrations

---

## Bonus Task — Update Strategies

### Partitioned Rolling Update

Set `partition: 2` so only pods with ordinal >= 2 get updated:

```
Before (all on :latest):
  pod-0: timofeq1/devops-lab03-python:latest
  pod-1: timofeq1/devops-lab03-python:latest
  pod-2: timofeq1/devops-lab03-python:latest

After patch (partition=2, image=v1.0):
  pod-0: timofeq1/devops-lab03-python:latest   (unchanged)
  pod-1: timofeq1/devops-lab03-python:latest   (unchanged)
  pod-2: timofeq1/devops-lab03-python:v1.0     (updated!)
```

This is a canary pattern for stateful workloads. You update one pod
first, validate it, then lower the partition to roll out the update.
For a 5-replica StatefulSet with `partition: 3`, only pods 3 and 4
would update -- pods 0-2 stay on the old version.

### OnDelete Strategy

Pods only update when you manually delete them:

```
After switching to OnDelete + new image (v2.0):
  pod-0: ...:latest   (unchanged -- not deleted)
  pod-1: ...:latest   (unchanged -- not deleted yet)
  pod-2: ...:v1.0     (unchanged -- not deleted)

$ kubectl delete pod lab15-sts-app-python-1

After pod-1 restarts:
  pod-0: ...:latest   (still old)
  pod-1: ...:v2.0     (updated on restart!)
  pod-2: ...:v1.0     (still old)
```

Use cases:

- Databases where you must run manual failover or data migration
  before restarting each instance
- Clusters where you need to drain connections gracefully
- When you want full control over update ordering and timing

### Commands Reference

```bash
# Set partitioned rolling update
kubectl patch statefulset <name> --type=merge -p '{
  "spec": {
    "updateStrategy": {
      "type": "RollingUpdate",
      "rollingUpdate": { "partition": 2 }
    }
  }
}'

# Switch to OnDelete
kubectl patch statefulset <name> --type=merge -p '{
  "spec": {
    "updateStrategy": { "type": "OnDelete" }
  }
}'

# Check update strategy
kubectl get statefulset <name> -o jsonpath='{.spec.updateStrategy.type}'
```

---

## Helm Chart Files Changed

| File | Action | Description |
|------|--------|-------------|
| `templates/statefulset.yaml` | Created | StatefulSet with volumeClaimTemplates |
| `templates/headless-service.yaml` | Created | Headless service (clusterIP: None) |
| `templates/pvc.yaml` | Modified | Disabled when statefulset mode is on |
| `templates/deployment.yaml` | Modified | Disabled when statefulset mode is on |
| `values.yaml` | Modified | Added `statefulset` config section |
| `values-statefulset.yaml` | Created | Dedicated values for StatefulSet mode |

---

## Checklist Verification

- [x] StatefulSet guarantees documented (Task 1 above)
- [x] `statefulset.yaml` created with volumeClaimTemplates (Task 2)
- [x] Headless service created (Task 2)
- [x] Per-pod PVCs verified (Task 2 -- 3 PVCs, one per pod)
- [x] DNS resolution tested (Task 3.1)
- [x] Per-pod storage isolation proven (Task 3.2)
- [x] Persistence test passed (Task 3.3)
- [x] `k8s/STATEFULSET.md` complete (Task 4)
- [x] Bonus: Partitioned rolling update tested
- [x] Bonus: OnDelete strategy tested
