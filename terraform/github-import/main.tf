terraform {
  required_version = ">= 1.9.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

resource "github_repository" "course_repo" {
  name        = var.repository_name
  description = var.repository_description
  visibility  = var.repository_visibility

  has_issues   = true
  has_wiki     = false
  has_projects = false

  delete_branch_on_merge = false
  auto_init              = false
  archive_on_destroy     = false
}