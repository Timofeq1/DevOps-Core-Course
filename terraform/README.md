# Terraform task setup (Yandex Cloud)

## 1) Prepare variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

## 2) Run terraform workflow

```bash
terraform init
terraform fmt -recursive
terraform validate
terraform plan -out tfplan
terraform apply tfplan
terraform output
```

## 3) Verify SSH

```bash
ssh $(terraform output -raw ssh_command | sed 's/^ssh //')
```

## 4) Cleanup after Task 2 switch

```bash
terraform destroy
```