# Task 6 — Documentation & Comparison (3 pts)

### Deployment Summary

| Item | Value |
|------|-------|
| Worker URL | `https://edge-api.t-ivlev.workers.dev` |
| Version ID | `d7eac747-73c1-451f-93ca-aae30e7dd71d` |
| Routes | `/`, `/health`, `/edge`, `/counter`, `/settings` |
| Vars | `APP_NAME`, `COURSE_NAME` |
| Secrets | `API_TOKEN`, `ADMIN_EMAIL` |
| KV Namespace | `SETTINGS` (`08e385de3e704c76b5a9b07ae285fe45`) |
| Runtime | TypeScript, Workers platform |

### Evidence

**Edge JSON response (from public URL):**
```json
{
    "colo": "AMS",
    "country": "NL",
    "city": "Amsterdam",
    "asn": 24875,
    "httpProtocol": "HTTP/2",
    "tlsVersion": "TLSv1.3",
    "timezone": "Europe/Amsterdam",
    "latitude": "52.37403",
    "longitude": "4.88969",
    "timestamp": "2026-05-14T10:26:08.918Z"
}
```

**Local dev server logs:**
```log
request { path: '/', method: 'GET', colo: 'AMS', country: 'NL' }
request { path: '/health', method: 'GET', colo: 'AMS', country: 'NL' }
request { path: '/edge', method: 'GET', colo: 'AMS', country: 'NL' }
request { path: '/counter', method: 'GET', colo: 'AMS', country: 'NL' }
```

#TODO: Add screenshot of Cloudflare dashboard (Workers & Pages > edge-api) showing the Worker overview with request metrics. This requires manual browser access to dash.cloudflare.com.

### Kubernetes vs Cloudflare Workers Comparison

| Aspect | Kubernetes | Cloudflare Workers |
|--------|------------|--------------------|
| Setup complexity | High -- need cluster, nodes, networking, RBAC, ingress controller | Low -- `npm create cloudflare`, `wrangler deploy` |
| Deployment speed | Minutes (image build, pull, pod scheduling) | Seconds (code upload to global edge) |
| Global distribution | Manual -- deploy to each region, set up geo-routing | Automatic -- every deploy hits all 330+ data centers |
| Cost (for small apps) | Medium-high -- cluster nodes cost money even when idle | Free tier: 100k requests/day, paid scales to zero |
| State/persistence model | PVCs, StatefulSets, external databases | KV (eventually consistent), D1 (SQLite), R2 (object storage), Durable Objects |
| Control/flexibility | Full -- any container, any port, any protocol, custom scheduling | Constrained -- V8 isolates, HTTP/WebSocket only, limited CPU time per request |
| Best use case | Long-running services, complex microservices, stateful workloads, custom networking | Lightweight APIs, edge middleware, A/B testing, static site backends, simple stateful apps |

### When to Use Each

**Scenarios favoring Kubernetes:**
- Complex microservice architectures with inter-service communication
- Long-running background workers or stream processing
- Applications needing custom protocols (gRPC, raw TCP)
- Teams that need full control over the runtime and networking
- Multi-cloud or hybrid deployments

**Scenarios favoring Workers:**
- Globally distributed HTTP APIs with low latency requirements
- Edge computing -- modifying requests/responses close to users
- Serverless functions triggered by HTTP or Cron
- Projects that want zero-ops deployment with automatic scaling
- Prototypes, MVPs, and small-to-medium production services

**My recommendation:** For this DevOps course's web app (Python/Go HTTP services), Kubernetes is the more natural fit because of Docker compatibility and broader ecosystem. But Workers shines for lightweight APIs, edge logic, and scenarios where you do not want to think about infrastructure at all. If I were building a simple API for a mobile app or a website backend, I would reach for Workers first.

### Reflection

**What felt easier than Kubernetes?**
Deployment speed is incredible -- `wrangler deploy` takes seconds versus minutes of docker build, push, and kubectl apply. No struggle with YAML, no pod debugging, no ingress configuration. The `workers.dev` URL is a killer feature for prototyping.

**What felt more constrained?**
No Docker images means you cannot just take your existing containerized app and deploy it. The Workers runtime is a specific JavaScript/TypeScript environment -- if your app is written in Go or Python, you are out of luck (Python Workers exist but are experimental). No filesystem, no long-running connections, and CPU time is capped per request.

**What changed because Workers is not a Docker host?**
I had to rewrite the app logic from scratch instead of reusing the existing Python/Go apps from earlier labs. The mental model shifts from "deploy this container" to "write a function that handles HTTP requests." Bindings replace environment variables and connection strings. State management moves from databases to KV and Durable Objects. It is a different paradigm entirely.