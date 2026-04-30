# Lab 12 - ConfigMaps and Persistent Volumes

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Date:** 2026-04-16  
**Lab Points:** 12.5 pts = 10 + 2.5 bonus

## Task 1 - Application Persistence Upgrade (2 pts)

### 1. Application code changes

Updated Python app to persist visits in a file and expose a new endpoint.

Changed files:
- `app_python/app.py`
- `app_python/tests/test_app.py`
- `app_python/docker-compose.yml`
- `app_python/README.md`
- `app_python/.gitignore`

Implementation details:
- Added file-backed visits counter (`VISITS_FILE`, default `data/visits`)
- Added thread safety with `threading.Lock`
- Added atomic file write (`os.replace`) using a temp file
- Added startup initialization to create/fix counter file
- Root endpoint `/` now increments and persists visits
- New endpoint `/visits` returns current persisted count

### 2. Local docker persistence test evidence

Run summary:

```bash
$ cd app_python
$ mkdir -p data
$ chmod 777 data
$ docker compose up -d --build
```

Service health evidence:

```bash
$ docker compose ps
NAME               IMAGE                       COMMAND           SERVICE   STATUS          PORTS
app-python-lab12   devops-lab12-python:local  "python app.py"  app       Up 40 seconds   0.0.0.0:5000->5000/tcp
```

Visits persistence evidence:

```bash
$ curl -s http://127.0.0.1:5000/visits
{"visits":0,"storage":"/app/data/visits"}

$ curl -s http://127.0.0.1:5000/ > /dev/null
$ curl -s http://127.0.0.1:5000/ > /dev/null

$ curl -s http://127.0.0.1:5000/visits
{"visits":2,"storage":"/app/data/visits"}

$ cat data/visits
2
```

After container restart, counter stayed persisted:

```bash
$ docker compose restart
$ curl -s http://127.0.0.1:5000/visits
{"visits":2,"storage":"/app/data/visits"}
```

Unit tests:

```bash
$ /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/app_python/venv/bin/python -m pytest -q
.....                                                                    [100%]
5 passed in 0.36s
```

## Task 2 - ConfigMaps (3 pts)

### 1. Config files and templates

Added:
- `k8s/app-python/files/config.json`
- `k8s/app-python/templates/configmap.yaml`

`configmap.yaml` renders two ConfigMaps:
- file-based config map: `<release>-app-python-config`
- env vars config map: `<release>-app-python-env`

### 2. Deployment integration

Updated:
- `k8s/app-python/templates/deployment.yaml`
- `k8s/app-python/templates/_helpers.tpl`
- `k8s/app-python/values.yaml`
- `k8s/app-python/values-dev.yaml`
- `k8s/app-python/values-prod.yaml`

What was added:
- file ConfigMap mounted at `/config`
- env ConfigMap injected with `envFrom.configMapRef`
- values for app name/environment/logging/visits path

### 3. Verification outputs

Helm lint/template verification:

```bash
$ helm lint k8s/app-python
1 chart(s) linted, 0 chart(s) failed

$ grep -nE 'kind: ConfigMap|kind: PersistentVolumeClaim|checksum/config|mountPath: /config|mountPath: /data|claimName:' /tmp/lab12-template.yaml
32:kind: ConfigMap
62:kind: ConfigMap
79:kind: PersistentVolumeClaim
146:        checksum/config: 78eba908eac136ef761c9d241aca710676316bdb0c3419dc8f57ab71bf789f62
171:              mountPath: /config
174:              mountPath: /data
206:            claimName: lab12-check-app-python-data
```

In-cluster evidence:

```bash
$ kubectl get configmap,pvc -l app.kubernetes.io/instance=lab12-cfg
NAME                                    DATA   AGE
configmap/lab12-cfg-app-python-config   1      29s
configmap/lab12-cfg-app-python-env      4      29s

NAME                                              STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/lab12-cfg-app-python-data   Bound    pvc-173cafb1-d947-4fe8-9c2f-7dcc71038b55   100Mi      RWO            standard       29s
```

Mounted file in pod:

```bash
$ kubectl exec <pod> -- cat /config/config.json
{
  "application": {
    "name": "devops-info-service",
    "environment": "dev",
    "logLevel": "debug"
  },
  "featureFlags": {
    "visitsEndpoint": true,
    "metricsEnabled": true
  },
  "settings": {
    "visitsFile": "/data/visits",
    "readinessPath": "/health"
  }
}
```

ConfigMap data and environment variables in pod:

```bash
$ kubectl get configmap lab12-cfg-app-python-env -o yaml
data:
  APP_ENV: dev
  APP_NAME: devops-info-service
  LOG_LEVEL: debug
  VISITS_FILE: /data/visits
```

```bash
$ kubectl exec <pod> -- sh -c 'printenv | sort | grep -E "APP|LOG_LEVEL|VISITS_FILE"'
APP_ENV=dev
APP_NAME=devops-info-service
LOG_LEVEL=debug
VISITS_FILE=/data/visits
```

## Task 3 - Persistent Volumes (3 pts)

### 1. PVC and mount implementation

Added:
- `k8s/app-python/templates/pvc.yaml`

