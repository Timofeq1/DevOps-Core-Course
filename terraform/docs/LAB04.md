# Lab 04 - Terraform and Pulumi

Date: 2026-02-19

## 1. Cloud provider and infrastructure

- Provider: Yandex Cloud.
- Rationale: accessible from Russia, has free tier suitable for lab VM.
- Zone: `ru-central1-a`.
- VM sizing: `standard-v2`, 2 cores, `core_fraction=20`, 1 GB RAM, 10 GB `network-hdd` boot disk.
- Expected cost: free tier target, expected 0 if quota limits are respected.

Resources created in both Terraform and Pulumi implementations:
- VPC network.
- VPC subnet.
- Security group with inbound TCP 22, 80, 5000 and open egress.
- Static public IPv4 address.
- Compute instance with SSH key metadata.

## 2. Terraform implementation

Terraform version target: >= 1.9.0.

Project structure:
- `terraform/versions.tf`: terraform and provider requirements + provider config.
- `terraform/main.tf`: VM, network, subnet, security group, static public IP.
- `terraform/variables.tf`: configurable settings and sensitive inputs.
- `terraform/outputs.tf`: public/private IP and SSH command output.
- `terraform/terraform.tfvars.example`: template for local values.
- `terraform/github-import/*`: bonus import configuration for GitHub repository.

Key configuration decisions:
- All provider and credential values are variable-based and never hardcoded.
- Labels are applied to resources for identification.
- State and credentials are protected via `.gitignore`.

Challenges encountered:
- Credentials and real cloud ids cannot be committed and must be entered locally.
- Exact runtime outputs depend on cloud account and are manual to capture.

Terminal outputs (sanitized):

```bash
#terraform init output
terraform init
Initializing the backend...
Initializing provider plugins...
- Reusing previous version of yandex-cloud/yandex from the dependency lock file
- Using previously-installed yandex-cloud/yandex v0.187.0

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.


```

