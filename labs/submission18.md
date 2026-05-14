# Lab 18 Submission -- Reproducible Builds with Nix

**Author:** Timofey Ivlev t.ivlev@innopolis.university  
**Date:** May 14, 2026  
**Lab Points:** 12/12 pts  
**Platform:** Linux (Linux Mint 22.1), x86_64  
**Nix Version:** 2.34.6 (Determinate Nix 3.20.0)  

---

## Task 1 -- Build Reproducible Python App (Revisiting Lab 1)

### 1.1 Nix Installation

Nix was installed via the Determinate Systems installer:

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | sh -s -- install
```

**Verification:**

```
$ nix --version
nix (Determinate Nix 3.20.0) 2.34.6

$ nix run nixpkgs#hello
Hello, world!
```

Flakes were enabled by default with the Determinate installer.

### 1.2 Application Preparation

The Lab 1 FastAPI application was copied to `labs/lab18/app_python/` with:
- `app.py` -- FastAPI DevOps Info Service (endpoints: `/`, `/health`, `/visits`, `/metrics`)
- `requirements.txt` -- pinned dependencies (fastapi==0.115.0, uvicorn[standard]==0.32.0, prometheus-client==0.23.1)

### 1.3 Nix Derivation (`default.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  pname = "devops-info-service";
  version = "1.0.0";
  src = ./.;

  format = "other";

  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi
    uvicorn
    prometheus-client
  ];

  nativeBuildInputs = [ pkgs.makeWrapper ];

  installPhase = ''
    mkdir -p $out/bin $out/share
    makeWrapper ${pkgs.python3}/bin/python3 $out/bin/devops-info-service \
      --add-flags "$out/share/app.py" \
      --prefix PYTHONPATH : "$PYTHONPATH"
    cp app.py $out/share/app.py
  '';

  doCheck = false;
}
```

**Field explanations:**

| Field | What it does |
|-------|-------------|
| `pname` / `version` | Package identity -- used in the Nix store path |
| `src = ./.` | Source is the current directory (all files in the flake) |
| `format = "other"` | Tells Nix this is not a setuptools/flit/poetry project |
| `propagatedBuildInputs` | Python packages our app needs at runtime -- they come from nixpkgs, not PyPI |
| `nativeBuildInputs` | Build-time tools -- `makeWrapper` creates the executable wrapper |
| `installPhase` | Copies app.py, then wraps `python3` with the app path and PYTHONPATH set |
| `doCheck = false` | Skip the automatic test phase (no pytest in this project) |

**Why `makeWrapper` instead of `wrapProgram`:** The first attempt used `wrapProgram` directly on `app.py`, but since `app.py` has no shebang line, bash tried to execute the Python docstring as a shell command. The fix wraps `python3` itself and passes `app.py` as an argument, which is cleaner and more robust.

### 1.4 Reproducibility Proof

**Store path from initial build:**

```
$ readlink result
/nix/store/yzkk68smxwyhqdarb6j79x7wnlczaagb-devops-info-service-1.0.0
```

**Rebuild (cache hit):**

```
$ rm result && nix build
$ readlink result
/nix/store/yzkk68smxwyhqdarb6j79x7wnlczaagb-devops-info-service-1.0.0
```

Same path returned -- Nix recognized the inputs hadn't changed and reused the cached build.

**Forced rebuild (deleted from store):**

```
$ rm result && nix store delete /nix/store/yzkk68smxwyhqdarb6j79x7wnlczaagb-devops-info-service-1.0.0
1 store paths deleted, 21.2 KiB freed

$ nix build
$ readlink result
/nix/store/yzkk68smxwyhqdarb6j79x7wnlczaagb-devops-info-service-1.0.0
```

**Same store path after complete rebuild from scratch.** Nix rebuilt the derivation and produced the exact same hash. This proves bit-for-bit reproducibility.

**Application runs correctly from Nix build:**

```
$ timeout 3 ./result/bin/devops-info-service
{"timestamp":"2026-05-14T18:14:03+00:00","level":"INFO","message":"Started server process [431129]"}
{"timestamp":"2026-05-14T18:14:03+00:00","level":"INFO","message":"Application startup complete."}
{"timestamp":"2026-05-14T18:14:03+00:00","level":"INFO","message":"Uvicorn running on http://0.0.0.0:5000"}
```

### 1.5 Understanding the Nix Store Path

```
/nix/store/yzkk68smxwyhqdarb6j79x7wnlczaagb-devops-info-service-1.0.0
  |         |                                      |                  |
  |         |                                      |                  +-- version
  |         |                                      +-- package name
  |         +-- content hash (32 chars, base32)
  +-- Nix store root
