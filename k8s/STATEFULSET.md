# StatefulSet Implementation — Lab 15

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Lab Points:** 12.5 pts = 10 + 2.5 bonus  
**Date:** May 1, 2026  

---

## 1. StatefulSet Overview

### Why StatefulSet?

A regular Deployment treats all pods as interchangeable -- they get random
suffixes, share a single PVC (if configured), and can be scaled or replaced
in any order. This works great for stateless apps, but falls apart when
each instance needs its own identity and storage.

StatefulSet gives us three guarantees:

- **Stable, unique network identifiers.** Each pod gets a predictable name
  like `<name>-0`, `<name>-1`, and keeps it across restarts.
- **Stable, persistent storage.** Each pod gets its own PVC via
  `volumeClaimTemplates`, and the PVC follows the pod through rescheduling.
- **Ordered, graceful deployment and scaling.** Pods start in order (0, 1,
  2...) and terminate in reverse order (2, 1, 0).

### Deployment vs StatefulSet

| Feature | Deployment | StatefulSet |
|---------|------------|-------------|
| Pod Names | Random suffix (e.g., `app-5d8f7b9c-x7k2j`) | Ordinal index (e.g., `app-0`, `app-1`) |
| Storage | Shared PVC (all pods mount same volume) | Per-pod PVC via `volumeClaimTemplates` |
| Scaling | Any order, all at once | Ordered: 0, then 1, then 2 |
| Network ID | Random, changes on restart | Stable DNS name via headless service |
| Rolling Update | All pods updated in parallel batches | Ordered or partitioned |
| Use Case | Stateless web servers, APIs | Databases, queues, distributed systems |

### Examples of Stateful Workloads

- Databases: PostgreSQL, MySQL, MongoDB
- Message queues: Kafka, RabbitMQ
- Distributed systems: Elasticsearch, Cassandra, Zookeeper
- Any app that needs per-instance persistent state

### Headless Services

A headless service has `clusterIP: None`. Instead of load-balancing to a
random pod, it creates DNS A records for every pod that matches its
selector. This lets you reach individual pods directly:

```
<pod>-<n>.<headless-service>.<namespace>.svc.cluster.local
```

For example:
```
lab15-sts-app-python-0.lab15-sts-app-python-headless.default.svc.cluster.local
lab15-sts-app-python-1.lab15-sts-app-python-headless.default.svc.cluster.local
lab15-sts-app-python-2.lab15-sts-app-python-headless.default.svc.cluster.local
```

---

## 2. Resource Verification

### StatefulSet, Pods, Services, PVCs

```
$ kubectl get statefulset,pods,svc,pvc -l app.kubernetes.io/instance=lab15-sts

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

Key observations:

- Pods have ordered names: `...-0`, `...-1`, `...-2`
- Headless service has `CLUSTER-IP: None`
- Three separate PVCs, one per pod, each 100Mi

---

## 3. Network Identity

DNS resolution test from pod-0:

```
$ kubectl exec lab15-sts-app-python-0 -- python3 -c "
import socket
print('Headless service resolves to all pods:')
for ip in socket.getaddrinfo('lab15-sts-app-python-headless', 80):
    print(f'  {ip[4]}')
print()
print('Pod-1 resolves to:')
for ip in socket.getaddrinfo('lab15-sts-app-python-1.lab15-sts-app-python-headless', 80):
    print(f'  {ip[4]}')
print()
print('Pod-0 (self) resolves to:')
for ip in socket.getaddrinfo('lab15-sts-app-python-0.lab15-sts-app-python-headless', 80):
    print(f'  {ip[4]}')
"

Headless service resolves to all pods:
  ('10.244.1.27', 80)   # pod-0
  ('10.244.1.29', 80)   # pod-1
  ('10.244.1.30', 80)   # pod-2

Pod-1 resolves to:
  ('10.244.1.29', 80)

Pod-0 (self) resolves to:
  ('10.244.1.27', 80)