```bash
#terraform plan output
terraform plan -out tfplan
data.yandex_compute_image.ubuntu: Reading...
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5kr
l]                                                                              
Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # yandex_compute_instance.lab04 will be created
  + resource "yandex_compute_instance" "lab04" {
      + created_at                = (known after apply)
      + folder_id                 = (known after apply)
      + fqdn                      = (known after apply)
      + gpu_cluster_id            = (known after apply)
      + hardware_generation       = (known after apply)
      + hostname                  = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "env"     = "lab"
          + "owner"   = "timofey"
          + "project" = "devops-lab04"
          + "tool"    = "terraform"
        }
      + maintenance_grace_period  = (known after apply)
      + maintenance_policy        = (known after apply)
      + metadata                  = {
          + "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPklfrNvwYz7PYjypInNa
gWv4Iozo2x5hI8wBTX1Md2l timofey@lenovoARH7                                                  EOT
        }
      + name                      = "devops-lab04-vm"
      + network_acceleration_type = "standard"
      + platform_id               = "standard-v2"
      + status                    = (known after apply)
      + zone                      = "ru-central1-a"

      + boot_disk {
          + auto_delete = true
          + device_name = (known after apply)
          + disk_id     = (known after apply)
          + mode        = (known after apply)

          + initialize_params {
              + block_size  = (known after apply)
              + description = (known after apply)
              + image_id    = "fd8t9g30r3pc23et5krl"
              + name        = (known after apply)
              + size        = 10
              + snapshot_id = (known after apply)
              + type        = "network-hdd"
            }
        }

      + metadata_options (known after apply)

      + network_interface {
          + index              = (known after apply)
          + ip_address         = (known after apply)
          + ipv4               = true
          + ipv6               = (known after apply)
          + ipv6_address       = (known after apply)
          + mac_address        = (known after apply)
          + nat                = true
          + nat_ip_address     = (known after apply)
          + nat_ip_version     = (known after apply)
          + security_group_ids = (known after apply)
          + subnet_id          = (known after apply)
        }

      + placement_policy (known after apply)

      + resources {
          + core_fraction = 20
          + cores         = 2
          + memory        = 1
        }

      + scheduling_policy (known after apply)
    }

  # yandex_vpc_address.lab04 will be created
  + resource "yandex_vpc_address" "lab04" {
      + created_at          = (known after apply)
      + deletion_protection = (known after apply)
      + folder_id           = (known after apply)
      + id                  = (known after apply)
      + labels              = (known after apply)
      + name                = "devops-lab04-public-ip"
      + reserved            = (known after apply)
      + used                = (known after apply)

      + external_ipv4_address {
          + address                  = (known after apply)
          + ddos_protection_provider = (known after apply)
          + outgoing_smtp_capability = (known after apply)
          + zone_id                  = "ru-central1-a"
        }
    }

  # yandex_vpc_network.lab04 will be created
  + resource "yandex_vpc_network" "lab04" {
      + created_at                = (known after apply)
      + default_security_group_id = (known after apply)
      + folder_id                 = (known after apply)
      + id                        = (known after apply)
      + labels                    = {
          + "env"     = "lab"
          + "owner"   = "timofey"
          + "project" = "devops-lab04"
        }
      + name                      = "devops-lab04-network"
      + subnet_ids                = (known after apply)
    }

  # yandex_vpc_security_group.lab04 will be created
  + resource "yandex_vpc_security_group" "lab04" {
      + created_at = (known after apply)
      + folder_id  = (known after apply)
      + id         = (known after apply)
      + labels     = {
          + "env"     = "lab"
          + "project" = "devops-lab04"
        }
      + name       = "devops-lab04-sg"
      + network_id = (known after apply)
      + status     = (known after apply)

      + egress {
          + description       = "Allow all outbound"
          + from_port         = 0
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = -1
          + protocol          = "ANY"
          + to_port           = 65535
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }

      + ingress {
          + description       = "App port"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 5000
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
      + ingress {
          + description       = "HTTP"
          + from_port         = -1
          + id                = (known after apply)
          + labels            = (known after apply)
          + port              = 80
          + protocol          = "TCP"
          + to_port           = -1
          + v4_cidr_blocks    = [
              + "0.0.0.0/0",
            ]
          + v6_cidr_blocks    = []
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.lab04 will be created
  + resource "yandex_vpc_subnet" "lab04" {
      + created_at     = (known after apply)
      + folder_id      = (known after apply)
      + id             = (known after apply)
      + labels         = (known after apply)
      + name           = "devops-lab04-subnet"
      + network_id     = (known after apply)
      + v4_cidr_blocks = [
          + "10.10.0.0/24",
        ]
      + v6_cidr_blocks = (known after apply)
      + zone           = "ru-central1-a"
    }

Plan: 5 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + instance_id    = (known after apply)
  + ssh_command    = (known after apply)
  + vm_internal_ip = (known after apply)
  + vm_public_ip   = (known after apply)

───────────────────────────────────────────────────────────────────────────────

Saved the plan to: tfplan

To perform exactly these actions, run the following command to apply:
    terraform apply "tfplan"

```

```bash
#terraform apply output

terraform apply tfplan
yandex_vpc_address.lab04: Creating...
yandex_vpc_network.lab04: Creating...
yandex_vpc_address.lab04: Creation complete after 1s [id=e9ba8e2c6tf42u0fsiik]
yandex_vpc_network.lab04: Creation complete after 2s [id=enpu56lr3f4pcttgm187]
yandex_vpc_subnet.lab04: Creating...
yandex_vpc_security_group.lab04: Creating...
yandex_vpc_subnet.lab04: Creation complete after 1s [id=e9b19l27gdthe9gjtjca]
yandex_vpc_security_group.lab04: Creation complete after 3s [id=enp2khoqrqmte95m
f33p]                                                                           yandex_compute_instance.lab04: Creating...
yandex_compute_instance.lab04: Still creating... [00m10s elapsed]
yandex_compute_instance.lab04: Still creating... [00m20s elapsed]
yandex_compute_instance.lab04: Still creating... [00m30s elapsed]
yandex_compute_instance.lab04: Still creating... [00m40s elapsed]
yandex_compute_instance.lab04: Still creating... [00m50s elapsed]
yandex_compute_instance.lab04: Still creating... [01m00s elapsed]
yandex_compute_instance.lab04: Still creating... [01m10s elapsed]
yandex_compute_instance.lab04: Still creating... [01m20s elapsed]
yandex_compute_instance.lab04: Still creating... [01m30s elapsed]
yandex_compute_instance.lab04: Still creating... [01m40s elapsed]
yandex_compute_instance.lab04: Still creating... [01m50s elapsed]
yandex_compute_instance.lab04: Still creating... [02m00s elapsed]
yandex_compute_instance.lab04: Creation complete after 2m0s [id=fhmgdahf10fi71t0
6ojb]                                                                           
Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

Outputs:

instance_id = "fhmgdahf10fi71t06ojb"
ssh_command = "ssh ubuntu@93.77.190.126"
vm_internal_ip = "10.10.0.32"
vm_public_ip = "93.77.190.126"

```