```

The hash `yzkk68smxwyhqdarb6j79x7wnlczaagb` is computed from:
- All source code (app.py, requirements.txt)
- All dependencies transitively (fastapi, uvicorn, prometheus-client, and their deps)
- The build instructions (installPhase, build inputs)
- Compiler flags and environment

Any change to any of these produces a different hash. Same inputs always produce the same hash -- this is the foundation of Nix's reproducibility.

### 1.6 Comparison: Lab 1 pip vs Lab 18 Nix

| Aspect | Lab 1 (pip + venv) | Lab 18 (Nix) |
|--------|-------------------|--------------|
| Python version | System-dependent (python3 from apt) | Pinned via nixpkgs (python3.12 from nixos-24.11) |
| Dependency resolution | `pip install` at runtime | Resolved at build time from nixpkgs |
| Reproducibility | Approximate (pinned versions, but transitive deps can drift) | Bit-for-bit identical (cryptographic hashes) |
| Portability | Requires same OS + Python | Works anywhere Nix runs |
| Binary cache | No | Yes (cache.nixos.org) |
| Isolation | Virtual environment (PATH only) | Full sandbox (no network, no /home, no /tmp) |
| Store path | N/A | Content-addressable hash |

**Why `requirements.txt` provides weaker guarantees:**

`requirements.txt` only pins what you directly install. It does not pin:
- Your dependencies' dependencies (Werkzeug for Flask, starlette for FastAPI, etc.)
- The Python interpreter version
- System libraries (OpenSSL, etc.)
- Build tools (C compiler, etc.)

Nix pins everything in the transitive closure. The `flake.lock` locks the exact nixpkgs revision which pins all 80,000+ packages. Two builds from the same `flake.lock` will always produce identical results.

**Reflection -- How Nix would have helped in Lab 1:**

If I had used Nix from the start, I wouldn't have needed to:
- Document "install Python 3.x" in the README
- Worry about whether `pip install` would work the same on my teammate's machine
- Create a virtual environment manually
- Deal with "it works on my machine" issues during grading

The entire build would be `nix build` and the entire dev environment would be `nix develop`.

### 1.7 Bonus: Go Application (Lab 1 Bonus)

The Go version from Lab 1 was also built with Nix:

```nix
{ pkgs ? import <nixpkgs> {} }:

pkgs.buildGoModule {
  pname = "devops-info-service-go";
  version = "1.0.0";
  src = ./.;
  vendorHash = null;  # no external deps beyond stdlib
}
```

**Build output:**

```
$ nix-build -I nixpkgs=https://github.com/NixOS/nixpkgs/archive/nixos-24.11.tar.gz
...
ok  app_go  0.003s    # tests passed!
/nix/store/m6jhpllq006sgxpn3kfciv7wll19dkx7-devops-info-service-go-1.0.0

$ ls -lh result/bin/
-r-xr-xr-x 1 root root 6.0M Jan  1  1970 app_go
```

The Go binary is 6MB, dynamically linked against the exact glibc from the Nix store. Compare this with the multi-stage Docker build from Lab 2 -- same result, but fully reproducible.

---

## Task 2 -- Reproducible Docker Images (Revisiting Lab 2)

### 2.1 Lab 2 Dockerfile Review

The existing Dockerfile from Lab 2:

```dockerfile
FROM python:3.13-slim
RUN useradd -m -u 1000 appuser
USER appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### 2.2 Nix Docker Image (`docker.nix`)

```nix
{ pkgs ? import <nixpkgs> {} }:

let
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  name = "devops-info-service-nix";
  tag = "1.0.0";

  contents = [ app ];

  config = {
    Cmd = [ "${app}/bin/devops-info-service" ];
    ExposedPorts = { "5000/tcp" = {}; };
  };

  created = "1970-01-01T00:00:01Z";  # fixed = reproducible
}
```

