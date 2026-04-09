# Helm Chart Implementation Summary

This file summarizes the Lab 10 Helm implementation.

Primary detailed report with full terminal logs and checklist:
- `k8s/docs/LAB10.md`

## 1. Chart Overview

Implemented charts:
- `k8s/app-python` (main application chart from Lab 9 manifests)
- `k8s/app-python-v2` (bonus second app chart)
- `k8s/common-lib` (shared template library chart)

Main templates:
- `deployment.yaml`
- `service.yaml`
- `ingress.yaml` (optional for app-python)
- `hooks/pre-install-job.yaml`
- `hooks/post-install-job.yaml`

Values strategy:
- base defaults in `values.yaml`
- environment overlays in `values-dev.yaml` and `values-prod.yaml`

## 2. Configuration Guide

Important values:
- `replicaCount`
- `image.repository`, `image.tag`, `image.pullPolicy`
- `service.type`, `service.port`, `service.targetPort`, `service.nodePort`
- `resources.requests/limits`
- `readinessProbe`, `livenessProbe`
- `hooks.enabled`, `hooks.image`, command strings

Example commands:

```bash
# Install dev profile
helm install lab10-dev ./k8s/app-python -f ./k8s/app-python/values-dev.yaml --set service.nodePort=30081

# Upgrade to prod profile
helm upgrade lab10-dev ./k8s/app-python -f ./k8s/app-python/values-prod.yaml

# Install second application
helm install lab10-app2 ./k8s/app-python-v2 --wait --timeout 240s
```

## 3. Hook Implementation

Implemented hooks in `k8s/app-python/templates/hooks/`:
- `pre-install-job.yaml`
- `post-install-job.yaml`

Hook config:
- pre-install weight: `-5`
- post-install weight: `5`
- delete policy: `hook-succeeded`

Execution and cleanup were validated in-cluster:
- `kubectl describe job lab10-jobcheck-app-python-pre-install`
- `kubectl get events ... | grep lab10-jobcheck-app-python-(pre-install|post-install)`
- `kubectl get jobs` returned no hook jobs after completion

## 4. Installation Evidence

Live evidence highlights:

```bash
$ helm list
NAME        NAMESPACE STATUS   CHART
lab10-dev   default   deployed app-python-0.1.0
lab10-app2  default   deployed app-python-v2-0.1.0
```

```bash
$ kubectl get all -l app.kubernetes.io/instance=lab10-dev
pod/lab10-dev-app-python-...   Running
service/lab10-dev-app-python   NodePort 80:30081/TCP
deployment.apps/lab10-dev-app-python 1/1
```

```bash
$ kubectl get all -l app.kubernetes.io/instance=lab10-app2
pod/lab10-app2-app-python-v2-... Running
service/lab10-app2-app-python-v2 ClusterIP 80/TCP
deployment.apps/lab10-app2-app-python-v2 2/2
```

## 5. Operations

Install:

```bash
helm install lab10-dev ./k8s/app-python -f ./k8s/app-python/values-dev.yaml --set service.nodePort=30081
```

Upgrade:

```bash
helm upgrade lab10-dev ./k8s/app-python -f ./k8s/app-python/values-prod.yaml
```

Rollback:

```bash
helm rollback lab10-dev 1 --wait --timeout 240s
```

Uninstall:

```bash
helm uninstall lab10-jobcheck
```

## 6. Testing and Validation

Validation commands used:

```bash
helm lint ./k8s/common-lib
helm lint ./k8s/app-python
helm lint ./k8s/app-python-v2

helm template app-python ./k8s/app-python
helm install --dry-run=client --debug test-release ./k8s/app-python
```

Runtime check:

```bash
MINIKUBE_IP=$(minikube ip)
curl -s "http://${MINIKUBE_IP}:30081/health"
```