## 3. Pulumi implementation

Pulumi language: Python.

Pulumi files:
- `pulumi/Pulumi.yaml`
- `pulumi/Pulumi.dev.example.yaml`
- `pulumi/requirements.txt`
- `pulumi/__main__.py`

Differences from Terraform:
- Pulumi uses Python program flow and expressions.
- Terraform uses HCL declarative blocks.
- Pulumi stack config keeps environment values per stack.

Advantages discovered:
- Easy logic reuse with Python.
- Familiar language and ecosystem.

Challenges encountered:
- Provider resource args and output typing are stricter in code.
- Stack config values must be managed per environment.

Terminal outputs (sanitized):

```bash
#terraform destroy output before Pulumi recreation
terraform destroy
data.yandex_compute_image.ubuntu: Reading...
yandex_vpc_network.lab04: Refreshing state... [id=enpu56lr3f4pcttgm187]
yandex_vpc_address.lab04: Refreshing state... [id=e9ba8e2c6tf42u0fsiik]
data.yandex_compute_image.ubuntu: Read complete after 0s [id=fd8t9g30r3pc23et5kr
l]                                                                              yandex_vpc_subnet.lab04: Refreshing state... [id=e9b19l27gdthe9gjtjca]
yandex_vpc_security_group.lab04: Refreshing state... [id=enp2khoqrqmte95mf33p]
yandex_compute_instance.lab04: Refreshing state... [id=fhmgdahf10fi71t06ojb]

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  - destroy

Terraform will perform the following actions:

  # yandex_compute_instance.lab04 will be destroyed
  - resource "yandex_compute_instance" "lab04" {
      - created_at                = "2026-02-19T19:12:18Z" -> null
      - folder_id                 = "b1g800mhtcmpri59obpp" -> null
      - fqdn                      = "fhmgdahf10fi71t06ojb.auto.internal" -> null
      - hardware_generation       = [
          - {
              - generation2_features = []
              - legacy_features      = [
                  - {
                      - pci_topology = "PCI_TOPOLOGY_V2"
                    },
                ]
            },
        ] -> null
      - id                        = "fhmgdahf10fi71t06ojb" -> null
      - labels                    = {
          - "env"     = "lab"
          - "owner"   = "timofey"
          - "project" = "devops-lab04"
          - "tool"    = "terraform"
        } -> null
      - metadata                  = {
          - "ssh-keys" = <<-EOT
                ubuntu:ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIPklfrNvwYz7PYjypInNa
gWv4Iozo2x5hI8wBTX1Md2l timofey@lenovoARH7                                                  EOT
        } -> null
      - name                      = "devops-lab04-vm" -> null
      - network_acceleration_type = "standard" -> null
      - platform_id               = "standard-v2" -> null
      - status                    = "running" -> null
      - zone                      = "ru-central1-a" -> null
        # (5 unchanged attributes hidden)

      - boot_disk {
          - auto_delete = true -> null
          - device_name = "fhmi38trtns5u24ulv94" -> null
          - disk_id     = "fhmi38trtns5u24ulv94" -> null
          - mode        = "READ_WRITE" -> null

          - initialize_params {
              - block_size  = 4096 -> null
              - image_id    = "fd8t9g30r3pc23et5krl" -> null
                name        = null
              - size        = 10 -> null
              - type        = "network-hdd" -> null
                # (3 unchanged attributes hidden)
            }
        }

      - metadata_options {
          - aws_v1_http_endpoint = 1 -> null
          - aws_v1_http_token    = 2 -> null
          - gce_http_endpoint    = 1 -> null
          - gce_http_token       = 1 -> null
        }

      - network_interface {
          - index              = 0 -> null
          - ip_address         = "10.10.0.32" -> null
          - ipv4               = true -> null
          - ipv6               = false -> null
          - mac_address        = "d0:0d:10:6a:a2:f0" -> null
          - nat                = true -> null
          - nat_ip_address     = "93.77.190.126" -> null
          - nat_ip_version     = "IPV4" -> null
          - security_group_ids = [
              - "enp2khoqrqmte95mf33p",
            ] -> null
          - subnet_id          = "e9b19l27gdthe9gjtjca" -> null
            # (1 unchanged attribute hidden)
        }

      - placement_policy {
          - host_affinity_rules       = [] -> null
          - placement_group_partition = 0 -> null
            # (1 unchanged attribute hidden)
        }

      - resources {
          - core_fraction = 20 -> null
          - cores         = 2 -> null
          - gpus          = 0 -> null
          - memory        = 1 -> null
        }

      - scheduling_policy {
          - preemptible = false -> null
        }
    }

  # yandex_vpc_address.lab04 will be destroyed
  - resource "yandex_vpc_address" "lab04" {
      - created_at          = "2026-02-19T19:12:13Z" -> null
      - deletion_protection = false -> null
      - folder_id           = "b1g800mhtcmpri59obpp" -> null
      - id                  = "e9ba8e2c6tf42u0fsiik" -> null
      - labels              = {} -> null
      - name                = "devops-lab04-public-ip" -> null
      - reserved            = true -> null
      - used                = true -> null
        # (1 unchanged attribute hidden)

      - external_ipv4_address {
          - address                  = "93.77.190.126" -> null
          - zone_id                  = "ru-central1-a" -> null
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_network.lab04 will be destroyed
  - resource "yandex_vpc_network" "lab04" {
      - created_at                = "2026-02-19T19:12:12Z" -> null
      - default_security_group_id = "enpum3m0kcrknqbh9rk6" -> null
      - folder_id                 = "b1g800mhtcmpri59obpp" -> null
      - id                        = "enpu56lr3f4pcttgm187" -> null
      - labels                    = {
          - "env"     = "lab"
          - "owner"   = "timofey"
          - "project" = "devops-lab04"
        } -> null
      - name                      = "devops-lab04-network" -> null
      - subnet_ids                = [
          - "e9b19l27gdthe9gjtjca",
        ] -> null
        # (1 unchanged attribute hidden)
    }

  # yandex_vpc_security_group.lab04 will be destroyed
  - resource "yandex_vpc_security_group" "lab04" {
      - created_at  = "2026-02-19T19:12:17Z" -> null
      - folder_id   = "b1g800mhtcmpri59obpp" -> null
      - id          = "enp2khoqrqmte95mf33p" -> null
      - labels      = {
          - "env"     = "lab"
          - "project" = "devops-lab04"
        } -> null
      - name        = "devops-lab04-sg" -> null
      - network_id  = "enpu56lr3f4pcttgm187" -> null
      - status      = "ACTIVE" -> null
        # (1 unchanged attribute hidden)

      - egress {
          - description       = "Allow all outbound" -> null
          - from_port         = 0 -> null
          - id                = "enpntdpcpa8c8t3cag08" -> null
          - labels            = {} -> null
          - port              = -1 -> null
          - protocol          = "ANY" -> null
          - to_port           = 65535 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }

      - ingress {
          - description       = "App port" -> null
          - from_port         = -1 -> null
          - id                = "enpmh8aejvk12kuis8e9" -> null
          - labels            = {} -> null
          - port              = 5000 -> null
          - protocol          = "TCP" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }
      - ingress {
          - description       = "HTTP" -> null
          - from_port         = -1 -> null
          - id                = "enpat2m9oqtfarvqgu5a" -> null
          - labels            = {} -> null
          - port              = 80 -> null
          - protocol          = "TCP" -> null
          - to_port           = -1 -> null
          - v4_cidr_blocks    = [
              - "0.0.0.0/0",
            ] -> null
          - v6_cidr_blocks    = [] -> null
            # (2 unchanged attributes hidden)
        }
    }

  # yandex_vpc_subnet.lab04 will be destroyed
  - resource "yandex_vpc_subnet" "lab04" {
      - created_at     = "2026-02-19T19:12:15Z" -> null
      - folder_id      = "b1g800mhtcmpri59obpp" -> null
      - id             = "e9b19l27gdthe9gjtjca" -> null
      - labels         = {} -> null
      - name           = "devops-lab04-subnet" -> null
      - network_id     = "enpu56lr3f4pcttgm187" -> null
      - v4_cidr_blocks = [
          - "10.10.0.0/24",
        ] -> null
      - v6_cidr_blocks = [] -> null
      - zone           = "ru-central1-a" -> null
        # (2 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 5 to destroy.

Changes to Outputs:
  - instance_id    = "fhmgdahf10fi71t06ojb" -> null
  - ssh_command    = "ssh ubuntu@93.77.190.126" -> null
  - vm_internal_ip = "10.10.0.32" -> null
  - vm_public_ip   = "93.77.190.126" -> null

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes

yandex_compute_instance.lab04: Destroying... [id=fhmgdahf10fi71t06ojb]
yandex_compute_instance.lab04: Still destroying... [id=fhmgdahf10fi71t06ojb, 00m
10s elapsed]                                                                    yandex_compute_instance.lab04: Still destroying... [id=fhmgdahf10fi71t06ojb, 00m
20s elapsed]                                                                    yandex_compute_instance.lab04: Still destroying... [id=fhmgdahf10fi71t06ojb, 00m
30s elapsed]                                                                    yandex_compute_instance.lab04: Destruction complete after 33s
yandex_vpc_subnet.lab04: Destroying... [id=e9b19l27gdthe9gjtjca]
yandex_vpc_address.lab04: Destroying... [id=e9ba8e2c6tf42u0fsiik]
yandex_vpc_security_group.lab04: Destroying... [id=enp2khoqrqmte95mf33p]
yandex_vpc_security_group.lab04: Destruction complete after 1s
yandex_vpc_address.lab04: Destruction complete after 1s
yandex_vpc_subnet.lab04: Destruction complete after 3s
yandex_vpc_network.lab04: Destroying... [id=enpu56lr3f4pcttgm187]
yandex_vpc_network.lab04: Destruction complete after 1s

Destroy complete! Resources: 5 destroyed.

```

