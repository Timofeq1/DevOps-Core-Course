# Lab 10 - Helm Package Manager

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Date:** 2026-04-02  
**Lab Points:** 14.5 pts = 12 + 2.5 bonus

## Task 1 - Helm Fundamentals (2 pts)

### 1. Helm concepts and value proposition

Helm is a package manager for Kubernetes that provides:
- Reusable chart packaging of manifests
- Strong parameterization through values files
- Lifecycle management (install, upgrade, rollback, uninstall)
- Versioned releases and release history
- Hook-based lifecycle automation

In this lab, Helm reduced duplication and made environment changes (dev/prod) manageable without copying manifests.

### 2. Helm installation verification

```bash
$ helm version
version.BuildInfo{Version:"v4.1.3", GitCommit:"c94d381b03be117e7e57908edbf642104e00eb8f", GitTreeState:"clean", GoVersion:"go1.25.8", KubeClientVersion:"v1.35"}
```

### 3. Repository setup and chart exploration

```bash
$ helm repo add bitnami https://charts.bitnami.com/bitnami
"bitnami" has been added to your repositories

$ helm repo update
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "bitnami" chart repository
Update Complete. Happy Helming!

$ helm search repo bitnami/nginx | head -n 5
NAME                             CHART VERSION   APP VERSION   DESCRIPTION
bitnami/nginx                    22.6.10         1.29.7        NGINX Open Source is a web server...
bitnami/nginx-ingress-controller 12.0.7          1.13.1        NGINX Ingress Controller is an Ingress...
bitnami/nginx-intel              2.1.15          0.4.9         DEPRECATED NGINX Open Source for Intel...
```

```bash
$ helm show chart bitnami/nginx | sed -n '1,80p'
apiVersion: v2
name: nginx
version: 22.6.10
appVersion: 1.29.7
dependencies:
- name: common
  repository: oci://registry-1.docker.io/bitnamicharts
  version: 2.37.0
description: NGINX Open Source is a web server that can be also used as a reverse proxy...
```

Note: Attempting `prometheus-community` repository in this environment timed out once due network instability, but repository setup and public chart exploration were completed with `bitnami` and OCI-backed charts.

## Task 2 - Create Your Helm Chart (3 pts)

### 1. Chart initialization and metadata

Created chart:
- `k8s/app-python`

Key metadata in `k8s/app-python/Chart.yaml`:
- `apiVersion: v2`
- `type: application`
- `version: 0.1.0`
- `appVersion: "1.0.0"`
- dependency on `common-lib`

### 2. Converted manifests to templates

Converted Lab 9 manifests into Helm templates:
- `k8s/deployment.yml` -> `k8s/app-python/templates/deployment.yaml`
- `k8s/service.yml` -> `k8s/app-python/templates/service.yaml`

Added:
- `k8s/app-python/templates/ingress.yaml` (optional, values-controlled)
- `k8s/app-python/templates/hooks/pre-install-job.yaml`
- `k8s/app-python/templates/hooks/post-install-job.yaml`

### 3. Values extraction and templating

Main values extracted into `k8s/app-python/values.yaml`:
- image repository/tag/pull policy
- replica count
- service type/port/targetPort/nodePort
- resource requests/limits
- liveness and readiness probe configs
- hook settings

### 4. Health checks retained and configurable

Both probes are active in `templates/deployment.yaml` and sourced from values:
- `readinessProbe` from `.Values.readinessProbe`
- `livenessProbe` from `.Values.livenessProbe`

No probe is commented out.

### 5. Validation evidence

```bash
$ helm dependency update app-python
Saving 1 charts
Deleting outdated charts

$ helm lint app-python
==> Linting app-python
[INFO] Chart.yaml: icon is recommended

1 chart(s) linted, 0 chart(s) failed
```

```bash
$ helm template app-python app-python > /tmp/lab10-app-python-template.yaml
$ grep -nE 'kind: Deployment|replicas:|kind: Service|type:|helm.sh/hook' /tmp/lab10-app-python-template.yaml
4:kind: Service
14:  type: NodePort
27:kind: Deployment
37:  replicas: 3
104:    "helm.sh/hook": post-install
136:    "helm.sh/hook": pre-install
```

