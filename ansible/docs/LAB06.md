# Lab 6: Advanced Ansible & CI/CD - Submission

**Name:** Timofey Ivlev t.ivlev@innopolis.university
**Date:** 2026-03-05
**Lab Points:** 10 + 0 bonus

---

## Task 1: Blocks & Tags (2 pts)

### Implementation

The `common` and `docker` roles were refactored from flat task lists into grouped blocks with shared directives.

Files updated:
- `ansible/roles/common/tasks/main.yml`
- `ansible/roles/common/defaults/main.yml`
- `ansible/roles/docker/tasks/main.yml`
- `ansible/playbooks/provision.yml`

`common` role changes:
- Added package block with `tags: [packages]`
- Added user block with `tags: [users]`
- Added `rescue` logic to recover apt cache and retry install
- Added `always` logic writing `/tmp/common-packages-block.log`
- Applied elevated privileges at block level (`become: true`)

`docker` role changes:
- Added installation block with `tags: [docker_install]`
- Added configuration block with `tags: [docker_config]`
- Added `rescue` retry sequence with 10-second wait and apt cache refresh
- Added `always` section that enforces Docker service enabled and started
- Added role-level tag application in provision playbook (`common`, `docker`)

### Tag Strategy

- Role tags in playbook:
  - `common`
  - `docker`
- Task/block tags:
  - `packages`
  - `users`
  - `docker_install`
  - `docker_config`

### Execution Evidence
Terminal output of `ansible-playbook playbooks/provision.yml --list-tags`.

```
ansible-playbook playbooks/provision.yml --list-tags

playbook: playbooks/provision.yml

  play #1 (webservers): Provision web servers   TAGS: []
      TASK TAGS: [common, docker, docker_config, docker_install, packages, users]
```

Terminal output of selective run: `ansible-playbook playbooks/provision.yml --tags "docker"`.

```
ansible-playbook playbooks/provision.yml --tags "docker"

PLAY [Provision web servers] ****************************************************

TASK [Gathering Facts] **********************************************************
ok: [lab05-vm]

TASK [docker : Create apt keyrings directory] ***********************************
ok: [lab05-vm]

TASK [docker : Download Docker GPG key] *****************************************
changed: [lab05-vm]

TASK [docker : Convert Docker GPG key to apt keyring format] ********************
changed: [lab05-vm]

TASK [docker : Set Docker apt keyring permissions] ******************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] ***************************************
changed: [lab05-vm]

TASK [docker : Install Docker engine packages] **********************************
changed: [lab05-vm]

TASK [docker : Install docker Python binding package] ***************************
changed: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] ********************
ok: [lab05-vm]

TASK [docker : Add users to docker group] ***************************************
changed: [lab05-vm] => (item=ubuntu)

RUNNING HANDLER [docker : restart docker] ***************************************
changed: [lab05-vm]

PLAY RECAP **********************************************************************
lab05-vm                   : ok=11   changed=7    unreachable=0    failed=0    sk
ipped=0    rescued=0    ignored=0                                                

```

Terminal output of selective run: `ansible-playbook playbooks/provision.yml --tags "packages"`.

```
ansible-playbook playbooks/provision.yml --tags "packages"

PLAY [Provision web servers] ****************************************************

TASK [Gathering Facts] **********************************************************
ok: [lab05-vm]

TASK [common : Update apt cache] ************************************************
ok: [lab05-vm]

TASK [common : Install common packages] *****************************************
changed: [lab05-vm]

TASK [common : Set timezone] ****************************************************
changed: [lab05-vm]

TASK [common : Mark common package block completion] ****************************
changed: [lab05-vm]

PLAY RECAP **********************************************************************
lab05-vm                   : ok=5    changed=3    unreachable=0    failed=0    sk
ipped=0    rescued=0    ignored=0                                                

```

### Research Answers

1. What happens if rescue block also fails?
- The task remains failed and play execution follows normal failure rules (stop for that host unless errors are ignored).

2. Can you have nested blocks?
- Yes, Ansible supports nested blocks, but they should be used carefully to avoid hard-to-read flow.