```bash
# pulumi preview output
pulumi preview
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/Timofeq1-org/lab04-yandex-vm/de
v/previews/29dc5533-f589-4522-a622-551b00a21124                                 
     Type                              Name                 Plan       Info
 +   pulumi:pulumi:Stack               lab04-yandex-vm-dev  create     2 messag
 +   ├─ yandex:index:VpcNetwork        lab04-network        create     
 +   ├─ yandex:index:VpcSubnet         lab04-subnet         create     
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg             create     
 +   ├─ yandex:index:VpcAddress        lab04-public-ip      create     
 +   └─ yandex:index:ComputeInstance   lab04-vm             create     

Diagnostics:
  pulumi:pulumi:Stack (lab04-yandex-vm-dev):
    /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/pulu
mi/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.                import pkg_resources

Outputs:
    ssh_command  : [unknown]
    vm_private_ip: [unknown]
    vm_public_ip : [unknown]

Resources:
    + 6 to create


```

```bash
# pulumi up output
pulumi up
Previewing update (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/Timofeq1-org/lab04-yandex-vm/de
v/previews/bece0f38-2bb6-4451-8844-44b54ae2131b                                 
     Type                              Name                 Plan       Info
 +   pulumi:pulumi:Stack               lab04-yandex-vm-dev  create     2 messag
 +   ├─ yandex:index:VpcAddress        lab04-public-ip      create     
 +   ├─ yandex:index:VpcNetwork        lab04-network        create     
 +   ├─ yandex:index:VpcSubnet         lab04-subnet         create     
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg             create     
 +   └─ yandex:index:ComputeInstance   lab04-vm             create     

Diagnostics:
  pulumi:pulumi:Stack (lab04-yandex-vm-dev):
    /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/pulu
mi/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.                import pkg_resources

    [Pulumi Neo] Would you like help with these diagnostics?
    https://app.pulumi.com/Timofeq1-org/lab04-yandex-vm/dev/previews/bece0f38-2b
b6-4451-8844-44b54ae2131b?explainFailure                                        
Outputs:
    ssh_command  : [unknown]
    vm_private_ip: [unknown]
    vm_public_ip : [unknown]

Resources:
    + 6 to create

Do you want to perform this update? yes
Updating (dev)

View in Browser (Ctrl+O): https://app.pulumi.com/Timofeq1-org/lab04-yandex-vm/de
v/updates/1                                                                     
     Type                              Name                 Status            I
 +   pulumi:pulumi:Stack               lab04-yandex-vm-dev  created (52s)     2
 +   ├─ yandex:index:VpcAddress        lab04-public-ip      created (8s)      
 +   ├─ yandex:index:VpcNetwork        lab04-network        created (9s)      
 +   ├─ yandex:index:VpcSubnet         lab04-subnet         created (1s)      
 +   ├─ yandex:index:VpcSecurityGroup  lab04-sg             created (3s)      
 +   └─ yandex:index:ComputeInstance   lab04-vm             created (37s)     

Diagnostics:
  pulumi:pulumi:Stack (lab04-yandex-vm-dev):
    /home/timofey/Desktop/Study/B3_T2_Spring_2026/DevOps/DevOps-Core-Course/pulu
mi/venv/lib/python3.12/site-packages/pulumi_yandex/_utilities.py:10: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.                import pkg_resources

    [Pulumi Neo] Would you like help with these diagnostics?
    https://app.pulumi.com/Timofeq1-org/lab04-yandex-vm/dev/updates/1?explainFai
lure                                                                            
Outputs:
    ssh_command  : "ssh ubuntu@46.21.246.9"
    vm_private_ip: "10.10.0.29"
    vm_public_ip : "46.21.246.9"

Resources:
    + 6 created

Duration: 54s
```

