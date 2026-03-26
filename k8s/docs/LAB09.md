# Lab 09 - Kubernetes Fundamentals

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Date:** 2026-03-25  
**Lab Points:** 14.5 pts = 12 + 2.5 bonus 

## Task 1 — Local Kubernetes Setup (2 pts)

#### 1. Kubectl and local cluster minikube installed: 
```bash
timofey@lenovoARH7:~$ minikube start
😄  minikube v1.38.1 on Linuxmint 22.1
✨  Automatically selected the docker driver. Other choices: none, ssh
❗  Starting v1.39.0, minikube will default to "containerd" container runtime. See #21973 for more info.
📌  Using Docker driver with root privileges
👍  Starting "minikube" primary control-plane node in "minikube" cluster
🚜  Pulling base image v0.0.50 ...
💾  Downloading Kubernetes v1.35.1 preload ...
    > preloaded-images-k8s-v18-v1...:  272.45 MiB / 272.45 MiB  100.00% 3.82 Mi
    > gcr.io/k8s-minikube/kicbase...:  519.58 MiB / 519.58 MiB  100.00% 3.01 Mi
🔥  Creating docker container (CPUs=2, Memory=3700MB) ...
🐳  Preparing Kubernetes v1.35.1 on Docker 29.2.1 ...
🔗  Configuring bridge CNI (Container Networking Interface) ...
🔎  Verifying Kubernetes components...
    ▪ Using image gcr.io/k8s-minikube/storage-provisioner:v5
🌟  Enabled addons: storage-provisioner, default-storageclass

❗  /usr/bin/kubectl is version 1.33.10, which may have incompatibilities with Kubernetes 1.35.1.
    ▪ Want kubectl v1.35.1? Try 'minikube kubectl -- get pods -A'
🏄  Done! kubectl is now configured to use "minikube" cluster and "default" namespace by default
```
#### 2. Cluster running successfully
```bash
timofey@lenovoARH7:~$ minikube status
minikube
type: Control Plane
host: Running
kubelet: Running
apiserver: Running
kubeconfig: Configured


timofey@lenovoARH7:~$ kubectl get nodes
NAME       STATUS   ROLES           AGE     VERSION
minikube   Ready    control-plane   7m36s   v1.35.1

```
#### 3. Terminal output showing cluster info
```bash
timofey@lenovoARH7:~$ kubectl cluster-info
Kubernetes control plane is running at https://192.168.49.2:8443
CoreDNS is running at https://192.168.49.2:8443/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
```
#### 4. Documentation of setup process

I followed the official Minikube installation guide for Linux, which can be found at https://kubernetes.io/ru/docs/tasks/tools/install-minikube/. I installed Minikube using the direct link and then started the cluster using `minikube start`. After the cluster was up and running, I verified its status with `minikube status` and checked the cluster information with `kubectl cluster-info`. The setup process was straightforward, and I encountered no issues.
I decided to use Minikube because it has full Kubernetes entities support including Ingress, which is essential for getting bonus points in this lab. Additionally, Minikube is widely used for local Kubernetes development and testing, making it a suitable choice for this lab.

## Task 2 - Application Deployment (3 pts)

### Implemented manifest

File: `k8s/deployment.yml`

Key implementation details:
- Deployment name: `app-python-deployment`
- Replicas: `3`
- Image: `timofeq1/devops-lab03-python:latest`
- Container port: `5000`
- Rolling update strategy:
    - `maxSurge: 1`
    - `maxUnavailable: 0`
- Readiness probe: `GET /health` on port `5000`
- Liveness probe: `GET /health` on port `5000`
- Resource requests/limits:
    - Requests: `100m CPU`, `128Mi memory`
    - Limits: `300m CPU`, `256Mi memory`
- Labels and selectors aligned via `app: app-python`

Rationale:
- `/health` endpoint exists in FastAPI app, so probes are meaningful.
- Requests/limits are conservative for local clusters and demonstrate production baseline.
- Rolling update config ensures high availability during updates.

### Validation

Manifests were validated with client-side kubectl dry run:

```bash
kubectl apply --dry-run=client -f k8s/deployment.yml
```

Output:

```text
deployment.apps/app-python-deployment created (dry run)
```

### Deployment evidence

Applied and verified live on cluster:

```bash
kubectl apply -f k8s/deployment.yml
kubectl rollout status deployment/app-python-deployment
kubectl get deployments app-python-deployment
kubectl get pods -l app=app-python -o wide
```

Output:

```text
deployment.apps/app-python-deployment unchanged
deployment "app-python-deployment" successfully rolled out
NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
app-python-deployment   3/3     3            3           13h
NAME                                     READY   STATUS    RESTARTS      AGE   IP            NODE       NOMINATED NODE   READINESS GATES
app-python-deployment-5657dbfb44-pr8r4   1/1     Running   1 (12h ago)   13h   10.244.0.25   minikube   <none>           <none>
app-python-deployment-5657dbfb44-qfffc   1/1     Running   1 (12h ago)   13h   10.244.0.29   minikube   <none>           <none>
app-python-deployment-5657dbfb44-vk2sf   1/1     Running   1 (12h ago)   13h   10.244.0.24   minikube   <none>           <none>
```

## Task 3 - Service Configuration (2 pts)

### Implemented manifest

File: `k8s/service.yml`

Key implementation details:
- Service name: `app-python-service`
- Type: `NodePort`
- Selector: `app: app-python`
- Service port: `80`
- Target port: `5000`
- Fixed NodePort: `30080`

Rationale:
- `NodePort` is required by task for local external access.
- Port `80 -> 5000` provides a standard external HTTP entrypoint.

### Validation

```bash
kubectl apply --dry-run=client -f k8s/service.yml
```

Output:

```text
service/app-python-service created (dry run)
```

### Service evidence

Applied and verified live on cluster:

```bash
kubectl apply -f k8s/service.yml
kubectl get services app-python-service
curl http://$(minikube ip):30080/health
curl http://$(minikube ip):30080/
```

Output (abridged):

```text
service/app-python-service unchanged
NAME                 TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
app-python-service   NodePort   10.105.44.183   <none>        80:30080/TCP   13h
{"status":"healthy","timestamp":"2026-03-26T10:30:27.614176+00:00","uptime_seconds":155}{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"app-python-deployment-5657dbfb44-vk2sf","platform":"Linux","platform_version":"#101-Ubuntu SMP PREEMPT_DYNAMIC Mon Feb  9 10:15:05 UTC 2026","architecture":"x86_64","cpu_count":12,"python_version":"3.13.11"},"runtime":{"uptime_seconds":155,"uptime_human":"0 hours, 2 minutes","current_time":"2026-03-26T10:30:27.756204+00:00","timezone":"UTC"},"request":{"client_ip":"10.244.0.1","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"},{"path":"/metrics","method":"GET","description":"Prometheus metrics"}]}
```

## Task 4 - Scaling and Updates (2 pts)

### Scaling demonstration commands

Declarative scale to 5 replicas:

```bash
kubectl apply -f k8s/deployment.yml
deployment.apps/app-python-deployment configured
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 of 5 updated replicas are available...
Waiting for deployment "app-python-deployment" rollout to finish: 4 of 5 updated replicas are available...
deployment "app-python-deployment" successfully rolled out
NAME                                     READY   STATUS    RESTARTS      AGE
app-python-deployment-5657dbfb44-8hrd5   1/1     Running   0             8s
app-python-deployment-5657dbfb44-l6sv9   1/1     Running   0             8s
app-python-deployment-5657dbfb44-pr8r4   1/1     Running   1 (12h ago)   13h
app-python-deployment-5657dbfb44-qfffc   1/1     Running   1 (12h ago)   13h
app-python-deployment-5657dbfb44-vk2sf   1/1     Running   1 (12h ago)   13h
```

### Rolling update demonstration commands

Updated image tag in `k8s/deployment.yml` - from latest to 2026.02.19, then applied.

```bash
kubectl apply -f k8s/deployment.yml
deployment.apps/app-python-deployment configured
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
deployment "app-python-deployment" successfully rolled out
deployment.apps/app-python-deployment 
REVISION  CHANGE-CAUSE
2         <none>
3         <none>
4         <none>
```

### Rollback demonstration commands

```bash
kubectl rollout undo deployment/app-python-deployment
deployment.apps/app-python-deployment rolled back
Waiting for deployment "app-python-deployment" rollout to finish: 0 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
deployment "app-python-deployment" successfully rolled out
deployment.apps/app-python-deployment 
REVISION  CHANGE-CAUSE
2         <none>
4         <none>
5         <none>
```

### Performed operations and evidence

Scaling to 5 replicas:

```bash
kubectl scale deployment/app-python-deployment --replicas=5
deployment.apps/app-python-deployment scaled
deployment "app-python-deployment" successfully rolled out
NAME                    READY   UP-TO-DATE   AVAILABLE   AGE
app-python-deployment   5/5     5            5           13h
```

Rolling update and rollback:

```bash
kubectl set env deployment/app-python-deployment ROLLOUT_VERSION=v2
deployment.apps/app-python-deployment env updated
Waiting for deployment "app-python-deployment" rollout to finish: 0 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
deployment "app-python-deployment" successfully rolled out
deployment.apps/app-python-deployment 
REVISION  CHANGE-CAUSE
4         <none>
5         <none>
6         <none>

deployment.apps/app-python-deployment rolled back
Waiting for deployment "app-python-deployment" rollout to finish: 0 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 2 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 3 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 4 out of 5 new replicas have been updated...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
Waiting for deployment "app-python-deployment" rollout to finish: 1 old replicas are pending termination...
deployment "app-python-deployment" successfully rolled out
deployment.apps/app-python-deployment 
REVISION  CHANGE-CAUSE
4         <none>
6         <none>
7         <none>
```