3. How do tags inherit to tasks within blocks?
- Tags on a block are inherited by all tasks inside the block, including rescue/always sections when they belong to that block.

---

## Task 2: Docker Compose (3 pts)

### Implementation

The role was renamed from `app_deploy` to `web_app`, then migrated to Docker Compose with a Jinja2 template and role dependency.

Files updated:
- `ansible/roles/web_app/defaults/main.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/templates/docker-compose.yml.j2`
- `ansible/roles/web_app/meta/main.yml`
- `ansible/playbooks/deploy.yml`
- `ansible/group_vars/all.yml.example`

Compose template variables supported:
- `app_name`
- `docker_image`
- `docker_tag`
- `app_port`
- `app_internal_port`
- `compose_project_dir`
- `docker_compose_version`
- `app_env`
- `app_secret_key`

Role dependency:
- `web_app` now depends on `docker` via `meta/main.yml`, so Docker install runs automatically before app deployment.

Deployment behavior:
- Creates project directory
- Renders `docker-compose.yml`
- Starts stack with `community.docker.docker_compose_v2`
- Performs health checks
- Exposes deployment tags `app_deploy`, `compose`

### Before/After Comparison

Before:
- Single-container deployment via `community.docker.docker_container`

After:
- Declarative stack via Compose (`docker-compose.yml.j2` + `docker_compose_v2`)

### Evidence

Terminal output of `ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass` showing compose deployment success.

```
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] *******************************************************

TASK [Gathering Facts] **********************************************************
ok: [lab05-vm]

TASK [docker : Create apt keyrings directory] ***********************************
ok: [lab05-vm]

TASK [docker : Download Docker GPG key] *****************************************
ok: [lab05-vm]

TASK [docker : Convert Docker GPG key to apt keyring format] ********************
skipping: [lab05-vm]

TASK [docker : Set Docker apt keyring permissions] ******************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] ***************************************
ok: [lab05-vm]

TASK [docker : Install Docker engine packages] **********************************
ok: [lab05-vm]

TASK [docker : Install docker Python binding package] ***************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] ********************
ok: [lab05-vm]

TASK [docker : Add users to docker group] ***************************************
ok: [lab05-vm] => (item=ubuntu)

TASK [web_app : Include wipe tasks] *********************************************
included: /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course
/ansible/roles/web_app/tasks/wipe.yml for lab05-vm                               
TASK [web_app : Stop and remove compose services] *******************************
skipping: [lab05-vm]

TASK [web_app : Remove docker-compose manifest] *********************************
skipping: [lab05-vm]

TASK [web_app : Remove compose project directory] *******************************
skipping: [lab05-vm]

TASK [web_app : Optionally remove application image] ****************************
skipping: [lab05-vm]

TASK [web_app : Log wipe completion] ********************************************
skipping: [lab05-vm]

TASK [web_app : Ensure Docker service is running] *******************************
ok: [lab05-vm]

TASK [web_app : Create compose project directory] *******************************
changed: [lab05-vm]

TASK [web_app : Render docker-compose manifest] *********************************
changed: [lab05-vm]

TASK [web_app : Start services via Docker Compose] ******************************
[WARNING]: Cannot parse event from line: 'time="2026-03-05T18:55:42Z"
level=warning msg="/opt/devops-lab03-python/docker-compose.yml: the attribute
`version` is obsolete, it will be ignored, please remove it to avoid potential
confusion"'. Please report this at https://github.com/ansible-collections/commun
ity.docker/issues/new?assignees=&labels=&projects=&template=bug_report.md
changed: [lab05-vm]

TASK [web_app : Wait for application port] **************************************
ok: [lab05-vm]

TASK [web_app : Verify health endpoint] *****************************************
ok: [lab05-vm]

PLAY RECAP **********************************************************************
lab05-vm                   : ok=16   changed=3    unreachable=0    failed=0    sk
ipped=6    rescued=0    ignored=0                                                

```

Idempotency evidence: second run should be mostly `ok`:

