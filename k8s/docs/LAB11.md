# Lab 11 - Kubernetes Secrets and HashiCorp Vault

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Date:** 2026-04-09  
**Lab Points:** 12.5 pts = 10 + 2.5 bonus

## Task 1 - Kubernetes Secrets Fundamentals (2 pts)

### 1. Secret creation with kubectl

```bash
$ kubectl create secret generic app-credentials \
    --from-literal=username=lab11-admin \
    --from-literal=password='Lab11-Pass-123'
secret/app-credentials created
```

### 2. Secret inspection and decoding

```bash
$ kubectl get secret app-credentials -o yaml
apiVersion: v1
data:
  password: TGFiMTEtUGFzcy0xMjM=
  username: bGFiMTEtYWRtaW4=
kind: Secret
metadata:
  name: app-credentials
  namespace: default
type: Opaque
```

```bash
$ echo 'bGFiMTEtYWRtaW4=' | base64 -d
lab11-admin

$ echo 'TGFiMTEtUGFzcy0xMjM=' | base64 -d
Lab11-Pass-123
```

### 3. Security implications

- Base64 is encoding, not encryption.
- Anyone who can read Secret objects from the Kubernetes API can decode values.
- Kubernetes Secrets are not encrypted at rest by default on every cluster setup.
- Production recommendation:
  - Enable etcd encryption at rest for Secret resources.
  - Restrict Secret access with RBAC (least privilege).
  - Use external secret managers (Vault) for stronger controls, rotation, and audit trails.

About etcd encryption:
- etcd encryption at rest encrypts Secret payloads before they are persisted in etcd.
- It should be enabled when the cluster stores any sensitive credentials, tokens, or keys.
- Typical implementation is `EncryptionConfiguration` on API server with providers (for example `aescbc` or KMS).

## Task 2 - Helm-Managed Secrets (3 pts)

### 1. Implemented chart changes

Added files:
- `k8s/app-python/templates/secrets.yaml`
- `k8s/app-python/templates/serviceaccount.yaml`
- `k8s/app-python/templates/_helpers.tpl`

Updated files:
- `k8s/app-python/templates/deployment.yaml`
- `k8s/app-python/values.yaml`
- `k8s/app-python/values-dev.yaml`
- `k8s/app-python/values-prod.yaml`

Highlights:
- Secret rendered from `.Values.secret.*` with `stringData`.
- Deployment consumes the secret with `envFrom.secretRef`.
- Resource requests/limits remain configurable via values files.
- Added named helper template (`app-python.envVars`) and included it in deployment (`env`).

### 2. Helm validation

```bash
$ helm dependency update app-python
Saving 1 charts
Deleting outdated charts

$ helm lint app-python
1 chart(s) linted, 0 chart(s) failed
```

Rendered secret/deployment evidence:

```bash
$ helm template lab11-preview app-python -f app-python/values-dev.yaml ...
# Source: app-python/templates/secrets.yaml
kind: Secret
metadata:
  name: lab11-preview-app-python-secret

# Source: app-python/templates/deployment.yaml
...
envFrom:
  - secretRef:
      name: lab11-preview-app-python-secret
```

### 3. Deployment and runtime verification

```bash
$ helm upgrade --install lab11-secrets app-python -f app-python/values-dev.yaml \
    --set service.nodePort=30082 \
    --set secret.data.username=helm-user \
    --set secret.data.password='Helm-Pass-321' \
    --set vault.enabled=true \
    --set vault.role=lab11-app \
    --set vault.secretPath=secret/data/myapp/config \
    --set vault.injectFileName=config
STATUS: deployed
```

```bash
$ kubectl get secret lab11-secrets-app-python-secret -o yaml
apiVersion: v1
data:
  password: SGVsbS1QYXNzLTMyMQ==
  username: aGVsbS11c2Vy
kind: Secret
metadata:
  annotations:
    meta.helm.sh/release-name: lab11-secrets
```

Environment variables in pod (showing secret injection works):

```bash
$ kubectl exec <pod> -c app-python -- printenv | grep -E '^(username|password|APP_ENV|LOG_LEVEL|HOST|PORT)='
APP_ENV=dev
HOST=0.0.0.0
LOG_LEVEL=debug
password=Helm-Pass-321
PORT=5000
username=helm-user
```