## Task 3 - Multi-Environment Support (2 pts)

### 1. Environment files

Created:
- `k8s/app-python/values-dev.yaml`
- `k8s/app-python/values-prod.yaml`

### 2. Environment differences

`values-dev.yaml`:
- `replicaCount: 1`
- smaller requests/limits
- `service.type: NodePort`

`values-prod.yaml`:
- `replicaCount: 5`
- larger requests/limits
- `service.type: LoadBalancer`
- production probe delays
- image tag pinned to `1.0.0`

### 3. Environment rendering checks

```bash
$ helm template app-python-dev app-python -f app-python/values-dev.yaml > /tmp/lab10-app-python-dev-template.yaml
$ helm template app-python-prod app-python -f app-python/values-prod.yaml > /tmp/lab10-app-python-prod-template.yaml
$ grep -nE 'replicas:|type: NodePort|nodePort:' /tmp/lab10-app-python-dev-template.yaml
14:  type: NodePort
23:      nodePort: 30080
37:  replicas: 1

$ grep -nE 'replicas:|type: LoadBalancer|nodePort:' /tmp/lab10-app-python-prod-template.yaml
14:  type: LoadBalancer
36:  replicas: 5
```

### 4. Live install and upgrade evidence

Dev install (NodePort adjusted to avoid existing Lab 9 service conflict):

```bash
$ helm install lab10-dev app-python -f app-python/values-dev.yaml --set service.nodePort=30081 --wait --timeout 240s
NAME: lab10-dev
STATUS: deployed
DESCRIPTION: Install complete
```

```bash
$ kubectl get deployment lab10-dev-app-python
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
lab10-dev-app-python   1/1     1            1           ...
```

Prod upgrade:

```bash
$ helm upgrade lab10-dev app-python -f app-python/values-prod.yaml --wait --timeout 240s
Error: UPGRADE FAILED: ... ImagePullBackOff ...
```

Failure reason was network restriction pulling uncached tag `1.0.0` from Docker Hub in this environment.

Successful production-profile upgrade with temporary cached image override:

```bash
$ helm upgrade lab10-dev app-python -f app-python/values-prod.yaml --set image.tag=latest --wait --timeout 300s
Release "lab10-dev" has been upgraded. Happy Helming!
STATUS: deployed
REVISION: 3
```

```bash
$ helm get values lab10-dev
USER-SUPPLIED VALUES:
replicaCount: 5
service:
  type: LoadBalancer
resources:
  requests:
    cpu: 200m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

```bash
$ kubectl get deployment lab10-dev-app-python
NAME                   READY   UP-TO-DATE   AVAILABLE   AGE
lab10-dev-app-python   5/5     5            5           ...
```

## Task 4 - Chart Hooks (3 pts)

### 1. Implemented hooks

Hook templates:
- `k8s/app-python/templates/hooks/pre-install-job.yaml`
- `k8s/app-python/templates/hooks/post-install-job.yaml`

Annotations used:
- `helm.sh/hook: pre-install` and `post-install`
- `helm.sh/hook-weight: -5` for pre-install, `5` for post-install
- `helm.sh/hook-delete-policy: hook-succeeded`

### 2. Hook rendering evidence

```bash
$ helm get hooks lab10-dev
# Source: app-python/templates/hooks/post-install-job.yaml
annotations:
  "helm.sh/hook": post-install
  "helm.sh/hook-weight": "5"
  "helm.sh/hook-delete-policy": hook-succeeded

# Source: app-python/templates/hooks/pre-install-job.yaml
annotations:
  "helm.sh/hook": pre-install
  "helm.sh/hook-weight": "-5"
  "helm.sh/hook-delete-policy": hook-succeeded
