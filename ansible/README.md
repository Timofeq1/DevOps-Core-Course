# Ansible Automation

[![Ansible Deployment](https://github.com/Timofeq1/DevOps-Core-Course/actions/workflows/ansible-deploy.yml/badge.svg)](https://github.com/your-username/your-repo/actions/workflows/ansible-deploy.yml)

## Lab 6 Scope

- Role refactor with blocks, rescue, always, and tags (`common`, `docker`)
- Docker Compose based deployment role (`web_app`)
- Safe wipe flow (`web_app_wipe` variable + `web_app_wipe` tag)
- GitHub Actions deployment pipeline targeting a Yandex Cloud VM

## Quick Run

```bash
cd ansible
ansible-playbook playbooks/provision.yml
ansible-playbook playbooks/deploy.yml
ansible-playbook playbooks/deploy-monitoring.yml
```