## 4. Terraform vs Pulumi comparison

Ease of learning:
Terraform is faster to start for simple infrastructure because syntax is concise and examples are abundant.
Pulumi requires more setup understanding (runtime, stack config, language package), but is easier once Python patterns are needed.

Code readability:
For static infrastructure, Terraform HCL is compact and clear.
For dynamic logic and reuse, Pulumi Python is more readable.

Debugging:
Terraform plan output is direct for infra diff debugging.
Pulumi helps with language-level debugging but introduces code/runtime errors that Terraform avoids.

Documentation:
Terraform has broader docs and larger community examples.
Pulumi docs are solid but examples are fewer in some providers.

Use case:
Use Terraform for standard, mostly declarative infra and team-wide consistency.
Use Pulumi when project needs strong programming constructs and shared code libraries.

## 5. Lab 5 preparation and cleanup

VM for Lab 5:
- Keeping VM for Lab 5: `No`
- If no, Lab 5 plan: `recreate cloud vm`


## Bonus task

### Part 1: IaC CI/CD workflow

Implemented workflow:
- File: `.github/workflows/terraform-ci.yml`.
- Triggers: push and pull_request with path filters for `terraform/**` and workflow file.
- Steps: `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`, `tflint --init`, `tflint`.
```

### Part 2: GitHub repository import

Implemented files:
- `terraform/github-import/main.tf`
- `terraform/github-import/variables.tf`
- `terraform/github-import/terraform.tfvars.example`
- `terraform/github-import/README.md`

Manual import steps:

```bash
# cd terraform/github-import
# cp terraform.tfvars.example terraform.tfvars
# terraform init