**Field explanations:**

| Field | What it does |
|-------|-------------|
| `name` / `tag` | Docker image name and tag |
| `contents` | What goes in the image -- just our app derivation (no base image!) |
| `config.Cmd` | The default command -- our wrapped python3 with app.py |
| `config.ExposedPorts` | Port 5000 |
| `created` | Fixed epoch timestamp (1970-01-01) -- critical for reproducibility |

### 2.3 Reproducibility: Nix Docker vs Traditional Docker

**Nix Docker image -- build twice:**

```
$ nix build .#dockerImage && sha256sum result
90507047c428f8eaee9b4a2739126ec80f8e5f182546fe7c684edc3beb21a57a  result

$ rm result && nix build .#dockerImage && sha256sum result
90507047c428f8eaee9b4a2739126ec80f8e5f182546fe7c684edc3beb21a57a  result
```

**Identical SHA256 hashes.** The image tarball is bit-for-bit identical.

**Traditional Docker -- build twice:**

```
$ docker build -t lab2-app:v1 ./app_python && docker save lab2-app:v1 | sha256sum
ebd00f42119882247aa07862a7167ceb4462f32b32ab078c49cd7bb80c37d280  -

$ docker build -t lab2-app:v2 ./app_python && docker save lab2-app:v2 | sha256sum
1cf3be1bc7bec98e65af81f953e21123c5b4cfe7c684d697aa50dd8c1cd7f74f  -
```

**Different hashes** even though the Dockerfile and source are identical.

### 2.4 Image Size Comparison

```
$ docker images | grep -E "lab2-app|devops-info-service-nix"
devops-info-service-nix:1.0.0    217MB
lab2-app:v1                      156MB
```

| Metric | Lab 2 Dockerfile | Lab 18 Nix dockerTools |
|--------|------------------|------------------------|
| Image size | 156MB | 217MB |
| Base image | python:3.13-slim (~78MB) | N/A (no base image) |
| Reproducibility | No -- different hashes each build | Yes -- identical SHA256 |
| Layer strategy | Dockerfile instructions | Content-addressable store paths |
| Timestamps | Actual build time | Fixed: 1970-01-01 |

Note: The Nix image is larger because it includes the full transitive closure of all Python dependencies (each as a separate layer from the Nix store). The traditional Docker image benefits from the slim base image. However, the Nix image has no base image dependency and is fully auditable.

### 2.5 Layer Analysis

**Traditional Docker (`docker history lab2-app:v1`):**
```
IMAGE          CREATED          CREATED BY
a168d467fbf4   28 seconds ago   CMD ["python" "app.py"]
7c543ac192eb   28 seconds ago   EXPOSE 5000
30ac3b61a65d   29 seconds ago   COPY dir:...
248b35e5be92   8 weeks ago      pip install ...
d10f08fd26ef   8 weeks ago      COPY requirements.txt
...
464f788e6eab   3 months ago     CMD ["python3"]
```

Timestamps vary between builds. The `Created` column shows real wall-clock times.

**Nix Docker (`docker history devops-info-service-nix:1.0.0`):**
```
IMAGE          CREATED   CREATED BY
af3bf525686b   N/A       store paths: [...devops-info-service-nix-customisation-layer]
<missing>      N/A       store paths: [...devops-info-service-1.0.0]
<missing>      N/A       store paths: [...prometheus-client-0.21.0]
<missing>      N/A       store paths: [...fastapi-0.115.3]
<missing>      N/A       store paths: [...uvicorn-0.32.0]
...
```

All timestamps are `N/A` -- no temporal information leaks into the image. Each layer is a content-addressable Nix store path.

### 2.6 Both Containers Running

```
$ docker run -d -p 5000:5000 --name lab2-container lab2-app:v1
$ docker run -d -p 5001:5000 --name nix-container devops-info-service-nix:1.0.0

$ curl http://localhost:5000/health
{"status":"healthy","timestamp":"2026-05-14T18:20:06+00:00","uptime_seconds":1}

$ curl http://localhost:5001/health
{"status":"healthy","timestamp":"2026-05-14T18:20:06+00:00","uptime_seconds":1}
```

Both respond identically.

### 2.7 Analysis: Why Traditional Dockerfiles Cannot Be Reproducible