```
ansible-playbook playbooks/deploy.yml --vault-password-file .vault_pass

PLAY [Deploy application] *******************************************************

TASK [Gathering Facts] **********************************************************
ok: [lab05-vm]

TASK [docker : Create apt keyrings directory] ***********************************
ok: [lab05-vm]

TASK [docker : Download Docker GPG key] *****************************************
ok: [lab05-vm]

TASK [docker : Convert Docker GPG key to apt keyring format] ********************
skipping: [lab05-vm]

TASK [docker : Set Docker apt keyring permissions] ******************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] ***************************************
ok: [lab05-vm]

TASK [docker : Install Docker engine packages] **********************************
ok: [lab05-vm]

TASK [docker : Install docker Python binding package] ***************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] ********************
ok: [lab05-vm]

TASK [docker : Add users to docker group] ***************************************
ok: [lab05-vm] => (item=ubuntu)

TASK [web_app : Include wipe tasks] *********************************************
included: /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/ans
ible/roles/web_app/tasks/wipe.yml for lab05-vm                                       
TASK [web_app : Stop and remove compose services] *******************************
skipping: [lab05-vm]

TASK [web_app : Remove docker-compose manifest] *********************************
skipping: [lab05-vm]

TASK [web_app : Remove compose project directory] *******************************
skipping: [lab05-vm]

TASK [web_app : Optionally remove application image] ****************************
skipping: [lab05-vm]

TASK [web_app : Log wipe completion] ********************************************
skipping: [lab05-vm]

TASK [web_app : Ensure Docker service is running] *******************************
ok: [lab05-vm]

TASK [web_app : Create compose project directory] *******************************
ok: [lab05-vm]

TASK [web_app : Render docker-compose manifest] *********************************
ok: [lab05-vm]

TASK [web_app : Start services via Docker Compose] ******************************
[WARNING]: Cannot parse event from line: 'time="2026-03-05T18:59:42Z"
level=warning msg="/opt/devops-lab03-python/docker-compose.yml: the attribute
`version` is obsolete, it will be ignored, please remove it to avoid potential
confusion"'. Please report this at https://github.com/ansible-collections/commun
ity.docker/issues/new?assignees=&labels=&projects=&template=bug_report.md
ok: [lab05-vm]

TASK [web_app : Wait for application port] **************************************
ok: [lab05-vm]

TASK [web_app : Verify health endpoint] *****************************************
ok: [lab05-vm]

PLAY RECAP **********************************************************************
lab05-vm                   : ok=16   changed=0    unreachable=0    failed=0    skippe
d=6    rescued=0    ignored=0                                                        

```

Rendered file output: `cat /opt/devops-lab03-python/docker-compose.yml` from VM.

```
cat docker-compose.yml 
version: "3.8"

services:
  devops-lab03-python:
    image: "timofeq1/devops-lab03-python:latest"
    container_name: "devops-lab03-python"
    ports:
      - "5000:5000"
    environment:
      PORT: "5000"
      APP_ENV: "production"
      APP_SECRET_KEY: "change-me"
    restart: unless-stopped
    networks:
      - devops-lab03-python_net

networks:
  devops-lab03-python_net:
    driver: bridge
```

Verification output: `docker ps` and `curl http://<vm_ip>:5000/health`.

```
docker ps
CONTAINER ID   IMAGE                                 COMMAND           CREATED          STATUS          PORTS                                         NAMES
ea5e5de5ca49   timofeq1/devops-lab03-python:latest   "python app.py"   17 minutes ago   Up 17 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp   devops-lab03-python

curl http://<vm_ip>:5000/health
{"status":"healthy","timestamp":"2026-03-05T19:15:18.396332+00:00","uptime_seconds":1163}
```

### Research Answers

1. Difference between `restart: always` and `restart: unless-stopped`?
- `always` restarts even after manual stop and daemon restart; `unless-stopped` restarts automatically except when intentionally stopped by operator.

2. How do Compose networks differ from default bridge?
- Compose creates project-scoped networks with automatic DNS service discovery and isolation per stack.

3. Can template reference Vault variables?
- Yes. Vault-decrypted variables are available during templating and can be injected into Jinja2 output.

---

## Task 3: Wipe Logic (1 pt)

### Implementation

Safe wipe logic is implemented with double gating:
- Variable gate: `web_app_wipe | bool`
- Tag gate: `web_app_wipe`

