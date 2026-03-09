output "vm_public_ip" {
  description = "Public IPv4 address of lab VM"
  value       = yandex_vpc_address.lab04.external_ipv4_address[0].address
}

output "vm_internal_ip" {
  description = "Private IPv4 address of lab VM"
  value       = yandex_compute_instance.lab04.network_interface[0].ip_address
}

output "ssh_command" {
  description = "SSH command to connect to VM"
  value       = "ssh ${var.ssh_user}@${yandex_vpc_address.lab04.external_ipv4_address[0].address}"
}

output "instance_id" {
  description = "Yandex Compute instance id"
  value       = yandex_compute_instance.lab04.id
}