Zero-downtime note:
- During both rollout and rollback, the deployment remained available with `maxUnavailable: 0`, and requests to `/health` stayed successful.

## Task 5 - Documentation (3 pts)

### Architecture overview

Current architecture:
- Deployment `app-python-deployment` with 3+ replicas (scaled to 5 during Task 4).
- Service `app-python-service` (NodePort) exposing application traffic.
- Health endpoint `/health` used by probes and manual checks.

Network flow:
- Client -> NodeIP:NodePort (`30080`) -> Service (`app-python-service`) -> Pods (`app-python-deployment`).

Resource strategy:
- Per-pod requests/limits to guarantee schedulability and cap resource usage.

### Manifest files and choices

- `k8s/deployment.yml`
    - Main application deployment with probes, resources, rolling update strategy.
- `k8s/service.yml`
    - NodePort service for local external access.
- `k8s/bonus-app2-deployment.yml`
    - Second application deployment for Ingress bonus routing.
- `k8s/bonus-app2-service.yml`
    - Internal ClusterIP service for second app.
- `k8s/ingress.yml`
    - Host/path based routing and TLS binding.

### Deployment evidence

Executed commands:

```bash
kubectl get all
kubectl get pods,svc -o wide
kubectl describe deployment app-python-deployment
curl http://$(minikube ip):30080/
curl http://$(minikube ip):30080/health
```

Output (abridged):

```text
NAME                                    READY   STATUS
pod/app-python-deployment-...           1/1     Running
pod/app-python-v2-deployment-...        1/1     Running

NAME                            TYPE       CLUSTER-IP      PORT(S)
service/app-python-service      NodePort   10.105.44.183   80:30080/TCP
service/app-python-v2-service   ClusterIP  10.111.201.24   80/TCP

deployment.apps/app-python-deployment      5/5
deployment.apps/app-python-v2-deployment   2/2

RollingUpdateStrategy:  0 max unavailable, 1 max surge
Liveness:  http-get http://:5000/health ...
Readiness: http-get http://:5000/health ...
```

```text
curl http://$(minikube ip):30080/health
{"status":"healthy",...}
```

### Production considerations

Implemented now:
- Liveness and readiness probes (`/health`) for self-healing and traffic gating.
- CPU/memory requests and limits for predictable scheduling and isolation.
- Rolling update strategy with `maxUnavailable: 0` for high availability.

Areas for improvements for real production:
- Pin immutable image tags (not `latest`) and use signed images.
- Add HPA, PDB, and anti-affinity rules.
- Use dedicated namespace, RBAC, and NetworkPolicies.
- Add centralized logs/metrics/traces dashboards and alerts.
- Move environment config to ConfigMap and secrets to Secret manager.

### Challenges and solutions

- Challenge: ensuring path-based Ingress works with app root endpoints.
- Solution: regex paths + rewrite annotation in Ingress (`/$2`) to strip `/app1` and `/app2` prefixes.
- Challenge: confirming manifest correctness before applying to cluster.
- Solution: used `kubectl apply --dry-run=client` for each manifest.

## Bonus Task - Ingress with TLS (2.5 pts)

### Implemented manifests

- `k8s/bonus-app2-deployment.yml` (second app)
- `k8s/bonus-app2-service.yml` (second app service)
- `k8s/ingress.yml` (host + path routing + TLS)

Ingress routing implemented:
- `https://local.example.com/app1` -> `app-python-service`
- `https://local.example.com/app2` -> `app-python-v2-service`

TLS configured in Ingress via secret name: `apps-tls-secret`

### Validation

```bash
kubectl apply --dry-run=client -f k8s/bonus-app2-deployment.yml
kubectl apply --dry-run=client -f k8s/bonus-app2-service.yml
kubectl apply --dry-run=client -f k8s/ingress.yml
```

Output:

```text
deployment.apps/app-python-v2-deployment created (dry run)
service/app-python-v2-service created (dry run)
ingress.networking.k8s.io/apps-ingress created (dry run)
```

### Bonus operations and evidence

Ingress controller and TLS setup were executed live:

```bash
minikube addons enable ingress
kubectl get pods -n ingress-nginx
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout k8s/certs/tls.key -out k8s/certs/tls.crt \
    -subj "/CN=local.example.com/O=local.example.com"
kubectl create secret tls apps-tls-secret --key k8s/certs/tls.key --cert k8s/certs/tls.crt --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f k8s/bonus-app2-deployment.yml
kubectl apply -f k8s/bonus-app2-service.yml
kubectl apply -f k8s/ingress.yml
kubectl rollout status deployment/app-python-v2-deployment
kubectl get all,ingress
```