Files updated:
- `ansible/roles/web_app/tasks/wipe.yml`
- `ansible/roles/web_app/tasks/main.yml`
- `ansible/roles/web_app/defaults/main.yml`

Behavior:
- Wipe tasks are included first from `main.yml`
- Wipe block runs only when `web_app_wipe=true`
- Wipe block is tag-targeted (`--tags web_app_wipe`)
- Optional image cleanup via `web_app_wipe_remove_images`

### Scenario Results

1. Scenario 1: Normal deployment (wipe should not run)
- Expected: deployment runs, wipe skipped (command and output provided above)

1. Scenario 2: Wipe only
- Command:
  - `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass`
- Expected: app removed; deploy tasks skipped.

```
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --tags web_app_wipe --vault-password-file .vault_pass

PLAY [Deploy application] ***********************************************************

TASK [Gathering Facts] **************************************************************
ok: [lab05-vm]

TASK [web_app : Include wipe tasks] *************************************************
included: /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/ans
ible/roles/web_app/tasks/wipe.yml for lab05-vm                                       
TASK [web_app : Stop and remove compose services] ***********************************
[WARNING]: Cannot parse event from line: 'time="2026-03-05T19:17:36Z" level=warning
msg="/opt/devops-lab03-python/docker-compose.yml: the attribute `version` is
obsolete, it will be ignored, please remove it to avoid potential confusion"'.
Please report this at https://github.com/ansible-collections/community.docker/issues
/new?assignees=&labels=&projects=&template=bug_report.md
changed: [lab05-vm]

TASK [web_app : Remove docker-compose manifest] *************************************
changed: [lab05-vm]

TASK [web_app : Remove compose project directory] ***********************************
changed: [lab05-vm]

TASK [web_app : Optionally remove application image] ********************************
skipping: [lab05-vm]

TASK [web_app : Log wipe completion] ************************************************
ok: [lab05-vm] => {
    "msg": "Application devops-lab03-python wiped successfully"
}

PLAY RECAP **************************************************************************
lab05-vm                   : ok=6    changed=3    unreachable=0    failed=0    skippe
d=1    rescued=0    ignored=0                                                        
```

**docker ps**

```
ubuntu@fhml66r4npuncpbadrqv:~$ docker ps
CONTAINER ID   IMAGE     COMMAND   CREATED   STATUS    PORTS     NAMES
ubuntu@fhml66r4npuncpbadrqv:~$ 
```

1. Scenario 3: Clean reinstall (wipe -> deploy)
- Command:
  - `ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --vault-password-file .vault_pass`
- Expected: wipe tasks first, then fresh deploy.

```
ansible-playbook playbooks/deploy.yml -e "web_app_wipe=true" --vault-password-file .vault_pass

PLAY [Deploy application] ***********************************************************

TASK [Gathering Facts] **************************************************************
ok: [lab05-vm]

TASK [docker : Create apt keyrings directory] ***************************************
ok: [lab05-vm]

TASK [docker : Download Docker GPG key] *********************************************
ok: [lab05-vm]

TASK [docker : Convert Docker GPG key to apt keyring format] ************************
skipping: [lab05-vm]

TASK [docker : Set Docker apt keyring permissions] **********************************
ok: [lab05-vm]

TASK [docker : Add Docker apt repository] *******************************************
ok: [lab05-vm]

TASK [docker : Install Docker engine packages] **************************************
ok: [lab05-vm]

TASK [docker : Install docker Python binding package] *******************************
ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] ************************
ok: [lab05-vm]

TASK [docker : Add users to docker group] *******************************************
ok: [lab05-vm] => (item=ubuntu)

TASK [web_app : Include wipe tasks] *************************************************
included: /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/ans
ible/roles/web_app/tasks/wipe.yml for lab05-vm                                       
TASK [web_app : Stop and remove compose services] ***********************************
ok: [lab05-vm]

TASK [web_app : Remove docker-compose manifest] *************************************
ok: [lab05-vm]

TASK [web_app : Remove compose project directory] ***********************************
ok: [lab05-vm]

TASK [web_app : Optionally remove application image] ********************************
skipping: [lab05-vm]

TASK [web_app : Log wipe completion] ************************************************
ok: [lab05-vm] => {
    "msg": "Application devops-lab03-python wiped successfully"
}

TASK [web_app : Ensure Docker service is running] ***********************************
ok: [lab05-vm]

TASK [web_app : Create compose project directory] ***********************************
changed: [lab05-vm]

TASK [web_app : Render docker-compose manifest] *************************************
changed: [lab05-vm]

TASK [web_app : Start services via Docker Compose] **********************************
[WARNING]: Cannot parse event from line: 'time="2026-03-05T19:21:57Z" level=warning
msg="/opt/devops-lab03-python/docker-compose.yml: the attribute `version` is
obsolete, it will be ignored, please remove it to avoid potential confusion"'.
Please report this at https://github.com/ansible-collections/community.docker/issues
/new?assignees=&labels=&projects=&template=bug_report.md
changed: [lab05-vm]

TASK [web_app : Wait for application port] ******************************************
ok: [lab05-vm]

TASK [web_app : Verify health endpoint] *********************************************
ok: [lab05-vm]

PLAY RECAP **************************************************************************
lab05-vm                   : ok=20   changed=3    unreachable=0    failed=0    skippe
d=2    rescued=0    ignored=0                                                        

```

