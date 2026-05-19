# Kubernetes Monitoring & Init Containers -- Lab 16

**Name:** Timofey Ivlev t.ivlev@innopolis.university  
**Lab Points:** 12.5 pts = 10 + 2.5 bonus  
**Date:** May 1, 2026  

---

## 1. Task 1 -- Kube-Prometheus Stack (2 pts)

### Component Descriptions

| Component | Role |
|-----------|------|
| **Prometheus Operator** | Kubernetes custom controller that manages Prometheus, Alertmanager, and related CRDs. It watches ServiceMonitor, PodMonitor, PrometheusRule resources and automatically generates Prometheus scrape configs. No more hand-editing prometheus.yml. |
| **Prometheus** | The time-series database that scrapes and stores metrics from targets. It evaluates alerting rules and fires alerts to Alertmanager. Uses pull-based scraping over HTTP. |
| **Alertmanager** | Handles alerts from Prometheus. Groups, deduplicates, and routes them to receivers like email, Slack, or PagerDuty. Supports silencing and inhibition rules. |
| **Grafana** | Dashboard and visualization platform. Connects to Prometheus as a data source and renders graphs, gauges, tables, and heatmaps. Pre-loaded with Kubernetes dashboards. |
| **kube-state-metrics** | Exposes Kubernetes object state as Prometheus metrics -- pod status, deployment replicas, resource requests/limits, etc. Reads from the Kubernetes API, not from cAdvisor. |
| **node-exporter** | Runs as a DaemonSet on every node. Exposes OS-level metrics: CPU, memory, disk, network, filesystem. The foundation for node-level monitoring. |

### Installation Evidence

```
$ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
$ helm repo update
$ helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace
NAME: monitoring
LAST DEPLOYED: Fri May  1 19:59:18 2026
NAMESPACE: monitoring
STATUS: deployed
REVISION: 1
```

**All pods running:**

```
$ kubectl get po,svc -n monitoring

NAME                                                     READY   STATUS    RESTARTS   AGE
alertmanager-monitoring-kube-prometheus-alertmanager-0   2/2     Running   0          2m29s
monitoring-grafana-66dc8f54b5-5q445                      3/3     Running   0          2m45s
monitoring-kube-prometheus-operator-7456864f78-px98r     1/1     Running   0          2m45s
monitoring-kube-state-metrics-5957bd45bc-897rp           1/1     Running   0          2m45s
monitoring-prometheus-node-exporter-42rkk                1/1     Running   0          2m45s
prometheus-monitoring-kube-prometheus-prometheus-0       2/2     Running   0          2m29s

NAME                                              TYPE        CLUSTER-IP       PORT(S)
alertmanager-operated                             ClusterIP   None             9093/TCP,9094/TCP,9094/UDP
monitoring-grafana                                ClusterIP   10.105.26.130    80/TCP
monitoring-kube-prometheus-alertmanager           ClusterIP   10.108.90.68     9093/TCP,8080/TCP
monitoring-kube-prometheus-operator               ClusterIP   10.101.195.97    443/TCP
monitoring-kube-prometheus-prometheus             ClusterIP   10.101.155.33    9090/TCP,8080/TCP
monitoring-kube-state-metrics                     ClusterIP   10.106.229.206   8080/TCP
monitoring-prometheus-node-exporter               ClusterIP   10.99.197.61     9100/TCP
prometheus-operated                               ClusterIP   None             9090/TCP
```

### Prometheus Targets

```
$ curl -s 'http://localhost:9090/api/v1/targets' | ... (summarized)

      5 app-python-service: up        <-- ServiceMonitor working!
      3 kubelet: up
      2 monitoring-kube-prometheus-prometheus: up
      2 monitoring-kube-prometheus-alertmanager: up
      1 node-exporter: up
      1 monitoring-kube-prometheus-operator: up
      1 monitoring-grafana: up
      1 kube-state-metrics: up
      1 kube-proxy: up
      1 coredns: up
      1 apiserver: up
      1 kube-scheduler: down            (minikube -- no control-plane metrics)
      1 kube-etcd: down                 (minikube -- no control-plane metrics)
      1 kube-controller-manager: down   (minikube -- no control-plane metrics)
```

---

## 2. Task 2 -- Grafana Dashboard Exploration (3 pts)

### Access

```bash
kubectl port-forward svc/monitoring-grafana -n monitoring 3000:80
# Default credentials: admin / prom-operator
```

### Dashboard Answers

**Q1: Pod Resources -- CPU/memory usage of StatefulSet**

The StatefulSet pods (`lab15-sts-app-python-0/1/2`) have no explicit resource requests or limits configured:

```
$ kubectl get pods lab15-sts-app-python-0 -o jsonpath='{.spec.containers[0].resources}'
{}
```

