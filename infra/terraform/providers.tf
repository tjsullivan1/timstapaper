terraform {
  required_version = ">= 1.12.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 4.49.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = ">= 3.6.0"
    }
  }
}


provider "azurerm" {
  features {}
  use_oidc = true
}


provider "azuread" {
  tenant_id = var.tenant_id
}