`kubectl describe pod` does not reveal secret values directly:

```bash
$ kubectl describe pod <pod> | grep -E 'Environment Variables from|Secret' -n
81:    Environment Variables from:
82:      lab11-secrets-app-python-secret  Secret  Optional: false
```

### 4. Resource management

Configured values (dev profile):
- requests: `cpu: 50m`, `memory: 64Mi`
- limits: `cpu: 100m`, `memory: 128Mi`

Live deployment proof:

```bash
$ kubectl get deployment lab11-secrets-app-python -o jsonpath='{.spec.template.spec.containers[0].resources}'
{"limits":{"cpu":"100m","memory":"128Mi"},"requests":{"cpu":"50m","memory":"64Mi"}}
```

Requests vs limits:
- Requests are guaranteed minimum resources for scheduling.
- Limits are hard caps to prevent runaway usage.
- Start from observed usage and keep headroom for spikes.

## Task 3 - HashiCorp Vault Integration (3 pts)

### 1. Vault install and pod verification

Repository and install command used:

```bash
$ helm repo add hashicorp https://helm.releases.hashicorp.com
$ helm repo update
$ helm upgrade --install vault hashicorp/vault \
    --set server.dev.enabled=true \
    --set injector.enabled=true
```

Pod verification:

```bash
$ kubectl get pods -l app.kubernetes.io/name=vault
NAME                                    READY   STATUS    RESTARTS   AGE
vault-agent-injector-848dd747d7-r4lzc   1/1     Running   0          ...
vault-0                                  1/1     Running   0          ...
```

Note:
- A Helm upgrade conflict happened on webhook `caBundle` ownership during re-apply.
- Vault server and injector pods stayed healthy and functional for this lab run.

### 2. Vault configuration (KV, policy, role)

Configured inside `vault-0`:

```bash
$ vault kv put secret/myapp/config username="vault-user" password="vault-password-123" api_key="vault-api-key-xyz"

$ vault auth enable kubernetes
Success! Enabled kubernetes auth method at: kubernetes/

$ vault write auth/kubernetes/config \
    kubernetes_host="https://${KUBERNETES_PORT_443_TCP_ADDR}:443" \
    token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
    kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
Success! Data written to: auth/kubernetes/config
```

Policy and role:

```hcl
path "secret/data/myapp/config" {
  capabilities = ["read"]
}
```

```bash
$ vault policy write lab11-app /tmp/lab11-policy.hcl
Success! Uploaded policy: lab11-app

$ vault write auth/kubernetes/role/lab11-app \
    bound_service_account_names="lab11-secrets-app-python" \
    bound_service_account_namespaces="default" \
    policies="lab11-app" ttl="1h"
```

Verification:

```bash
$ vault auth list
kubernetes/    kubernetes    ...

$ vault read auth/kubernetes/role/lab11-app
bound_service_account_names      [lab11-secrets-app-python]
bound_service_account_namespaces [default]
policies                         [lab11-app]
```

### 3. Vault Agent injection verification

Deployment pod with sidecar injection:

```bash
$ kubectl get pods -l app.kubernetes.io/instance=lab11-secrets
NAME                                        READY   STATUS    RESTARTS   AGE
lab11-secrets-app-python-6fd6f76d77-2vqck   2/2     Running   0          ...
```

Injected files path and content:

```bash
$ kubectl exec <pod> -c app-python -- ls -la /vault/secrets
total 12
-rw-r--r-- 1 100 appuser 55 ... config
-rw-r--r-- 1 100 appuser  7 ... reload.flag

$ kubectl exec <pod> -c app-python -- cat /vault/secrets/config
APP_USERNAME=vault-user
APP_PASSWORD=vault-password-123
```

Sidecar injection pattern summary:
- Vault Agent injector mutating webhook adds init/sidecar containers.
- Pod authenticates to Vault via Kubernetes service account token.
- Agent renders secret templates to in-pod files (`/vault/secrets/*`).
- App reads secrets from mounted files without embedding credentials in images.

