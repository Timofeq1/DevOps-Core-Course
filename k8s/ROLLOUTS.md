# Argo Rollouts — Progressive Delivery Implementation

This document summarizes the Lab 14 Argo Rollouts implementation for progressive delivery.

Primary detailed report with full terminal logs and checklist:
- `k8s/docs/LAB14.md`

---

## 1. Argo Rollouts Setup

### Installation Verification

**Controller:**
```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml
```

Verified controller running:
```
NAMESPACE       NAME                                     READY   STATUS    RESTARTS   AGE
argo-rollouts   argo-rollouts-5f64f8d68-vzv9v            1/1     Running   0          81s
argo-rollouts   argo-rollouts-dashboard-755bbc64c-zsfnw  1/1     Running   0          12s
```

**CRDs installed:**
```
analysisruns.argoproj.io
analysistemplates.argoproj.io
clusteranalysistemplates.argoproj.io
experiments.argoproj.io
rollouts.argoproj.io
```

**kubectl plugin:**
```bash
kubectl-argo-rollouts version
# kubectl-argo-rollouts: v1.9.0+838d4e7
```

### Dashboard Access

```bash
# Deploy dashboard
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/dashboard-install.yaml

# Access dashboard (port-forward)
kubectl port-forward svc/argo-rollouts-dashboard -n argo-rollouts 3100:3100
# Open http://localhost:3100
```

### Rollout vs Deployment — Key Differences

| Feature | Deployment | Rollout |
|---------|-----------|---------|
| **Strategy field** | `type: RollingUpdate` or `Recreate` | `strategy.canary` or `strategy.blueGreen` |
| **Traffic shifting** | Not supported | Percentage-based weight steps |
| **Manual promotion** | N/A | `kubectl argo rollouts promote` |
| **Preview service** | N/A | Blue-green preview service |
| **Automated analysis** | N/A | AnalysisTemplate with metrics |
| **Rollback** | Manual via `kubectl rollout undo` | Instant via `kubectl argo rollouts abort` |
| **API Group** | `apps/v1` | `argoproj.io/v1alpha1` |

Additional Rollout fields:
- `spec.strategy.canary.steps[]` — progressive traffic shifting steps
- `spec.strategy.blueGreen.activeService` / `previewService` — dual-service for instant switch
- `spec.strategy.blueGreen.autoPromotionEnabled` — automatic promotion
- Integration with AnalysisTemplate for metrics-based decisions

---

## 2. Canary Deployment

### Strategy Configuration

File: `k8s/app-python/templates/rollout.yaml`

The canary strategy uses progressive traffic shifting with a mix of manual and automatic pauses:

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20        # 20% traffic to new version
      - pause: {}            # MANUAL promotion required
      - setWeight: 40        # 40% traffic
      - pause: { duration: 30s }  # Auto-advance after 30s
      - setWeight: 60        # 60% traffic
      - pause: { duration: 30s }
      - setWeight: 80        # 80% traffic
      - pause: { duration: 30s }
      - setWeight: 100       # Full rollout
```

### Step-by-Step Rollout Progression

1. **Initial State**: All 3 replicas running stable version (weight: 0% canary)
2. **Step 1 (setWeight: 20)**: 20% traffic to new version, 80% to stable. Requires MANUAL promotion.
3. **Step 2 (setWeight: 40)**: After manual promotion, auto-advances to 40% after 30s pause.
4. **Step 3 (setWeight: 60)**: Auto-advances after 30s.
5. **Step 4 (setWeight: 80)**: Auto-advances after 30s.
6. **Step 5 (setWeight: 100)**: Full traffic to new version. Rollout complete.

### CLI Commands

```bash
# Watch rollout progress
kubectl argo rollouts get rollout <name> -w

# Manual promotion to next step
kubectl argo rollouts promote <name>

# Abort rollout (instant rollback)
kubectl argo rollouts abort <name>

# Retry aborted rollout
kubectl argo rollouts retry rollout <name>

# Set image to trigger new rollout
kubectl argo rollouts set image <name> "container=new-image:tag"
```

### Promotion and Abort Demonstration

```bash
# Trigger canary update
kubectl argo rollouts set image lab14-canary-app-python "app-python=timofeq1/devops-lab03-python:v2.0"

# Watch the canary steps
kubectl argo rollouts get rollout lab14-canary-app-python -w
# Output shows: Step 1/9 (setWeight: 20) → waiting for promotion

# Manual promote past first step
kubectl argo rollouts promote lab14-canary-app-python
# Rollout advances to 40%, then auto-advances every 30s

# Abort during rollout (instant rollback)
kubectl argo rollouts abort lab14-canary-app-python
# All traffic instantly shifts back to stable version
```

---

## 3. Blue-Green Deployment

### Strategy Configuration

File: `k8s/app-python/templates/rollout.yaml` (blueGreen section)
File: `k8s/app-python/templates/preview-service.yaml`
File: `k8s/app-python/values-bluegreen.yaml`

```yaml
strategy:
  blueGreen:
    activeService: lab14-bg-app-python         # Production traffic
    previewService: lab14-bg-app-python-preview  # Test new version
    autoPromotionEnabled: false                # Manual promotion