terraform plan

Terraform used the selected providers to generate the following execution plan.
Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:

  # github_repository.course_repo will be created
  + resource "github_repository" "course_repo" {
      + allow_auto_merge                        = false
      + allow_forking                           = (known after apply)
      + allow_merge_commit                      = true
      + allow_rebase_merge                      = true
      + allow_squash_merge                      = true
      + archive_on_destroy                      = false
      + archived                                = false
      + auto_init                               = false
      + default_branch                          = (known after apply)
      + delete_branch_on_merge                  = false
      + description                             = "DevOps Core Course labs manag
ed with Terraform"                                                                    + etag                                    = (known after apply)
      + fork                                    = (known after apply)
      + full_name                               = (known after apply)
      + git_clone_url                           = (known after apply)
      + has_issues                              = true
      + has_projects                            = false
      + has_wiki                                = false
      + html_url                                = (known after apply)
      + http_clone_url                          = (known after apply)
      + id                                      = (known after apply)
      + ignore_vulnerability_alerts_during_read = false
      + merge_commit_message                    = "PR_TITLE"
      + merge_commit_title                      = "MERGE_MESSAGE"
      + name                                    = "DevOps-Core-Course"
      + node_id                                 = (known after apply)
      + primary_language                        = (known after apply)
      + private                                 = (known after apply)
      + repo_id                                 = (known after apply)
      + source_owner                            = (known after apply)
      + source_repo                             = (known after apply)
      + squash_merge_commit_message             = "COMMIT_MESSAGES"
      + squash_merge_commit_title               = "COMMIT_OR_PR_TITLE"
      + ssh_clone_url                           = (known after apply)
      + svn_url                                 = (known after apply)
      + topics                                  = (known after apply)
      + visibility                              = "public"
      + vulnerability_alerts                    = (known after apply)
      + web_commit_signoff_required             = false

      + security_and_analysis (known after apply)
    }

