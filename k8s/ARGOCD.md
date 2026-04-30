# ArgoCD Documentation

## ArgoCD Installation & Setup

ArgoCD was installed using the official Helm chart in the `argocd` namespace.

### Installation Verification
All pods in the `argocd` namespace are running correctly:
```bash
kubectl get pods -n argocd
```

### UI Access
Access the ArgoCD UI via port-forwarding:
```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```
The initial admin password can be retrieved with:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d && echo
```

### CLI Configuration
The `argocd` CLI is installed and logged in using:
```bash
argocd login localhost:8080 --username admin --password <password> --insecure
```

## Application Configuration

### Application Manifests
The application manifests are located in [k8s/argocd/](k8s/argocd/).

- `application.yaml`: Initial single-environment deployment.
- `application-dev.yaml`: Dev environment with auto-sync and self-healing.
- `application-prod.yaml`: Prod environment with manual sync for safety.

### Source and Destination
- **Source**: `https://github.com/Timofeq1/DevOps-Core-Course.git`
- **Path**: `k8s/app-python`
- **Destination**: Local Kubernetes cluster (`https://kubernetes.default.svc`)

## Multi-Environment Deployment

We use separate namespaces and values files for each environment:
- **Dev**: Namespace `dev`, uses `values-dev.yaml`.
- **Prod**: Namespace `prod`, uses `values-prod.yaml`.

### Rationale
- **Dev**: Automated sync ensures that developers see their changes immediately. Self-healing prevents manual drift from persisting.
- **Prod**: Manual sync acts as a safety gate, requiring an explicit action to deploy changes to production after verification.

## Self-Healing Evidence

### Manual Scale Test
1. **Initial State**: 1 replica.
2. **Action**: Manually scale to 5 replicas.
   ```bash
   kubectl scale deployment python-app-dev-app-python -n dev --replicas=5
   ```
3. **Observation**: ArgoCD detected the drift and scaled the deployment back to 1 replica within seconds.
4. **Behavior**: This is ArgoCD's `selfHeal` policy at work, enforcing the Git state over cluster changes.

### Pod Deletion Test
1. **Action**: Delete a running pod in the `dev` namespace.
   ```bash
   kubectl delete pod <pod-name> -n dev
   ```
2. **Observation**: Kubernetes immediately scheduled a new pod.
3. **Behavior**: This is **Kubernetes** self-healing (via the ReplicaSet controller), not ArgoCD. ArgoCD remains "Synced" because the cluster state (1 replica) still matches the Git state.

### Configuration Drift Test
1. **Action**: Add a manual annotation to the pod.
2. **Observation**: ArgoCD marks the application as `OutOfSync`.
3. **Behavior**: If `selfHeal` is enabled, ArgoCD removes the unauthorized annotation to match Git.

## ApplicationSet

The `applicationset.yaml` simplifies management by using a List generator to template both environments from a single resource.

### Benefits
- **DRY (Don't Repeat Yourself)**: Avoids duplicating the Application manifest for every new environment.
- **Consistency**: Ensures all environments follow the same structure and source.
- **Scalability**: Adding a new environment (e.g., `staging`) only requires adding an element to the generator list.