1. Scenario 4a: Tag set, variable false
- Command:
  - `ansible-playbook playbooks/deploy.yml --tags web_app_wipe --vault-password-file .vault_pass`
- Expected: wipe block skipped due to `when` condition.

```
ansible-playbook playbooks/deploy.yml --tags web_app_wipe --vault-password-file .vault_pass

PLAY [Deploy application] ***********************************************************

TASK [Gathering Facts] **************************************************************
ok: [lab05-vm]

TASK [web_app : Include wipe tasks] *************************************************
included: /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/ans
ible/roles/web_app/tasks/wipe.yml for lab05-vm                                       
TASK [web_app : Stop and remove compose services] ***********************************
skipping: [lab05-vm]

TASK [web_app : Remove docker-compose manifest] *************************************
skipping: [lab05-vm]

TASK [web_app : Remove compose project directory] ***********************************
skipping: [lab05-vm]

TASK [web_app : Optionally remove application image] ********************************
skipping: [lab05-vm]

TASK [web_app : Log wipe completion] ************************************************
skipping: [lab05-vm]

PLAY RECAP **************************************************************************
lab05-vm                   : ok=2    changed=0    unreachable=0    failed=0    skippe
d=5    rescued=0    ignored=0                                                        

```

### Research Answers

1. Why both variable and tag?
- It is a double safety mechanism. Both operator intent and explicit run targeting are needed.

2. Difference vs `never` tag?
- `never` hides tasks from normal runs unless explicitly included. Variable+tag adds runtime policy control and allows combined flows like wipe+deploy in one run.

3. Why place wipe before deployment?
- It enables clean reinstall in one command: remove previous state first, then deploy fresh state.

4. When clean reinstall vs rolling update?
- Clean reinstall for drift/corruption/testing reset. Rolling update for minimal downtime and preserving runtime state.

5. How extend wipe to volumes/images?
- Add optional cleanup flags and extra Compose/module steps for `docker volume rm` / image removal guarded by separate booleans.

---

## Task 4: CI/CD (3 pts)

### Workflow Added

File created:
- `.github/workflows/ansible-deploy.yml`

Pipeline design:
- Triggered only on Ansible/workflow changes
- Path filters exclude `ansible/docs/**`
- `lint` job:
  - installs `ansible-core`, `ansible-lint`
  - installs required collections
  - lints playbooks and roles
- `deploy` job (push only):
  - configures SSH to Yandex Cloud VM
  - builds runtime inventory dynamically from GitHub Secrets
  - runs `provision.yml` with `common,docker` tags
  - runs `deploy.yml` with `app_deploy,compose` tags
  - verifies service with `curl`

### Required Secrets

- `ANSIBLE_VAULT_PASSWORD`
- `SSH_PRIVATE_KEY`
- `VM_HOST`
- `VM_USER`

### Badge