```

### 3. Hook execution evidence

Temporary hook-check release with extended sleep was used to capture `kubectl describe job` before deletion:

```bash
$ kubectl get jobs
NAME                                    STATUS    COMPLETIONS   DURATION   AGE
lab10-jobcheck-app-python-pre-install   Running   0/1           18s        18s
```

```bash
$ kubectl describe job lab10-jobcheck-app-python-pre-install
Name:             lab10-jobcheck-app-python-pre-install
Annotations:      helm.sh/hook: pre-install
                  helm.sh/hook-delete-policy: hook-succeeded
                  helm.sh/hook-weight: -5
Pods Statuses:    1 Active / 0 Succeeded / 0 Failed
Events:
  SuccessfulCreate  Created pod: lab10-jobcheck-app-python-pre-install-...
```

Execution completion events for both hooks:

```bash
$ kubectl get events --sort-by=.metadata.creationTimestamp | grep -E 'lab10-jobcheck-app-python-(pre-install|post-install)'
... Completed  job/lab10-jobcheck-app-python-pre-install
... Completed  job/lab10-jobcheck-app-python-post-install
```

Deletion policy evidence:

```bash
$ kubectl get jobs | grep lab10-jobcheck || echo 'no lab10-jobcheck jobs found'
No resources found in default namespace.
no lab10-jobcheck jobs found
```

## Task 5 - Documentation (2 pts)

### 1. Chart overview

Implemented chart architecture:
- `k8s/app-python`: primary app chart from Lab 9 manifests
- `k8s/app-python-v2`: second app chart for bonus
- `k8s/common-lib`: library chart with shared helpers

Main chart structure:

```text
k8s/app-python/
  Chart.yaml
  Chart.lock
  values.yaml
  values-dev.yaml
  values-prod.yaml
  charts/common-lib-0.1.0.tgz
  templates/
    deployment.yaml
    service.yaml
    ingress.yaml
    hooks/pre-install-job.yaml
    hooks/post-install-job.yaml
    NOTES.txt
```

### 2. Configuration guide

Primary configuration points:
- `replicaCount`
- `image.repository`, `image.tag`, `image.pullPolicy`
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`
- `resources.requests/limits`
- `livenessProbe`, `readinessProbe`
- `hooks.enabled`, `hooks.image`, hook commands

Examples:

```bash
# Development
helm install lab10-dev app-python -f app-python/values-dev.yaml --set service.nodePort=30081

# Production profile
helm upgrade lab10-dev app-python -f app-python/values-prod.yaml

# One-off override
helm upgrade lab10-dev app-python -f app-python/values-prod.yaml --set replicaCount=6
```

### 3. Hook implementation

- Pre-install job validates before resource install
- Post-install job runs smoke validation after install
- Weights enforce order (`-5` then `5`)
- `hook-succeeded` keeps namespace clean

### 4. Installation evidence

```bash
$ helm list
NAME        NAMESPACE   REVISION   STATUS    CHART               APP VERSION
lab10-app2  default     1          deployed  app-python-v2-0.1.0 1.0.0
lab10-dev   default     4          deployed  app-python-0.1.0    1.0.0
```

```bash
$ kubectl get all -l app.kubernetes.io/instance=lab10-dev
pod/lab10-dev-app-python-...    1/1 Running
service/lab10-dev-app-python    NodePort 80:30081/TCP
deployment.apps/lab10-dev-app-python 1/1
```

```bash
$ kubectl get all -l app.kubernetes.io/instance=lab10-app2
pod/lab10-app2-app-python-v2-... 1/1 Running
service/lab10-app2-app-python-v2 ClusterIP 80/TCP
deployment.apps/lab10-app2-app-python-v2 2/2
```

### 5. Operations

Install:

```bash
helm install lab10-dev app-python -f app-python/values-dev.yaml --set service.nodePort=30081
```

Upgrade:

```bash
helm upgrade lab10-dev app-python -f app-python/values-prod.yaml
```

Rollback evidence:

```bash
$ helm history lab10-dev
REVISION  STATUS      DESCRIPTION
1         superseded  Install complete
2         failed      Upgrade failed (...ImagePullBackOff...)
3         superseded  Upgrade complete
4         deployed    Rollback to 1

$ helm rollback lab10-dev 1 --wait --timeout 240s
Rollback was a success! Happy Helming!
```

