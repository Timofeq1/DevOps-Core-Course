# Lab 02 - Docker Containerization

## Docker Best Practices Applied

1.  **Non-root User**
    *   **Why:** Running applications as root inside a container represents a significant security risk. If an attacker compromises the application, they gain root access to the container and potentially the host (via container escape vulnerabilities).
    *   **Implementation:**
        ```dockerfile
        RUN useradd -m -u 1000 appuser
        USER appuser
        ```

2.  **Specific Base Image**
    *   **Why:** Using `python:3.13-slim` instead of `latest` or full version reduces the image size significantly and ensures reproducibility. We know exactly which OS and Python version we are running.
    *   **Implementation:** `FROM python:3.13-slim`

3.  **Layer Caching**
    *   **Why:** By copying `requirements.txt` and installing dependencies *before* copying the application code, we ensure that the expensive `pip install` step is cached. It only re-runs if dependencies change, not when we change source code.
    *   **Implementation:**
        ```dockerfile
        COPY requirements.txt .
        RUN pip install --no-cache-dir -r requirements.txt
        COPY . .
        ```

4.  **No Cache Installation**
    *   **Why:** `pip` caches downloaded packages by default. In a Docker image, we install them once and never use the cache again. Disabling it reduces image size.
    *   **Implementation:** `pip install --no-cache-dir ...`

5.  **.dockerignore**
    *   **Why:** Prevents unnecessary files (like `venv`, `.git`, `__pycache__`) from being sent to the Docker daemon. This speeds up the build process and prevents secrets or large local files from bloating the image.

## Image Information & Decisions

*   **Base Image:** `python:3.13-slim`
    *   **Justification:** The `slim` variant contains the minimal packages needed to run Python. It is much smaller than the standard image (approx. 100MB vs 900MB) but easier to work with than `alpine` (which uses musl-libc and can cause compatibility issues with some Python wheels).
*   **Final Image Size:** ~150 MB
    *   **Assessment:** This is a reasonable size for a Python web application, containing the OS runtime, Python interpreter, and dependencies.

## Build & Run Process

### Build Command
```bash
docker build -t timofey/devops-lab02-python:latest .
```

### Run Command
```bash
docker run -d -p 5000:5000 --name python-app timofey/devops-lab02-python:latest
```

### Verification
```bash
curl http://localhost:5000/
# Output: {"service": {"name": "devops-info-service", ...}}
```

### Docker Hub
**Repository:** [https://hub.docker.com/repository/docker/timofey/devops-lab02-python](https://hub.docker.com/)

*(Note: Replace `timofey` with your actual Docker Hub username)*

## Technical Analysis

*   **Layer Order:** If we moved `COPY . .` before `RUN pip install`, every change to code would invalidate the cache for the pip install layer, causing a full re-install of dependencies on every build.
*   **Security:** Using a non-root user limits the blast radius of potential exploits. Only necessary files are copied, reducing the attack surface.
*   **Context:** The `.dockerignore` ensures that the build context sent to the daemon is small (KB, not MBs/GBs if venv was included).

## Challenges & Solutions

*   **Challenge:** Ensuring the application listens on the correct interface inside the container.
*   **Solution:** In Lab 1, I configured the app to listen on `0.0.0.0` via environment variable or default. This is crucial for Docker, as `127.0.0.1` would only be accessible inside the container.