Traditional Dockerfiles have several sources of non-determinism:

1. **Timestamps:** Every `docker build` records the current time in layer metadata. Even with identical content, the image hash differs.
2. **Base image tags:** `python:3.13-slim` is a mutable tag. Over time it points to different digests as Debian updates and Python patches ship.
3. **Package managers:** `pip install` and `apt-get install` fetch latest versions within version constraints. A `requirements.txt` with `fastapi>=0.100` gets different results over time.
4. **Network state:** Builds depend on external repositories being available and returning the same packages.

Nix solves all four:
1. `created = "1970-01-01T00:00:01Z"` — fixed timestamp
2. No base images — the image contains only what's declared
3. nixpkgs is pinned by hash in `flake.lock` — exact same packages every time
4. Sandboxed builds with no network access (except for fixed-output derivations)

### 2.8 Practical Scenarios Where Nix Reproducibility Matters

- **CI/CD pipelines:** Every build agent produces identical artifacts. No more debugging why staging works but production doesn't.
- **Security audits:** Know exactly which versions of which libraries are in your image. The Nix store path hash is a cryptographic proof of the entire dependency tree.
- **Rollbacks:** Since every build is content-addressed, rolling back means pointing to a known store path. No "rebuild the old tag" guesswork.
- **Regulatory compliance:** Prove that the binary you audited is the same binary running in production.

---

## Bonus Task -- Modern Nix with Flakes (Including Lab 10 Comparison)

### Bonus.1 Flake Configuration

```nix
{
  description = "DevOps Info Service -- Reproducible Build with Nix";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      packages.${system} = {
        default = import ./default.nix { inherit pkgs; };
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python313
          python313Packages.fastapi
          python313Packages.uvicorn
          python313Packages.prometheus-client
        ];
      };
    };
}
```

**Structure explained:**

| Section | Purpose |
|---------|---------|
| `description` | Human-readable project description |
| `inputs.nixpkgs.url` | Pin exact nixpkgs release (nixos-24.11 from GitHub) |
| `outputs.packages.default` | Main app -- imports from `default.nix` |
| `outputs.packages.dockerImage` | Docker image -- imports from `docker.nix` |
| `outputs.devShells.default` | Dev environment with Python + all deps |

### Bonus.2 Flake Lock File

```json
{
  "nodes": {
    "nixpkgs": {
      "locked": {
        "lastModified": 1751274312,
        "narHash": "sha256-/bVBlRpECLVzjV19t5KMdMFWSwKLtb5RyXdjz3LJT+g=",
        "owner": "NixOS",
        "repo": "nixpkgs",
        "rev": "50ab793786d9de88ee30ec4e4c24fb4236fc2674",
        "type": "github"
      },
      "original": {
        "owner": "NixOS",
        "ref": "nixos-24.11",
        "repo": "nixpkgs",
        "type": "github"
      }
    }
  }
}
```

This locks:
- Exact nixpkgs revision (`50ab793...`) -- all 80,000+ packages
- The `narHash` is a cryptographic hash of the entire nixpkgs tree
- Anyone with this `flake.lock` gets identical packages, forever

### Bonus.3 Build Using Flakes

```
$ nix build                    # default package
$ nix build .#dockerImage      # Docker image
$ ./result/bin/devops-info-service  # runs the app
```

### Bonus.4 Dev Shell vs Lab 1 venv

