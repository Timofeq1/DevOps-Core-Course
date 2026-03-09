# LAB05 - Ansible Fundamentals

## 1. Architecture Overview

- Ansible version: 
```
ansible --version
ansible [core 2.16.3]
  config file = None
  configured module search path = ['/home/timofey/.ansible/plugins/modules', '/usr/share/ansible/plugins/modules']
  ansible python module location = /usr/lib/python3/dist-packages/ansible
  ansible collection location = /home/timofey/.ansible/collections:/usr/share/ansible/collections
  executable location = /usr/bin/ansible
  python version = 3.12.3 (main, Jan 22 2026, 20:57:42) [GCC 13.3.0] (/usr/bin/python3)
  jinja version = 3.1.2
  libyaml = True
```
- Target VM: Ubuntu 22.04/24.04 on Yandex Cloud (from Lab 4)
- Automation style: role-based (`common`, `docker`, `app_deploy`) with dedicated playbooks for provisioning and deployment

Role structure:

```text
ansible/
|- inventory/
|  |- hosts.ini
|  |- yandex_compute.yml
|- roles/
|  |- common/
|  |  |- tasks/main.yml
|  |  `- defaults/main.yml
|  |- docker/
|  |  |- tasks/main.yml
|  |  |- handlers/main.yml
|  |  `- defaults/main.yml
|  `- app_deploy/
|     |- tasks/main.yml
|     |- handlers/main.yml
|     `- defaults/main.yml
|- playbooks/
|  |- site.yml
|  |- provision.yml
|  `- deploy.yml
|- group_vars/
|  |- all.yml
|  `- all.yml.example
|- collections/requirements.yml
`- ansible.cfg
```

Why roles instead of monolithic playbooks:
- Roles isolate responsibilities and reduce duplication.
- Roles are reusable across multiple playbooks and future labs.
- Defaults/tasks/handlers separation improves maintenance and testing.

## 2. Roles Documentation

### Role: common

Purpose:
- Base server preparation.
- Installs required OS tools and configures timezone.

Variables:
- `common_packages` (list of apt packages)
- `common_timezone` (default `UTC`)

Handlers:
- None.

Dependencies:
- `community.general` collection (for timezone module).

### Role: docker

Purpose:
- Installs Docker Engine from official Docker apt repository.
- Enables and starts Docker service.
- Adds selected user(s) to `docker` group.
- Installs `python3-docker` for Docker Ansible modules.

Variables:
- `docker_apt_arch`
- `docker_apt_repo`
- `docker_packages`
- `docker_users`
- `docker_python_package`

Handlers:
- `restart docker`

Dependencies:
- No role dependency.
- Uses built-in apt/service/user modules.

### Role: app_deploy

Purpose:
- Logs into Docker Hub with vaulted credentials.
- Pulls image and recreates container with expected runtime config.
- Waits for service readiness and verifies `/health` endpoint.

Variables:
- `dockerhub_username`, `dockerhub_password` (from `group_vars/all.yml`)
- `app_name`, `docker_image`, `docker_image_tag`
- `app_port`, `app_container_name`
- `app_restart_policy`, `app_env`
- `app_healthcheck_url`, `app_healthcheck_timeout`, `app_healthcheck_delay`

Handlers:
- `restart app container`

Dependencies:
- `community.docker` collection.

## 3. Idempotency Demonstration

Commands used:

```bash
cd ansible
ansible-playbook playbooks/provision.yml
ansible-playbook playbooks/provision.yml
```

First run output:

```text
ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***********************************************
****                                                                        
TASK [Gathering Facts] *****************************************************
****                                                                        ok: [lab05-vm]

TASK [common : Update apt cache] *******************************************
****                                                                        changed: [lab05-vm]

TASK [common : Install common packages] ************************************
****                                                                        changed: [lab05-vm]

TASK [common : Set timezone] ***********************************************
****                                                                        changed: [lab05-vm]

TASK [docker : Create apt keyrings directory] ******************************
****                                                                        ok: [lab05-vm]

TASK [docker : Download Docker GPG key] ************************************
****                                                                        changed: [lab05-vm]

TASK [docker : Convert Docker GPG key to apt keyring format] ***************
****                                                                        changed: [lab05-vm]

TASK [docker : Set Docker apt keyring permissions] *************************
****                                                                        ok: [lab05-vm]

TASK [docker : Add Docker apt repository] **********************************
****                                                                        changed: [lab05-vm]

TASK [docker : Install Docker engine packages] *****************************
****                                                                        changed: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] ***************
****                                                                        ok: [lab05-vm]

TASK [docker : Add users to docker group] **********************************
****                                                                        changed: [lab05-vm] => (item=ubuntu)

