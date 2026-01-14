# Best Practices

## Testing New Terraform Modules:
- should be able to run and test locally without the need for remote state store
- testing in remote environments should wrap with Terragrunt and use remote state store (e.g. Azurerm Backend for Terraform)
  - Allows the values for provider to be created by Terragrunt dynamically
  - Environment values should be passed in by CI/CD runners (e.g. Prefer GitHub Actions Environment Secrets)
  - Should be automated, testable and auditable
- should be created in the directory %project_root%/catalog/terraform_modules/%module_name%