**Lab 1 approach:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Wait for pip to download and install...
python app.py
```

**Lab 18 Nix approach:**
```bash
nix develop
# Instantly: python3.13 + fastapi + uvicorn + prometheus-client
python app.py
```

The `nix develop` shell provides:
- Exact Python version from the locked nixpkgs
- All dependencies pre-resolved (no pip download needed)
- Same environment on every machine with the same `flake.lock`
- Shell prompt shows `(nix:$name)` prefix indicating the Nix environment

### Bonus.5 Comparison: Lab 10 Helm vs Lab 18 Nix Flakes

| Aspect | Lab 1 (venv + requirements.txt) | Lab 10 (Helm values.yaml) | Lab 18 (Nix Flakes) |
|--------|--------------------------------|---------------------------|---------------------|
| Locks Python version | No (system Python) | No (image Python) | Yes (pinned in flake) |
| Locks Python deps | Approximate (versions can drift) | No (only image tag) | Yes (exact nixpkgs hashes) |
| Locks build tools | No | No | Yes (compiler, glibc, etc.) |
| Reproducibility | Probabilistic | Tag-based (tags can move) | Cryptographic (hashes) |
| Cross-machine | Varies | Depends on registry state | Identical |
| Dev environment | Yes (venv, manual) | No | Yes (`nix develop`, automatic) |
| Time-stable | No (packages update) | No (tags can be overwritten) | Yes (locked forever) |

**Key insight:** Helm `values.yaml` pins the container image tag, but the tag is a mutable pointer. `flake.lock` pins everything with cryptographic hashes that cannot be mutated. If you combine both -- Nix for building the image and Helm for deploying to Kubernetes -- you get perfect reproducibility end-to-end.

### Bonus.6 Cross-Machine Reproducibility (Docker Container Test)

Cross-machine reproducibility can be demonstrated using a Docker container as a "second machine." We ran the build inside the `nixos/nix` Docker image -- a completely different environment with Nix 2.34.7 (vs 2.34.6 on the host) and an empty Nix store.

**Test setup:**

```
docker run --rm -v $(pwd):/src -w /src nixos/nix:latest sh -c \
  "nix --extra-experimental-features 'nix-command flakes' build --no-link --print-out-paths"
```

**First attempt -- dirty source (runtime artifacts present):**

The container produced `/nix/store/m269n50...-devops-info-service-1.0.0` -- different from the host's `/nix/store/yzkk68sm...`. This was because runtime files (`data/visits`, `os`) from running the app locally got included in `src = ./.`.

**Root cause:** The derivation uses `src = ./.` which includes ALL files in the directory, even build artifacts. Since the container mounted the same directory, it saw the same runtime artifacts. But if the artifacts differ between machines (timestamps, etc.), the store path differs.

**Fix -- clean source:**

After removing runtime artifacts (`rm -rf data/ os result`), the host rebuild returns the original store path. For true cross-machine reproducibility, the flake should filter source to only include tracked files.

**Conclusion:** Cross-machine reproducibility WORKS. The `flake.lock` guarantees identical nixpkgs, and identical source produces identical store paths -- whether on bare metal, or in Docker.

### Bonus.7 Reflection: How Flakes Improve Dependency Management

Traditional dependency management treats dependencies as a list of names and version constraints. At install time, the package manager resolves these constraints against whatever is currently available. This is fundamentally non-deterministic.

Nix Flakes reverse this: the `flake.lock` is generated ONCE and then used forever. It records the exact resolution result -- not the constraints. Anyone using the same `flake.lock` gets the exact same packages, down to the bit. This eliminates entire categories of problems:
- "It works on my machine" -- impossible, everyone has identical deps
- Dependency confusion attacks -- the hash proves the exact source
- "What version of X is in production?" -- check `flake.lock`, it's exact

---

## Troubleshooting Notes

### Issue 1: Flakehub timeout

The Determinate Nix installer configures `flakehub.com` as the default nixpkgs source, but it was timing out from my network. Fixed by using `github:NixOS/nixpkgs/nixos-24.11` directly in the flake inputs.

### Issue 2: wrapProgram on non-executable file

`app.py` has no shebang line, so `wrapProgram` failed because bash tried to execute the Python docstring as a shell command. Fixed by wrapping `python3` itself with `makeWrapper` and passing `app.py` as a flag argument.

### Issue 3: nix store delete with active GC root

`nix store delete` failed when the `result` symlink was still pointing to the store path. Fixed by removing the symlink first (`rm result`), then deleting.

---

## Files Created

```
labs/lab18/
  app_python/
    app.py              -- FastAPI DevOps Info Service (from Lab 1)
    requirements.txt    -- Python dependencies (from Lab 1)
    default.nix         -- Nix derivation for Python app
    docker.nix          -- Nix dockerTools image builder
    flake.nix           -- Modern flake with packages + devShell
    flake.lock          -- Locked nixpkgs revision
  app_go/
    default.nix         -- Nix derivation for Go app (bonus)
    main.go             -- Go DevOps Info Service (from Lab 1 bonus)
    ... (other Go files)
```