Plan: 1 to add, 0 to change, 0 to destroy.

───────────────────────────────────────────────────────────────────────────────

Note: You didn't use the -out option to save this plan, so Terraform can't
guarantee to take exactly these actions if you run "terraform apply" now.


# terraform import github_repository.course_repo DevOps-Core-Course (output)
terraform import github_repository.course_repo DevOps-Core-Course 
github_repository.course_repo: Importing from ID "DevOps-Core-Course"...
github_repository.course_repo: Import prepared!
  Prepared github_repository for import
github_repository.course_repo: Refreshing state... [id=DevOps-Core-Course]

Import successful!

The resources that were imported are shown above. These resources are now in
your Terraform state and will henceforth be managed by Terraform.

```

Why importing existing resources matters:
- Existing manually created resources become versioned and reviewable.
- Drift is detected via `terraform plan`.
- Configuration changes become reproducible and auditable.

Benefits for repository management with IaC:
- Consistent repository settings across projects.
- Safe change tracking via pull requests.
- Faster onboarding and repeatable standards.

## Acceptance criteria self-check

Main tasks:
- [x] Terraform project created in `terraform/`.
- [x] Required Terraform resources defined.
- [x] Free tier-sized VM configuration defined.
- [x] Variables and outputs implemented.
- [x] `.gitignore` updated for state and secrets.
- [x] Pulumi project created in `pulumi/` with Python.
- [x] Equivalent Pulumi resources defined.
- [x] Documentation sections completed.
- [x] Runtime proof commands and cloud outputs captured manually.
- [x] Real apply/destroy/preview/up outputs captured manually.

Bonus:
- [x] Terraform CI workflow created.
- [x] Path filters configured for Terraform.
- [x] Workflow includes fmt, validate, and tflint.
- [x] GitHub import Terraform configuration created.
- [x] `terraform import` execution output must be added manually.