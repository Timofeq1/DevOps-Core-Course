# Lab 13 Report — GitOps with ArgoCD

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Date:** 2026-04-23   
**Lab Points:** 12.5 pts = 10 + 2.5 bonus

## Task 1 — ArgoCD Installation & Setup

ArgoCD was installed using Helm in the `argocd` namespace. The `argocd` CLI was installed locally in `~/.local/bin/`.

**Installation Verification:**
```bash
kubectl get pods -n argocd
NAME                                                READY   STATUS    RESTARTS   AGE
argocd-application-controller-0                     1/1     Running   0          12m
argocd-applicationset-controller-559566846f-xxsgt   1/1     Running   0          12m
argocd-dex-server-8f5687997-zk77x                   1/1     Running   0          12m
argocd-notifications-controller-56c7d65875-4m2br    1/1     Running   0          12m
argocd-redis-fcd76bcfb-lj67t                        1/1     Running   0          12m
argocd-repo-server-7b8447858f-bgskv                 1/1     Running   0          12m
argocd-server-7f857f54f-47knj                       1/1     Running   0          12m
```

**UI Access:**  
Accessed via port-forwarding: `kubectl port-forward svc/argocd-server -n argocd 8080:443`.

**CLI Login:**  
`argocd login localhost:8080 --username admin --password WHdiM3RnLAkSlDg2 --insecure`

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
2. Observed ArgoCD detecting drift and automatically scaling back to 1 replica (as defined in `values-dev.yaml`) within seconds.
3. Observed that when a manual annotation was added (`kubectl annotate pod -l app.kubernetes.io/name=app-python test=drift`), ArgoCD detected the drift and (since `selfHeal` was enabled) eventually reverted it to match Git's state.

**Pod Deletion Test:**
1. Deleted a pod in dev.
2. Kubernetes (ReplicaSet controller) recreated it immediately. ArgoCD stayed Synced.

**Key Differences:**
- **Kubernetes Healing:** Ensures desired state (replicas) at the object level (ReplicaSet controller).
- **ArgoCD Healing:** Ensures cluster state matches Git state (configuration drift detection).

**Documentation:**
Detailed documentation created in [k8s/ARGOCD.md](../ARGOCD.md).

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

**Benefits of ApplicationSet:**
1. **Consistency**: All generated applications share the same base configuration template.
2. **Efficiency**: Deploying multiple environments only requires updating a single `ApplicationSet` resource rather than creating multiple `Application` manifests.
3. **Scalability**: Adding a new environment (e.g., `staging`) is as simple as adding an entry to the `list` generator.

## Checklist Compliance

### Task 1 — ArgoCD Installation & Setup (2 pts)
- [x] ArgoCD installed via Helm
- [x] All pods running in argocd namespace
- [x] UI accessible via port-forward
- [x] Admin password retrieved
- [x] CLI installed and logged in

### Task 2 — Application Deployment (3 pts)
- [x] `k8s/argocd/` directory created
- [x] Application manifest created
- [x] Application visible in ArgoCD UI
- [x] Initial sync completed
- [x] App accessible and working
- [x] GitOps workflow tested

### Task 3 — Multi-Environment Deployment (3 pts)
- [x] Dev and prod namespaces created
- [x] Dev application with auto-sync
- [x] Prod application with manual sync
- [x] Different configurations per environment
- [x] Both apps deployed and verified

### Task 4 — Self-Healing & Documentation (2 pts)
- [x] Manual scale test performed
- [x] Self-healing observed
- [x] Pod deletion test performed
- [x] Configuration drift test done
- [x] `k8s/ARGOCD.md` complete

### Bonus — ApplicationSet (2.5 pts)
- [x] ApplicationSet manifest created
- [x] Multiple apps generated from template
- [x] Generator configuration documented
- [x] Benefits documented