PVC values in chart:
- `persistence.enabled`
- `persistence.accessMode` (ReadWriteOnce)
- `persistence.size`
- `persistence.storageClass`
- `persistence.mountPath` (`/data`)

Deployment mounts:
- volume `data-volume` from PVC
- mount path `/data`

### 2. Persistence test (pod deletion)

Command evidence:

```bash
POD_BEFORE_DELETE=lab12-cfg-app-python-f984479d-5n2rq
VISITS_BEFORE_HITS:
{"visits":0,"storage":"/data/visits"}
200
200
VISITS_AFTER_HITS:
{"visits":2,"storage":"/data/visits"}
DATA_FILE_BEFORE_DELETE:
2
pod "lab12-cfg-app-python-f984479d-5n2rq" deleted
pod/lab12-cfg-app-python-f984479d-cqqbf condition met
POD_AFTER_DELETE=lab12-cfg-app-python-f984479d-cqqbf
VISITS_IN_NEW_POD:
{"visits":2,"storage":"/data/visits"}
DATA_FILE_IN_NEW_POD:
2
```

Conclusion:
- Data persisted through pod deletion and recreation.
- PVC-backed file `/data/visits` preserved the counter.

## Task 4 - Documentation and Comparison (2 pts)

### ConfigMap vs Secret

Use ConfigMap when:
- data is not sensitive
- you need plain app config (feature flags, environment, logging settings)

Use Secret when:
- data is sensitive (passwords, API keys, tokens, certificates)
- you need stronger handling and restricted access

Key differences:
- sensitivity: ConfigMap non-sensitive, Secret sensitive
- storage type: both in Kubernetes API, but Secret should be protected with RBAC and etcd encryption at rest
- usage patterns: both can be mounted as files and injected as env vars

## Bonus Task - ConfigMap Hot Reload (2.5 pts)

### 1. Default ConfigMap update behavior

Patched ConfigMap directly and observed mounted file update delay.

Immediate check (no update yet):

```bash
PATCH_START=2026-04-16T19:06:22Z
FILE_BEFORE_PATCH:
    "logLevel": "debug"
configmap/lab12-cfg-app-python-config patched
FILE_IMMEDIATELY_AFTER_PATCH:
    "logLevel": "debug"
PATCH_END=2026-04-16T19:06:22Z
```

Later check (updated in mounted file):

```bash
CHECK_TIME=2026-04-16T19:07:08Z
    "logLevel": "hotreload-test"
```

Observed delay in this run: up to ~46 seconds.

### 2. subPath limitation

`subPath` does not receive ConfigMap updates because Kubernetes bind-mounts a specific file path and does not keep it linked to projected volume updates.

Use `subPath` when:
- you need one file from a volume at a custom path
- and you accept no live updates

Avoid `subPath` when:
- you need automatic ConfigMap refresh in running pods

### 3. Implemented reload approach

Implemented pod restart on config changes via checksum annotation in deployment template:

```yaml
metadata:
  annotations:
    checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

This is the chosen hot-reload strategy (restart-based).

### 4. Helm upgrade pattern evidence

After setting `appConfig.logLevel=error` with Helm upgrade:

```bash
POD_BEFORE=lab12-cfg-app-python-947654fbc-xzjhj
CHECKSUM_BEFORE=1e35b03e8bd9d766d37e335b30d0eaefc8cb09eeb82bead8f6d647af9d74afc4

POD_AFTER=lab12-cfg-app-python-6db876d6b7-hwm9g
CHECKSUM_AFTER=4a2af3420a838c13dc4b9dc5acc09d1b17d3f2b0b916926ed9072dab68f96821

FILE_LOGLEVEL_AFTER_CHECKSUM_UPGRADE:
    "logLevel": "error"
```

Result:
- checksum changed
- pod name changed (new ReplicaSet rollout)
- mounted config reflects updated value

### Operational note from testing

Manual `kubectl patch` against a Helm-managed ConfigMap caused an SSA conflict on next upgrade.
Resolved by using:

```bash
helm upgrade ... --server-side true --force-conflicts
```

## Checklist

### Task 1 - Application Persistence Upgrade (2 pts)
- [x] Visits counter implemented
- [x] `/visits` endpoint created
- [x] Counter persists in file
- [x] Docker Compose volume configured
- [x] Local testing successful
- [x] README updated

### Task 2 - ConfigMaps (3 pts)
- [x] `files/config.json` created
- [x] ConfigMap template for file mounting
- [x] ConfigMap template for env vars
- [x] ConfigMap mounted as file in pod
- [x] Environment variables injected
- [x] Verification outputs collected

### Task 3 - Persistent Volumes (3 pts)
- [x] PVC template created
- [x] PVC mounted to deployment
- [x] Visits file stored on PVC
- [x] Persistence tested (pod deletion)
- [x] Data survives pod restart

### Task 4 - Documentation (2 pts)
- [x] LAB12.md complete
- [x] Application changes documented
- [x] ConfigMap implementation documented
- [x] PVC implementation documented
- [x] Verification outputs included

### Bonus - ConfigMap Hot Reload (2.5 pts)
- [x] Update delay tested
- [x] subPath limitation documented
- [x] Reload mechanism implemented
- [x] Documentation complete