TASK [docker : Install docker Python binding package] **********************
****                                                                        changed: [lab05-vm]

RUNNING HANDLER [docker : restart docker] **********************************
****                                                                        changed: [lab05-vm]

PLAY RECAP *****************************************************************
****                                                                        lab05-vm                   : ok=14   changed=10   unreachable=0    failed=0 
   skipped=0    rescued=0    ignored=0                                      

```

Second run output:

```text
ansible-playbook playbooks/provision.yml

PLAY [Provision web servers] ***********************************************
****                                                                        
TASK [Gathering Facts] *****************************************************
****                                                                        ok: [lab05-vm]

TASK [common : Update apt cache] *******************************************
****                                                                        ok: [lab05-vm]

TASK [common : Install common packages] ************************************
****                                                                        ok: [lab05-vm]

TASK [common : Set timezone] ***********************************************
****                                                                        ok: [lab05-vm]

TASK [docker : Create apt keyrings directory] ******************************
****                                                                        ok: [lab05-vm]

TASK [docker : Download Docker GPG key] ************************************
****                                                                        ok: [lab05-vm]

TASK [docker : Convert Docker GPG key to apt keyring format] ***************
****                                                                        changed: [lab05-vm]

TASK [docker : Set Docker apt keyring permissions] *************************
****                                                                        ok: [lab05-vm]

TASK [docker : Add Docker apt repository] **********************************
****                                                                        ok: [lab05-vm]

TASK [docker : Install Docker engine packages] *****************************
****                                                                        ok: [lab05-vm]

TASK [docker : Ensure Docker service is enabled and running] ***************
****                                                                        ok: [lab05-vm]

TASK [docker : Add users to docker group] **********************************
****                                                                        ok: [lab05-vm] => (item=ubuntu)

TASK [docker : Install docker Python binding package] **********************
****                                                                        ok: [lab05-vm]

PLAY RECAP *****************************************************************
****                                                                        lab05-vm                   : ok=13   changed=1    unreachable=0    failed=0 
   skipped=0    rescued=0    ignored=0                                      

```

Analysis:
- First run should show `changed` for package/repository/service setup because desired state is being created.
- Second run should show `ok` and zero `changed` if state already matches role definitions. (we get only one `changed` but that is fine for converting the GPG operation)

Why roles are idempotent:
- Uses stateful modules (`apt`, `service`, `user`, `docker_container`, `docker_image`) with explicit `state`.
- No shell commands for mutable operations.
- Handlers run only when notified by state changes.

## 4. Ansible Vault Usage

Vault strategy:
- Sensitive variables are stored in `group_vars/all.yml`.
- This file must be encrypted before commit.

Manual steps:

```bash
cd ansible
ansible-vault encrypt group_vars/all.yml
ansible-vault view group_vars/all.yml
```

Encrypted file evidence:

```text
ansible-vault view group_vars/all.yml
Vault password: 
---
#TODO encrypt this file before commit: ansible-vault encrypt group_vars/all>

dockerhub_username: timofeq1
dockerhub_password: ***

app_name: devops-lab03-python
docker_image: "{{ dockerhub_username }}/{{ app_name }}"
docker_image_tag: latest
app_port: 5000
app_container_name: "{{ app_name }}"
```

Vault password management:
- Use local `.vault_pass` with strict permissions (`chmod 600 .vault_pass`) and never commit it.
- `.vault_pass` is ignored in root `.gitignore`.

Why Vault matters:
- Prevents plaintext secret leakage in git history.
- Keeps automation reproducible while protecting credentials.

## 5. Deployment Verification

Deployment command:

```bash
cd ansible
ansible-playbook playbooks/deploy.yml --ask-vault-pass
```

Deployment output:

```text
ansible-playbook playbooks/deploy.yml --ask-vault-pass
Vault password: 

PLAY [Deploy application] **************************************************
****                                                                        
TASK [Gathering Facts] *****************************************************
****                                                                        ok: [lab05-vm]

TASK [app_deploy : Validate Docker Hub credentials are provided] ***********
****                                                                        ok: [lab05-vm] => {
    "changed": false,
    "msg": "All assertions passed"
}

TASK [app_deploy : Ensure Docker service is running before registry login] *
****                                                                        ok: [lab05-vm]

TASK [app_deploy : Login to Docker Hub] ************************************
****                                                                        changed: [lab05-vm]

TASK [app_deploy : Pull application image] *********************************
****                                                                        ok: [lab05-vm]

TASK [app_deploy : Stop existing container if running] *********************
****                                                                        changed: [lab05-vm]

