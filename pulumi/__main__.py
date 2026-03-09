from pathlib import Path

import pulumi
import pulumi_yandex as yandex

config = pulumi.Config()

zone = config.get("zone") or "ru-central1-a"
subnet_cidr = config.get("subnetCidr") or "10.10.0.0/24"
ssh_user = config.get("sshUser") or "ubuntu"
ssh_public_key_path = config.require("sshPublicKeyPath")
image_id = config.require("imageId")

ssh_public_key = Path(ssh_public_key_path).expanduser().read_text(encoding="utf-8").strip()

network = yandex.VpcNetwork(
    "lab04-network",
    name="devops-lab04-network",
    labels={"project": "devops-lab04", "env": "lab", "tool": "pulumi"},
)

subnet = yandex.VpcSubnet(
    "lab04-subnet",
    name="devops-lab04-subnet",
    zone=zone,
    network_id=network.id,
    v4_cidr_blocks=[subnet_cidr],
)

security_group = yandex.VpcSecurityGroup(
    "lab04-sg",
    name="devops-lab04-sg",
    network_id=network.id,
    ingresses=[
        {
            "description": "HTTP",
            "protocol": "TCP",
            "port": 80,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
        {
            "description": "App port",
            "protocol": "TCP",
            "port": 5000,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egresses=[
        {
            "description": "Allow all outbound",
            "protocol": "ANY",
            "from_port": 0,
            "to_port": 65535,
            "v4_cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)

public_ip = yandex.VpcAddress(
    "lab04-public-ip",
    name="devops-lab04-public-ip",
    external_ipv4_address={"zone_id": zone},
)

instance = yandex.ComputeInstance(
    "lab04-vm",
    name="devops-lab04-vm",
    zone=zone,
    platform_id="standard-v2",
    resources={"cores": 2, "memory": 1, "core_fraction": 20},
    boot_disk={
        "initialize_params": {
            "image_id": image_id,
            "size": 10,
            "type": "network-hdd",
        }
    },
    network_interfaces=[
        {
            "subnet_id": subnet.id,
            "nat": True,
            "nat_ip_address": public_ip.external_ipv4_address.apply(lambda ip: ip["address"]),
            "security_group_ids": [security_group.id],
        }
    ],
    metadata={"ssh-keys": f"{ssh_user}:{ssh_public_key}"},
    labels={"project": "devops-lab04", "env": "lab", "owner": "timofey", "tool": "pulumi"},
)

vm_public_ip = instance.network_interfaces.apply(
    lambda interfaces: interfaces[0].get("nat_ip_address") if interfaces else None
)
vm_private_ip = instance.network_interfaces.apply(
    lambda interfaces: interfaces[0].get("ip_address") if interfaces else None
)

pulumi.export("vm_public_ip", vm_public_ip)
pulumi.export("vm_private_ip", vm_private_ip)
pulumi.export("ssh_command", pulumi.Output.concat("ssh ", ssh_user, "@", vm_public_ip))