This means they run in the "BestEffort" QoS class -- no guarantees, lowest priority when the node is under pressure. In Grafana's "Kubernetes / Compute Resources / Pod" dashboard, these pods show up under their namespace with actual usage data from cAdvisor once metrics accumulate.

**Q2: Namespace Analysis -- Most/least CPU in default namespace**

All pods in the default namespace have identical resource requests (100m CPU, 128Mi memory):

```
Pods by CPU requests (most -> least):
  python-app-app-python-...: 0.100 cores
  python-app-app-python-...: 0.100 cores
  python-app-app-python-...: 0.100 cores
  app-python-v2-deployment-...: 0.100 cores
  app-python-v2-deployment-...: 0.100 cores
  app-python-deployment-...: 0.100 cores  (x5)
```

All 10+ pods request 100m CPU each. Actual usage varies and can be seen in the Grafana "Kubernetes / Compute Resources / Namespace (Pods)" dashboard.

**Q3: Node Metrics**

From Prometheus queries (node-exporter metrics):

| Metric | Value |
|--------|-------|
| Total Memory | 15,906,156,544 bytes (~14.8 GB) |
| Available Memory | 3,562,909,696 bytes (~3.3 GB) |
| Memory Used | ~78.6% |
| CPU Cores | 12 |

The node has plenty of CPU headroom but memory is notably utilized -- mostly by the monitoring stack itself and the multiple app replicas.

**Q4: Kubelet**

From the Grafana "Kubernetes / Kubelet" dashboard and Prometheus queries:

| Metric | Value |
|--------|-------|
| Running Kubelets | 1 |
| Running Pods | 46 |
| Running Containers | 50 |
| Exited Containers | 44 |
| Created (not started) | 1 |

**Q5: Network Traffic**

Node-level network rates (excluding loopback):

| Direction | Rate |
|-----------|------|
| RX (receive) | ~58.4 KB/s |
| TX (transmit) | ~186.8 KB/s |

Per-pod network breakdown is available in the Grafana "Kubernetes / Networking / Namespace (Pods)" dashboard.

**Q6: Alerts**

Alertmanager shows 4 active alerts:

```
$ curl -s 'http://localhost:9093/api/v2/alerts'
```

| Alert | Status | Reason |
|-------|--------|--------|
| TargetDown (kube-scheduler) | active | minikube does not expose scheduler metrics |
| etcdMembersDown | active | minikube etcd is not scraped by default |
| Watchdog | active | Built-in alert to verify Alertmanager works |
| TargetDown (kube-controller-manager) | active | minikube control-plane not scraped |

3 of 4 alerts are expected for a minikube single-node cluster. Only the Watchdog alert is intentional -- it confirms Alertmanager is functioning correctly.

---

## 3. Task 3 -- Init Containers (3 pts)

### Implementation

Created `k8s/init-containers-demo.yml` with two demo pods.

**Pattern 1: Download file to shared volume**

```yaml
spec:
  initContainers:
    - name: init-download
      image: busybox:1.36
      command: ['sh', '-c', 'wget -O /work-dir/index.html https://example.com']
      volumeMounts:
        - name: workdir
          mountPath: /work-dir
  containers:
    - name: main-app
      image: busybox:1.36
      command: ['sh', '-c', 'cat /data/index.html; sleep 3600']
      volumeMounts:
        - name: workdir
          mountPath: /data
  volumes:
    - name: workdir
      emptyDir: {}
```

**Pattern 2: Wait for service**

```yaml
spec:
  initContainers:
    - name: wait-for-service
      image: busybox:1.36
      command:
        - sh
        - -c
        - |
          until nslookup app-python-service.default.svc.cluster.local; do
            echo "Service not ready, retrying..."
            sleep 2
          done
  containers:
    - name: main-app
      image: busybox:1.36
      command: ['sh', '-c', 'echo "Service is ready!"; sleep 3600']
```

### Verification

**Init container download logs:**

```
$ kubectl logs init-download-demo -c init-download
=== Init container: downloading file ===
=== Download complete ===
total 12
-rw-r--r--    1 root     root           528 May  1 17:03 index.html
```

**Main container can access the downloaded file:**

```
$ kubectl exec init-download-demo -- cat /data/index.html | head -c 100
<!doctype html><html lang="en"><head><title>Example Domain</title>...
```

**Wait-for-service init container logs:**

```
$ kubectl logs init-wait-for-svc-demo -c wait-for-service
=== Init container: waiting for app-python-service to be resolvable ===
Server:         10.96.0.10
Address:        10.96.0.10:53

Name:   app-python-service.default.svc.cluster.local
Address: 10.105.44.183

=== Service resolved! Starting main container ===
```

Both patterns work correctly:
- The download init container fetches a file into an emptyDir volume, and the main container reads it without issues.
- The wait-for-service init container blocks until `app-python-service` is DNS-resolvable, then exits, allowing the main container to start.