Output (abridged - excluding certificate generation for security):

```text
kubectl create secret tls apps-tls-secret --key k8s/certs/tls.key --cert k8s/certs/tls.crt --dry-run=client -o yaml
secret/apps-tls-secret configured
deployment.apps/app-python-v2-deployment unchanged
service/app-python-v2-service unchanged
ingress.networking.k8s.io/apps-ingress unchanged
deployment "app-python-v2-deployment" successfully rolled out
NAME                                           READY   STATUS    RESTARTS      AGE
pod/app-python-deployment-5657dbfb44-54d4z     1/1     Running   0             6m19s
pod/app-python-deployment-5657dbfb44-6fggk     1/1     Running   0             6m40s
pod/app-python-deployment-5657dbfb44-nr7zh     1/1     Running   0             6m26s
pod/app-python-deployment-5657dbfb44-xnscc     1/1     Running   0             6m33s
pod/app-python-deployment-5657dbfb44-z6z4k     1/1     Running   0             6m48s
pod/app-python-v2-deployment-7c9f565f4-dxl6v   1/1     Running   1 (13h ago)   13h
pod/app-python-v2-deployment-7c9f565f4-dzhcx   1/1     Running   1 (13h ago)   13h

NAME                            TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)        AGE
service/app-python-service      NodePort    10.105.44.183   <none>        80:30080/TCP   13h
service/app-python-v2-service   ClusterIP   10.111.201.24   <none>        80/TCP         13h
service/kubernetes              ClusterIP   10.96.0.1       <none>        443/TCP        14h

NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/app-python-deployment      5/5     5            5           13h
deployment.apps/app-python-v2-deployment   2/2     2            2           13h

NAME                                                 DESIRED   CURRENT   READY   AGE
replicaset.apps/app-python-deployment-5657dbfb44     5         5         5       13h
replicaset.apps/app-python-deployment-844b9bc9bf     0         0         0       13h
replicaset.apps/app-python-deployment-c99b49b4c      0         0         0       13m
replicaset.apps/app-python-v2-deployment-7c9f565f4   2         2         2       13h

NAME                                     CLASS   HOSTS               ADDRESS        PORTS     AGE
ingress.networking.k8s.io/apps-ingress   nginx   local.example.com   192.168.49.2   80, 443   13h

```

HTTPS routing test (using Host header):

```bash
curl -k https://$(minikube ip)/app1/health -H "Host: local.example.com"
{"status":"healthy","timestamp":"2026-03-26T10:54:45.140340+00:00","uptime_seconds":475}{"status":"healthy","timestamp":"2

```

Ingress benefit over NodePort:
- Ingress provides L7 HTTP routing, path/host rules, and TLS termination on one endpoint. NodePort exposes raw L4 ports and does not provide HTTP routing features.

## Checklist

### Task 1 - Local Kubernetes Setup (2 pts)
- [x] kubectl and local cluster (minikube/kind) installed
- [x] Cluster running successfully
- [x] Terminal output showing cluster info
- [x] Documentation of setup process

### Task 2 - Application Deployment (3 pts)
- [x] `k8s/deployment.yml` exists
- [x] Uses Docker image from Lab 2/3 workflow
- [x] Minimum 3 replicas configured
- [x] Resource requests and limits defined
- [x] Liveness and readiness probes configured
- [x] Deployment manifest validates successfully
- [x] Deployment successfully running

### Task 3 - Service Configuration (2 pts)
- [x] `k8s/service.yml` exists
- [x] Service type: NodePort
- [x] Correct label selectors
- [x] Service manifest validates successfully
- [x] Service accessible from outside cluster
- [x] All endpoints responding

### Task 4 - Scaling and Updates (2 pts)
- [x] Scaling commands documented
- [x] Rolling update commands documented
- [x] Rollback commands documented
- [x] Scaling to 5 replicas demonstrated with output
- [x] Rolling update performed and documented with output
- [x] Rollback capability demonstrated with output
- [x] Zero downtime verification note added

### Task 5 - Documentation (3 pts)
- [x] Report file complete with all sections (using `k8s/docs/LAB09.md` as requested)
- [x] Architecture overview provided
- [x] Manifest choices and rationale documented
- [x] Production considerations discussed
- [x] Challenges and learnings documented
- [x] Terminal output evidence inserted

### Bonus - Ingress with TLS (2.5 pts)
- [x] Second application manifests created
- [x] Ingress manifest with path-based routing created
- [x] TLS configured in Ingress manifest
- [x] Ingress controller enabled and verified
- [x] TLS certificate generated and secret created
- [x] HTTPS routing verified with curl output
- [x] Bonus documentation finalized with terminal output