File created:
- `ansible/README.md`

Includes workflow badge and repository URL.

### Research Answers

1. Security implications of SSH keys in GitHub Secrets?
- Secret exposure risk exists if workflow is misconfigured or malicious code runs on trusted branches. Use environment protection, least privilege keys, and short key rotation windows.

2. Staging -> production pipeline approach?
- Use separate environments, required approvals, and environment-scoped secrets. Promote same artifact/config from staging after checks.

3. What to add for rollback?
- Store release tags, keep previous compose files/image tags, and add a rollback workflow that redeploys last known good version.

4. Self-hosted vs GitHub-hosted security?
- Self-hosted can avoid exposing infra credentials to external runners and keeps deployment traffic inside controlled network boundaries.

---

## Task 5: Documentation (1 pt)

This file documents implementation, testing strategy, and research analysis.

### Challenges and Solutions

- Challenge: Existing role used direct container module instead of Compose.
- Solution: Introduced `docker_compose_v2` with Jinja2 template and dependency metadata.

- Challenge: Preventing accidental destructive wipe runs.
- Solution: Implemented variable + tag gating and defaulted wipe to disabled.

- Challenge: CI deploy target is Yandex Cloud VM with dynamic IP/user.
- Solution: Workflow creates inventory from GitHub Secrets at runtime.

---

## Overview

- Completed Lab 6 scope for advanced Ansible and CI/CD on a Yandex Cloud VM target.
- Refactored roles with block/rescue/always patterns and selective tags.
- Migrated app deployment to Docker Compose with role dependency and wipe safety controls.
- Added GitHub Actions automation for lint, deploy, and endpoint verification.

## Blocks & Tags

- Implemented in `ansible/roles/common/tasks/main.yml` and `ansible/roles/docker/tasks/main.yml`.
- Tag model includes role-level (`common`, `docker`) and block-level (`packages`, `users`, `docker_install`, `docker_config`) targeting.
- See Task 1 section for detailed command examples and evidence placeholders.

## Docker Compose Migration

- Implemented in `ansible/roles/web_app/` with template-based Compose deployment.
- Migration details, dependency wiring, and before/after comparison are documented in Task 2.

## Wipe Logic

- Implemented in `ansible/roles/web_app/tasks/wipe.yml` and included first in `ansible/roles/web_app/tasks/main.yml`.
- Uses variable + tag double gate (`web_app_wipe` + `web_app_wipe` tag).
- Scenario-based validation checklist is in Task 3.

## CI/CD Integration

- Workflow implemented at `.github/workflows/ansible-deploy.yml`.
- Includes path filters, lint stage, deploy stage, and service verification.
- Required GitHub Secrets are listed in Task 4.

## Testing Results

- Static checks completed locally:
  - `ansible-playbook playbooks/provision.yml --syntax-check --vault-password-file .vault_pass`
  - `ansible-playbook playbooks/deploy.yml --syntax-check --vault-password-file .vault_pass`
  - `ansible-playbook playbooks/provision.yml --list-tags --vault-password-file .vault_pass`
  - `ansible-playbook playbooks/deploy.yml --list-tags --vault-password-file .vault_pass`
- Manual runtime evidence still required and marked with `#TODO` entries above.

## Challenges & Solutions

- See the Task 5 subsection "Challenges and Solutions".

## Research Answers

- Research answers are provided in Task 1, Task 2, Task 3, and Task 4 sections.

---

## Acceptance Criteria Check

- [x] `common` role uses blocks, rescue/always, and tags (`packages`, `users`).
- [x] `docker` role uses blocks, rescue/always, and tags (`docker_install`, `docker_config`).
- [x] `app_deploy` role renamed to `web_app` and playbook references updated.
- [x] Docker Compose template added and used in deployment tasks.
- [x] Role dependency added: `web_app` depends on `docker`.
- [x] Wipe logic implemented with variable + tag (`web_app_wipe`).
- [x] CI workflow added for lint + deploy + verification.
- [x] Ansible status badge added in `ansible/README.md`.
- [x] Documentation created at `ansible/docs/LAB06.md`.
- [x] Manual runtime evidence attached (terminal outputs).

---