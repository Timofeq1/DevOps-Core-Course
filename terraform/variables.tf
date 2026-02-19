variable "yc_token" {
  description = "Yandex Cloud IAM token"
  type        = string
  sensitive   = true
}

variable "yc_cloud_id" {
  description = "Yandex Cloud cloud_id"
  type        = string
}

variable "yc_folder_id" {
  description = "Yandex Cloud folder_id"
  type        = string
}

variable "zone" {
  description = "Yandex Cloud zone"
  type        = string
  default     = "ru-central1-a"
}

variable "subnet_cidr" {
  description = "CIDR for the lab subnet"
  type        = string
  default     = "10.10.0.0/24"
}

variable "ssh_user" {
  description = "Linux username for SSH login"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key file"
  type        = string
}

variable "image_family" {
  description = "Image family for VM"
  type        = string
  default     = "ubuntu-2204-lts"
}

variable "vm_cores" {
  description = "Number of VM cores"
  type        = number
  default     = 2
}

variable "vm_memory_gb" {
  description = "VM RAM in GB"
  type        = number
  default     = 1
}

variable "vm_core_fraction" {
  description = "CPU guaranteed performance percent"
  type        = number
  default     = 20
}

variable "boot_disk_size_gb" {
  description = "Boot disk size in GB"
  type        = number
  default     = 10
}

variable "boot_disk_type" {
  description = "Boot disk type"
  type        = string
  default     = "network-hdd"
}

variable "project_name" {
  description = "Project name tag"
  type        = string
  default     = "devops-lab04"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "lab"
}

variable "owner" {
  description = "Owner tag"
  type        = string
  default     = "student"
}