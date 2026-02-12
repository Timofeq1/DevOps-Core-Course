# Lab 3 — Continuous Integration (CI/CD)

## 1. Overview

**Testing Framework:**
I chose **pytest** because it offers a simple, concise syntax compared to `unittest`, maintains excellent compatibility, and supports powerful features like fixtures and a rich ecosystem of plugins (e.g., `pytest-cov` for coverage). It is the industry standard for modern Python testing.

**Coverage:**
Unit tests in `app_python/tests/test_app.py` cover:
- `GET /`: Verifies status code (200), JSON structure, and correct service metadata.
- `GET /health`: Verifies status code (200), healthy status, and uptime presence.
- `GET /non-existent`: Verifies 404 error handling for invalid paths.

**CI Workflow Trigger:**
The `python-ci.yml` workflow triggers on:
- **Push** to `main` or `master` branches.
- **Pull Request** to `main` or `master` branches.
- **Path Filtering:** Only runs when files in `app_python/` or the workflow file itself change, avoiding unnecessary runs for Go app changes (Bonus Task).

**Versioning Strategy:**
I chose **Calendar Versioning (CalVer)** with format `YYYY.MM.DD`.
Rationale: For a continuously deployed service like this, date-based versioning provides immediate context on when the artifact was built, which is often more useful than arbitrary semantic numbers. The CI also tags with `latest` and the commit SHA for precise tracking.

## 2. Workflow Evidence

- **Successful Workflow Run:** [Link to GitHub Actions](https://github.com/timofeq1/DevOps-Core-Course/actions)
- **Docker Hub Image:** [timofeq1/devops-lab02](https://hub.docker.com/r/timofeq1/devops-lab02)

**Tests Passing Locally:**
```text
(venv) timofey@lenovoARH7:~/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/app_python$ ./venv/bin/pytest 
============================ test session starts =============================
platform linux -- Python 3.12.3, pytest-8.0.0, pluggy-1.6.0
rootdir: /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/app_python
plugins: anyio-4.12.1, cov-4.1.0
collected 3 items                                                            

tests/test_app.py ...                                                  [100%]

============================= 3 passed in 0.37s ==============================
```

**Workflow Status:**
![Python CI](https://github.com/timofey/devops-lab03/actions/workflows/python-ci.yml/badge.svg)

## 3. Best Practices Implemented

1.  **Dependency Caching (`cache: 'pip'`):** Speeds up workflows by caching downloaded pip packages between runs, reducing installation time significantly (e.g., from ~1m to ~10s).
2.  **Linting (`pylint`):** Ensures code quality and consistency before testing, failing fast if syntax or style violations occur.
3.  **Concurrency Management:** Automatically cancels outdated in-progress runs on the same branch to save CI resources.
4.  **Security Scanning (Snyk):** Proactively detects vulnerabilities in dependencies defined in `requirements.txt` to prevent security issues.
5.  **Timeout Limits:** `timeout-minutes` is set to prevent stalled jobs from consuming all compute minutes.

**Snyk Results:**
Snyk scanning is integrated. If vulnerabilities are found (e.g., in `fastapi` or `uvicorn`), the report details them. Currently set to warn only (`continue-on-error: true`) to ensure lab workflow continuity, but in production, high-severity issues should block deployment.

## 4. Key Decisions

-   **Versioning Strategy:** **CalVer**. I chose it because for a web service, the "release date" is often the most meaningful identifier for deployed artifacts.
-   **Docker Tags:** The CI creates: `latest`, `YYYY.MM.DD`, and `sha-<long_sha>`. `latest` for easy pulling, date for releases, commit SHA for precise rollback.
-   **Workflow Triggers:** Restricted to `app_python/` paths using Path Filters. This ensures that changes to the Go application do not trigger the Python CI pipeline, respecting the monorepo structure.
-   **Test Coverage:** Key endpoints (`/`, `/health`) are fully tested. Simple startup logic or logging config might be excluded. Coverage goal is functional correctness of API contracts.

## 5. Challenges

-   **Path Context:** Initial manual runs encountered directory context issues (`cd app_python`), resolved by using `defaults.run.working-directory` in GitHub Actions and correct relative paths in local testing.
-   **Linting:** Pylint found trailing whitespaces and missing docstrings in the provided `app.py`, which were fixed to ensure a clean codebase.
