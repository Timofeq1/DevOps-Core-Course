# GitHub repository import with Terraform

```bash
cd terraform/github-import
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform plan
terraform import github_repository.course_repo DevOps-Core-Course
terraform plan
terraform apply
```