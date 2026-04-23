# Lab 13 Report — GitOps with ArgoCD

## Task 1 — ArgoCD Installation & Setup

ArgoCD was installed using Helm in the `argocd` namespace. The `argocd` CLI was installed locally in `~/.local/bin/`.

**Installation Verification:**
```bash
# kubectl get pods -n argocd
# Output showing all argocd components running
```

**UI Access:**  
Accessed via port-forwarding: `kubectl port-forward svc/argocd-server -n argocd 8080:443`.

**CLI Login:**  
`argocd login localhost:8080 --username admin --password <password> --insecure`

## Task 2 — Application Deployment

The application was deployed using the `k8s/argocd/application.yaml` manifest.

**Sync Status:** Synced.
**Health Status:** Healthy.

## Task 3 — Multi-Environment Deployment

Created separate applications for `dev` and `prod` environments.

- **Dev:** `application-dev.yaml`, target namespace `dev`, uses `values-dev.yaml`, automated sync with self-heal enabled.
- **Prod:** `application-prod.yaml`, target namespace `prod`, uses `values-prod.yaml`, manual sync.

**Dev Status:** Synced, Healthy.
**Prod Status:** Synced, Healthy (Note: LoadBalancer status stays Progressing in minikube as External-IP remains pending).

## Task 4 — Self-Healing & Documentation

**Self-Healing Test (Dev):**
1. Scaled dev deployment to 5 replicas: `kubectl scale deployment python-app-dev-app-python -n dev --replicas=5`.
2. Observed ArgoCD detecting drift and automatically scaling back to 1 replica (as defined in `values-dev.yaml`).

**Pod Deletion Test:**
1. Deleted a pod in dev.
2. Kubernetes (ReplicaSet controller) recreated it immediately. ArgoCD stayed Synced.

**Key Differences:**
- **Kubernetes Healing:** Ensures desired state (replicas) at the object level.
- **ArgoCD Healing:** Ensures cluster state matches Git state (configuration drift).

## Bonus Task — ApplicationSet

Created `k8s/argocd/applicationset.yaml` using the List generator to manage both environments.

**ApplicationSet Manifest:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: python-app-set
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - env: dev
            namespace: dev
            valuesFile: values-dev.yaml
          - env: prod
            namespace: prod
            valuesFile: values-prod.yaml
  template:
    metadata:
      name: 'python-app-{{env}}'
    spec:
      project: default
      source:
        repoURL: https://github.com/Timofeq1/DevOps-Core-Course.git
        targetRevision: lab13
        path: k8s/app-python
        helm:
          valueFiles:
            - '{{valuesFile}}'
      destination:
        server: https://kubernetes.default.svc
        namespace: '{{namespace}}'
      syncPolicy:
        automated:
          prune: true
          selfHeal: true
        syncOptions:
          - CreateNamespace=true
```

## Checklist Compliance

- [x] Task 1: ArgoCD installed, CLI ready.
- [x] Task 2: Initial app deployed and synced.
- [x] Task 3: Dev/Prod environments set up with different policies.
- [x] Task 4: Self-healing tested and documented.
- [x] Bonus: ApplicationSet implemented.
