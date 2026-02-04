# Lab 02 - Go Multi-Stage Build (Bonus)

## Multi-Stage Build Strategy

**Concept:** 
We use two stages in our `Dockerfile`:
1.  **Builder Stage:** Based on `golang:1.21-alpine`. Contains all the tools needed to compile Go code (compiler, linker, standard library). This image is relatively large.
2.  **Runtime Stage:** Based on `scratch` (an empty image). It contains **only** the compiled binary.

**Why it matters:**
Compiled languages like Go produce self-contained binaries. Once the binary is built, we don't need the Go compiler or the source code anymore. By discarding the builder stage and keeping only the binary, we drastically reduce the image size and the attack surface.

## Size Comparison

| Image Type | Size (Approx) | Description |
|------------|---------------|-------------|
| golang:1.21 | ~800 MB | Full development environment |
| golang:1.21-alpine | ~300 MB | Minimal development environment |
| **Final Image (scratch)** | **~7 MB** | **Just the binary** |

**Reduction:** The final image is ~98% smaller than the builder image.

## Technical Explanation of Stages

### Stage 1: Builder
```dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
RUN adduser -D -g '' appuser
COPY go.mod ./
COPY main.go ./
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o app main.go
```
*   `adduser`: Creates a system user so we don't have to run as root.
*   `ldflags="-w -s"`: Strips debug info for smaller size.

### Stage 2: Runtime
```dockerfile
FROM scratch
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /app/app /app/app
USER appuser
ENTRYPOINT ["/app/app"]
```
*   `FROM scratch`: Starts with a completely empty filesystem.
*   `COPY --from=builder`: Extracts *only* the artifact we built in the previous stage.

## Security Benefits

1.  **Minimal Attack Surface:** The final container has no shell (`/bin/sh` or `/bin/bash`), no package manager (`apk`, `apt`), and no other system utilities (like `curl`, `wget`).
2.  **Immutability:** An attacker who manages to exploit the application cannot install new tools or easily navigate the filesystem because there is practically no filesystem to navigate.
3.  **Vulnerability Scanning:** With fewer files (literally just one binary), there are fewer things that can have CVEs.

## Build Process

```bash
docker build -t timofeq1/devops-lab02-go:latest .
```

## Run Process

```bash
docker run -d -p 8080:8080 --name go-app timofeq1/devops-lab02-go:latest
```