## Task 4 - Documentation and Security Analysis (2 pts)

### K8s Secrets vs Vault

Kubernetes Secret:
- Native and simple.
- Good for basic scenarios.
- Requires strict RBAC and etcd encryption to be safer.
- Limited built-in rotation/audit workflows.

Vault:
- Centralized secrets backend with auth methods and policies.
- Better auditing, lease/TTL model, and rotation workflows.
- Supports dynamic secret generation and templated injection.
- Operationally heavier, but preferred for production-grade secret management.

### When to use each

Use Kubernetes Secrets when:
- Project is simple/internal and risk is low.
- You can enforce RBAC and etcd encryption.

Use Vault when:
- Multiple services/teams consume secrets.
- You need rotation, stronger policy boundaries, and auditability.
- You want to avoid static credentials in cluster objects.

### Production recommendations

- Enable etcd encryption at rest.
- Enforce least-privilege RBAC for `secrets` verbs.
- Use dedicated service accounts per workload.
- Prefer external managers (Vault/ESO/cloud SM) for sensitive systems.
- Rotate secrets periodically and monitor secret access events.

## Bonus Task - Vault Agent Templates (2.5 pts)

### 1. Template annotation implementation

Implemented in deployment template via values-driven key names:
- `vault.hashicorp.com/agent-inject-secret-config`
- `vault.hashicorp.com/agent-inject-template-config`
- `vault.hashicorp.com/agent-inject-command-config`

Template value from `values.yaml`:

```yaml
vault:
  injectTemplate: |
    {{- with secret "secret/data/myapp/config" -}}
    APP_USERNAME={{ .Data.data.username }}
    APP_PASSWORD={{ .Data.data.password }}
    {{- end -}}
```

### 2. Dynamic refresh research and command annotation

Observed behavior:

```bash
$ vault kv put secret/myapp/config username="vault-user-rotated" password="vault-password-rotated" ...
version: 2

$ kubectl exec <pod> -c app-python -- cat /vault/secrets/config
APP_USERNAME=vault-user
```

- Update to KV v2 version was successful, but immediate in-pod file still showed previous value.
- This is expected for many static secret template scenarios where refresh is not instantaneous.
- `vault.hashicorp.com/agent-inject-command-*` executes after template render and can trigger app reload logic.
- Verified command annotation output file:

```bash
$ kubectl exec <pod> -c app-python -- cat /vault/secrets/reload.flag
reload
```

### 3. Named template for env vars (DRY)

Added named template in `k8s/app-python/templates/_helpers.tpl`:

```yaml
{{- define "app-python.envVars" -}}
- name: APP_ENV
  value: {{ .Values.appConfig.environment | quote }}
- name: LOG_LEVEL
  value: {{ .Values.appConfig.logLevel | quote }}
{{- end -}}
```

Used in deployment:

```yaml
env:
  {{- include "app-python.envVars" . | nindent 12 }}
```

Benefit:
- Shared env var block is defined once and reused cleanly, reducing duplication and drift.

## Checklist

### Task 1 - Kubernetes Secrets Fundamentals (2 pts)
- [x] Secret created via kubectl
- [x] Secret viewed and decoded
- [x] Security implications understood and documented

### Task 2 - Helm-Managed Secrets (3 pts)
- [x] `templates/secrets.yaml` created
- [x] Secrets defined in `values.yaml`
- [x] Deployment updated to consume secrets
- [x] Environment variables verified in pod
- [x] Resource limits configured

### Task 3 - HashiCorp Vault Integration (3 pts)
- [x] Vault installed via Helm
- [x] KV secrets engine configured
- [x] Kubernetes auth method enabled
- [x] Policy and role created
- [x] Vault Agent injection working
- [x] Secrets accessible in pod

### Task 4 - Documentation (2 pts)
- [x] LAB11.md complete
- [x] All sections documented with evidence
- [x] Security analysis included

### Bonus - Vault Agent Templates (2.5 pts)
- [x] Template annotation implemented
- [x] Custom format rendering working
- [x] Named template in `_helpers.tpl`
- [x] Documentation complete
- [x] Dynamic refresh behavior researched and documented
