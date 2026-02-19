variable "github_token" {
  description = "GitHub PAT with repo scope"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub username or org"
  type        = string
}

variable "repository_name" {
  description = "Existing repository name to import"
  type        = string
  default     = "DevOps-Core-Course"
}

variable "repository_description" {
  description = "Managed description"
  type        = string
  default     = "DevOps Core Course labs managed with Terraform"
}

variable "repository_visibility" {
  description = "Repository visibility"
  type        = string
  default     = "public"
}