```

The headless service DNS returns all pod IPs. Individual pod DNS names
resolve to their specific IP. This is how distributed systems like Kafka
or Elasticsearch discover peers in a cluster.

### DNS Naming Pattern

```
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
```

Example:
```
lab15-sts-app-python-1.lab15-sts-app-python-headless.default.svc.cluster.local
```

---

## 4. Per-Pod Storage Evidence

Each pod writes to its own independent PVC. We wrote unique markers to
each pod and confirmed they are isolated:

```
$ kubectl exec lab15-sts-app-python-0 -- sh -c "echo 'pod-0-data-666' > /data/visits"
$ kubectl exec lab15-sts-app-python-1 -- sh -c "echo 'pod-1-data-777' > /data/visits"
$ kubectl exec lab15-sts-app-python-2 -- sh -c "echo 'pod-2-data-888' > /data/visits"

$ for pod in lab15-sts-app-python-0 lab15-sts-app-python-1 lab15-sts-app-python-2; do
    echo "$pod: $(kubectl exec $pod -- cat /data/visits)"
done

lab15-sts-app-python-0: pod-0-data-666
lab15-sts-app-python-1: pod-1-data-777
lab15-sts-app-python-2: pod-2-data-888
```

Each pod sees only its own data. No cross-pod leakage. This is because
each pod has its own PVC created by `volumeClaimTemplates`, unlike a
Deployment where all pods share one PVC.

---

## 5. Persistence Test

Data survives pod deletion -- the PVC is independent of the pod lifecycle:

```
$ kubectl exec lab15-sts-app-python-0 -- cat /data/visits
pod-0-data-666

$ kubectl delete pod lab15-sts-app-python-0
pod "lab15-sts-app-python-0" deleted

$ kubectl wait --for=condition=Ready pod/lab15-sts-app-python-0 --timeout=120s
pod/lab15-sts-app-python-0 condition met

$ kubectl exec lab15-sts-app-python-0 -- cat /data/visits
pod-0-data-666
```

The data is still there after pod deletion and restart. The StatefulSet
controller reattaches the same PVC to the new pod automatically.

---

## 6. Update Strategies (Bonus)

### Partitioned Rolling Update

With `partition: 2`, only pods with ordinal >= 2 get updated:

```
$ kubectl patch statefulset lab15-sts-app-python --type=merge -p='{
  "spec": {
    "updateStrategy": {
      "type": "RollingUpdate",
      "rollingUpdate": { "partition": 2 }
    },
    "template": {
      "spec": { "containers": [{ "name": "app-python", "image": "timofeq1/devops-lab03-python:v1.0" }] }
    }
  }
}'

After update:
  lab15-sts-app-python-0: timofeq1/devops-lab03-python:latest   (unchanged)
  lab15-sts-app-python-1: timofeq1/devops-lab03-python:latest   (unchanged)
  lab15-sts-app-python-2: timofeq1/devops-lab03-python:v1.0     (updated!)
```

This is like a canary for stateful workloads -- update one pod first,
verify it works, then lower the partition to roll out to the rest.

### OnDelete Strategy

Pods only update when manually deleted:

```
$ kubectl patch statefulset ... -p '{"spec":{"updateStrategy":{"type":"OnDelete"}}}'

Before manual deletion:
  lab15-sts-app-python-0: ...:latest   (unchanged)
  lab15-sts-app-python-1: ...:latest   (unchanged)
  lab15-sts-app-python-2: ...:v1.0     (unchanged)

$ kubectl delete pod lab15-sts-app-python-1

After pod-1 restarts:
  lab15-sts-app-python-0: ...:latest   (still old)
  lab15-sts-app-python-1: ...:v2.0     (updated on restart!)
  lab15-sts-app-python-2: ...:v1.0     (still old)
```

Use cases: databases where you want full control over when each instance
restarts, or when you need to run manual migration steps before each pod
update.

---

## 7. Helm Chart Structure

Files added/modified for this lab:

- `templates/statefulset.yaml` -- StatefulSet resource with volumeClaimTemplates
- `templates/headless-service.yaml` -- Headless service (clusterIP: None)
- `templates/pvc.yaml` -- Updated: disabled when statefulset mode is on
- `templates/deployment.yaml` -- Updated: disabled when statefulset mode is on
- `values.yaml` -- Added `statefulset` configuration section
- `values-statefulset.yaml` -- New: dedicated values file for StatefulSet mode

Deploy command:
```bash
helm install lab15-sts . -f values-statefulset.yaml
```