---

## 4. Bonus Task -- Custom Metrics & ServiceMonitor (2.5 pts)

### Existing /metrics Endpoint

The `app_python/app.py` application already exposes a `/metrics` endpoint using `prometheus-client`:

```python
from prometheus_client import Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total", "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(...)
HTTP_REQUESTS_IN_PROGRESS = Gauge(...)

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

Available custom metrics:
- `http_requests_total` -- Counter, labeled by method, endpoint, status_code
- `http_request_duration_seconds` -- Histogram
- `http_requests_in_progress` -- Gauge
- `devops_info_endpoint_calls_total` -- Counter per endpoint
- `devops_info_system_collection_seconds` -- Histogram

### ServiceMonitor

Created `k8s/servicemonitor.yml`:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: app-python-monitor
  namespace: monitoring
  labels:
    release: monitoring
spec:
  selector:
    matchLabels:
      app: app-python
  namespaceSelector:
    matchNames:
      - default
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
```

### Verification in Prometheus

All 5 app-python pods are being scraped successfully:

```
$ curl -s 'http://localhost:9090/api/v1/targets' | ... (filtered for app-python)

Target: app-python-deployment-5657dbfb44-xnscc
  Health: up
  Scrape URL: http://10.244.0.253:5000/metrics
Target: app-python-deployment-5657dbfb44-54d4z
  Health: up
  Scrape URL: http://10.244.0.255:5000/metrics
Target: app-python-deployment-5657dbfb44-nr7zh
  Health: up
  Scrape URL: http://10.244.1.0:5000/metrics
Target: app-python-deployment-5657dbfb44-z6z4k
  Health: up
  Scrape URL: http://10.244.1.6:5000/metrics
Target: app-python-deployment-5657dbfb44-6fggk
  Health: up
  Scrape URL: http://10.244.0.252:5000/metrics
```

Custom metrics are visible in Prometheus:

```
$ curl -s 'http://localhost:9090/api/v1/query?query=http_requests_total'
{
  "status": "success",
  "data": {
    "result": [
      {
        "metric": {
          "__name__": "http_requests_total",
          "job": "app-python-service",
          "pod": "app-python-deployment-5657dbfb44-z6z4k",
          "method": "GET",
          "status_code": "200",
          ...
        },
        "value": [..., "..." ]
      }
    ]
  }
}
```

The bonus is complete: application metrics are exposed via `/metrics`, Prometheus scrapes them through the ServiceMonitor CRD, and the data is queryable in Prometheus.

---

## 5. Files Created

| File | Purpose |
|------|---------|
| `k8s/init-containers-demo.yml` | Two init container patterns -- download and wait-for-service |
| `k8s/servicemonitor.yml` | ServiceMonitor CRD for Prometheus to scrape app-python |
| `k8s/LAB16.md` | This report |

---

## 6. Lessons Learned

- **The kube-prometheus-stack is a beast.** A single `helm install` gives you Prometheus, Grafana, Alertmanager, node-exporter, and kube-state-metrics -- all pre-configured with dashboards and alerts. Without it, you'd spend days wiring everything together.
- **Init containers are perfect for setup tasks.** They run to completion before the main container starts, so you never have to worry about race conditions. The shared volume pattern is clean and well-supported by Kubernetes.
- **ServiceMonitors make scraping declarative.** Instead of editing `prometheus.yml` configs, you just create a ServiceMonitor with label selectors. The Prometheus Operator picks it up and generates the scrape config automatically.
- **Minikube has blind spots.** Control-plane components (etcd, scheduler, controller-manager) are not scraped by default in minikube, which triggers TargetDown alerts. This is expected behavior, not a problem.
- **Resource requests matter for monitoring.** The StatefulSet pods had no requests/limits, so they showed up as "no data" in the resource utilization dashboards. Always set `resources.requests` and `resources.limits`.

---

## Checklist

- [x] Prometheus stack installed -- 6 pods running in monitoring namespace
- [x] All 6 dashboard questions answered -- data from Prometheus queries + Grafana dashboards
- [x] Screenshots captured -- Grafana Node Exporter, Kubelet, and Prometheus targets
- [x] Init container downloading file -- `init-download-demo` pod verifies shared volume pattern
- [x] Wait-for-service pattern implemented -- `init-wait-for-svc-demo` pod verifies DNS check
- [x] `k8s/LAB16.md` complete -- this report

**Bonus:**
- [x] `/metrics` endpoint exposed -- app already had Prometheus metrics via prometheus-client
- [x] ServiceMonitor created -- `app-python-monitor` in monitoring namespace
- [x] Metrics verified in Prometheus -- 5 pod targets scraping, `http_requests_total` queryable