```

### Preview vs Active Service

- **Active Service** (`lab14-bg-app-python`): Serves production traffic to stable (blue) version
- **Preview Service** (`lab14-bg-app-python-preview`): Serves traffic to new (green) version for testing

Both services use the same selector labels; Argo Rollouts manages which pods receive which traffic.

### Testing Blue-Green Flow

```bash
# Deploy blue-green
helm install lab14-bg ./app-python -f ./app-python/values-bluegreen.yaml --set service.nodePort=30088 --set previewService.nodePort=30089

# Access active (production — BLUE)
kubectl port-forward svc/lab14-bg-app-python 8080:80

# Access preview (new version — GREEN)
kubectl port-forward svc/lab14-bg-app-python-preview 8081:80

# Trigger green deployment
kubectl argo rollouts set image lab14-bg-app-python "app-python=timofeq1/devops-lab03-python:v2.0"

# Test preview at localhost:8081
curl http://localhost:8081/health

# Promote green to active
kubectl argo rollouts promote lab14-bg-app-python
# Instant switch — all production traffic now goes to green
```

### Instant Rollback

```bash
# Rollback after promotion (instant)
kubectl argo rollouts undo lab14-bg-app-python
# Traffic instantly switches back to previous stable version
```

---

## 4. Strategy Comparison

### When to Use Canary vs Blue-Green

| Scenario | Recommended Strategy |
|----------|---------------------|
| Zero-downtime critical | **Either** — both support zero-downtime |
| Need gradual exposure | **Canary** — percentage-based traffic shifting |
| Need instant switch | **Blue-Green** — atomic cutover |
| Limited resources | **Canary** — shares resources between versions |
| Pre-release testing | **Blue-Green** — full isolated preview environment |
| Automated metrics-based promotion | **Canary** — native analysis integration |
| Simple rollback | **Blue-Green** — instant switch back |

### Pros and Cons

**Canary:**
- ✅ Gradual risk reduction — small % exposed first
- ✅ Shared resources (no double cost)
- ✅ Supports automated analysis at each step
- ❌ Slower full rollout
- ❌ Mixed-traffic debugging harder
- ❌ Requires more complex traffic routing setup

**Blue-Green:**
- ✅ Instant switch / instant rollback
- ✅ Full isolated testing of new version
- ✅ Simple mental model
- ❌ 2x resource requirement during deployment
- ❌ All-or-nothing risk model
- ❌ Stateful apps need careful data migration

### Recommendation

- **Production APIs with high traffic**: Canary with metrics analysis — gradual exposure minimizes blast radius
- **Critical quick-fix patches**: Blue-Green — instant rollback provides safety net
- **Dev/staging environments**: Canary with short pauses — fast feedback loop
- **Database-dependent services**: Blue-Green — easier to test schema changes against full copy

---

## 5. CLI Commands Reference

| Command | Description |
|---------|-------------|
| `kubectl argo rollouts get rollout <name>` | Show rollout status and tree |
| `kubectl argo rollouts get rollout <name> -w` | Watch rollout progress |
| `kubectl argo rollouts promote <name>` | Promote to next canary step / promote blue-green |
| `kubectl argo rollouts abort <name>` | Abort rollout (instant rollback) |
| `kubectl argo rollouts retry rollout <name>` | Retry aborted rollout |
| `kubectl argo rollouts undo <name>` | Rollback to previous stable version |
| `kubectl argo rollouts set image <name> <container>=<image>` | Update container image |
| `kubectl argo rollouts dashboard` | Launch dashboard UI |
| `kubectl argo rollouts version` | Show plugin version |
| `kubectl argo rollouts lint <file>` | Validate Rollout manifest |
| `kubectl argo rollouts terminate <name>` | Terminate analysis run |

### Monitoring and Troubleshooting

```bash
# View rollout history
kubectl argo rollouts history <name>

# View rollout details
kubectl argo rollouts describe <name>

# Check analysis runs
kubectl get analysisruns -l rollout=<name>

# Dashboard visualization
kubectl argo rollouts dashboard
# Open browser at the displayed URL
```

---

## 6. Automated Analysis (Bonus)

### AnalysisTemplate Configuration

File: `k8s/app-python/templates/analysistemplate.yaml`

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: lab14-canary-app-python-success-rate
spec:
  metrics:
    - name: webcheck
      provider:
        web:
          url: http://lab14-canary-app-python.default.svc.cluster.local/health
          jsonPath: "{$.status}"
      successCondition: result == 'ok'
      interval: 10s
      count: 3
      failureLimit: 1
```

### How Metrics Determine Success/Failure

1. During canary step with analysis, Argo Rollouts queries the web URL every 10 seconds
2. Extracts `status` field from JSON response using jsonPath
3. Checks if `result == 'ok'` (success condition)
4. Runs 3 times; if more than 1 failure → rollout is aborted
5. If all 3 checks pass → rollout proceeds to next step

### Canary with Analysis

```yaml
strategy:
  canary:
    steps:
      - setWeight: 20
      - analysis:
          templates:
            - templateName: success-rate
      - setWeight: 50
      - pause: { duration: 30s }
      - setWeight: 100
```

### Demonstration of Auto-Rollback

When the health endpoint returns an error status (e.g., `{"status":"error"}`), the analysis detects failure and automatically aborts the rollout, shifting all traffic back to the stable version.