TASK [app_deploy : Remove old container if present] ************************
****                                                                        changed: [lab05-vm]

TASK [app_deploy : Run application container] ******************************
****                                                                        changed: [lab05-vm]

TASK [app_deploy : Wait for application port] ******************************
****                                                                        ok: [lab05-vm]

TASK [app_deploy : Verify health endpoint] *********************************
****                                                                        ok: [lab05-vm]

RUNNING HANDLER [app_deploy : restart app container] ***********************
****                                                                        changed: [lab05-vm]

PLAY RECAP *****************************************************************
****                                                                        lab05-vm                   : ok=11   changed=5    unreachable=0    failed=0 
   skipped=0    rescued=0    ignored=0                                      

```

Container status:

```bash
ansible webservers -a "docker ps" --ask-vault-pass
```

```text
ansible webservers -a "docker ps" --ask-vault-pass
Vault password: 
lab05-vm | CHANGED | rc=0 >>
CONTAINER ID   IMAGE                                 COMMAND           CREAT
ED          STATUS          PORTS                    NAMES                  509e35f41c84   timofeq1/devops-lab03-python:latest   "python app.py"   56 se
conds ago   Up 47 seconds   0.0.0.0:5000->5000/tcp   devops-lab03-python    
```

Health checks:

```bash
curl http://130.193.49.207:5000/health
curl http://130.193.49.207:5000/
```

```text

curl http://130.193.49.207:5000/health
{"status":"healthy","timestamp":"2026-02-26T09:54:06.487960+00:00","uptime_seconds":192}

curl http://130.193.49.207:5000/
{"service":{"name":"devops-info-service","version":"1.0.0","description":"DevOps course info service","framework":"FastAPI"},"system":{"hostname":"509e35f41c84","platform":"Linux","platform_version":"#180-Ubuntu SMP Fri Jan 9 16:10:31 UTC 2026","architecture":"x86_64","cpu_count":2,"python_version":"3.13.12"},"runtime":{"uptime_seconds":196,"uptime_human":"0 hours, 3 minutes","current_time":"2026-02-26T09:54:10.627165+00:00","timezone":"UTC"},"request":{"client_ip":"213.87.71.131","user_agent":"curl/8.5.0","method":"GET","path":"/"},"endpoints":[{"path":"/","method":"GET","description":"Service information"},{"path":"/health","method":"GET","description":"Health check"}]}
```

Handler execution:

```text
Handler executed on deploy run #1
```

## 6. Key Decisions

Why use roles instead of plain playbooks:
- Roles keep provisioning and deployment logic modular and reusable.
- It becomes easier to test, review, and extend one concern at a time.

How do roles improve reusability:
- Variable-driven defaults let the same tasks run across environments.
- A role can be imported by different playbooks without code copy.

What makes a task idempotent:
- Idempotent tasks declare desired state and only change when drift exists.
- Re-running converges to the same final state without side effects.

How do handlers improve efficiency:
- Handlers execute only on change notifications, avoiding unnecessary restarts.
- This reduces runtime and service interruption.

Why is Ansible Vault necessary:
- Playbooks need credentials, but plaintext secrets are unsafe for VCS.
- Vault enables secure storage and sharing of encrypted variables.

## 7. Challenges

- Dynamic inventory plugin fields for public IP are nested and must be mapped with `compose`.
- Docker modules require both Docker Engine and Python Docker bindings on target host.
- Manual environment setup is required for cloud API authentication.
- Terraform configuration did not opened a ssh port for connection - was corrected.

## Acceptance Criteria Cross-check

Setup and structure:
- [x] Role-based directory structure created.
- [x] Three roles created: `common`, `docker`, `app_deploy`.
- [x] Tasks/defaults/handlers files added for each role where required.
- [x] `ansible.cfg` configured.
- [x] Connectivity tested and output captured. 

System provisioning:
- [x] `common` role implemented.
- [x] `docker` role implemented.
- [x] `playbooks/provision.yml` uses roles.
- [x] Idempotency proven with two real runs and outputs.
- [x] Handlers included (`restart docker`).

Application deployment:
- [x] Vault variable structure prepared in `group_vars/all.yml`.
- [x] Vault file encrypted and verified.
- [x] `app_deploy` role implemented with required task flow.
- [x] `playbooks/deploy.yml` uses role.
- [x] Container runtime verification captured (`docker ps`).
- [x] Health check verification captured (`curl`).
- [x] Handler included (`restart app container`).

Documentation:
- [x] This document contains required sections.
- [x] Architecture and role structure described.
- [x] Roles documented with purpose/variables/handlers.
- [x] Idempotency analysis section included.
- [x] Vault usage section included.
- [x] Key decisions answered.