Uninstall evidence (temporary hook-check release):

```bash
$ helm uninstall lab10-jobcheck
release "lab10-jobcheck" uninstalled
```

### 6. Testing and validation

```bash
$ helm lint common-lib
1 chart(s) linted, 0 chart(s) failed

$ helm lint app-python
1 chart(s) linted, 0 chart(s) failed

$ helm lint app-python-v2
1 chart(s) linted, 0 chart(s) failed
```

```bash
$ helm template app-python app-python > /tmp/lab10-app-python-template.yaml
$ helm install --dry-run=client --debug test-release app-python
STATUS: pending-install
DESCRIPTION: Dry run complete
```

Application accessibility verification:

```bash
$ MINIKUBE_IP=$(minikube ip)
$ curl -s "http://${MINIKUBE_IP}:30081/health"
{"status":"healthy",...}

$ curl -s "http://${MINIKUBE_IP}:30081/" | head -c 220
{"service":{"name":"devops-info-service","version":"1.0.0",...}
```

## Bonus Task - Library Charts (2.5 pts)

### 1. Second application chart

Implemented second app chart:
- `k8s/app-python-v2`

Converted from:
- `k8s/bonus-app2-deployment.yml`
- `k8s/bonus-app2-service.yml`

### 2. Library chart

Created shared library chart:
- `k8s/common-lib`
- `type: library`

Shared templates in `k8s/common-lib/templates/_helpers.tpl`:
- `common.name`
- `common.fullname`
- `common.chart`
- `common.selectorLabels`
- `common.labels`

### 3. Dependency wiring

Both app charts depend on library chart:

```yaml
dependencies:
  - name: common-lib
    version: 0.1.0
    repository: "file://../common-lib"
```

Dependency verification:

```bash
$ helm dependency list app-python
NAME        VERSION REPOSITORY            STATUS
common-lib  0.1.0   file://../common-lib ok

$ helm dependency list app-python-v2
NAME        VERSION REPOSITORY            STATUS
common-lib  0.1.0   file://../common-lib ok
```

### 4. Dual deployment evidence

```bash
$ helm install lab10-app2 app-python-v2 --wait --timeout 240s
NAME: lab10-app2
STATUS: deployed
```

```bash
$ helm list
NAME        NAMESPACE  STATUS    CHART
lab10-dev   default    deployed  app-python-0.1.0
lab10-app2  default    deployed  app-python-v2-0.1.0
```

Benefits achieved:
- DRY labels and naming logic across charts
- Consistent metadata conventions
- Easier maintenance for future charts

## Checklist

### Task 1 - Helm Fundamentals (2 pts)
- [x] Helm installed and verified
- [x] Chart repositories explored
- [x] Helm concepts understood
- [x] Documentation of setup

### Task 2 - Create Your Helm Chart (3 pts)
- [x] Chart created in `k8s/` directory
- [x] `Chart.yaml` properly configured
- [x] Manifests converted to templates
- [x] Values properly extracted
- [x] Helper templates implemented
- [x] Health checks remain functional (not commented out)
- [x] Chart installs successfully

### Task 3 - Multi-Environment Support (2 pts)
- [x] `values-dev.yaml` created
- [x] `values-prod.yaml` created
- [x] Environment-specific configurations
- [x] Both environments tested
- [x] Documentation of differences

### Task 4 - Chart Hooks (3 pts)
- [x] Pre-install hook implemented
- [x] Post-install hook implemented
- [x] Proper hook annotations
- [x] Hook weights configured
- [x] Deletion policies applied
- [x] Hooks execute successfully
- [x] Hooks deleted per policy

### Task 5 - Documentation (2 pts)
- [x] `k8s/HELM.md` complete
- [x] Chart structure explained
- [x] Configuration guide provided
- [x] Hook implementation documented
- [x] Installation evidence included
- [x] Operations documented

### Bonus - Library Charts (2.5 pts)
- [x] Library chart created
- [x] Shared templates extracted
- [x] Two app charts using the library
- [x] Dependencies configured
- [x] Both apps deploy successfully
- [x] Documentation complete