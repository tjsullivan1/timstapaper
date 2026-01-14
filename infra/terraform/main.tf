locals {
  env      = "dev"
  rg_name  = "rg-${var.project_name}-${local.env}"
  asp_name = "asp-${var.project_name}-${local.env}"
  app_name = "app-${var.project_name}-${local.env}"
}


resource "azurerm_resource_group" "rg" {
  name     = local.rg_name
  location = var.location
  tags     = { env = local.env, project = var.project_name, owner = "tjsullivan1" }
}


# App Service Plan (Linux)
resource "azurerm_service_plan" "asp" {
  name                = local.asp_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  os_type             = "Linux"
  sku_name            = "B1"
}


# Web App for Containers pulling from ACR image
resource "azurerm_linux_web_app" "app" {
  name                = local.app_name
  location            = var.location
  resource_group_name = azurerm_resource_group.rg.name
  service_plan_id     = azurerm_service_plan.asp.id


  site_config {
    application_stack {
      docker_image_name = "${var.acr_name}.azurecr.io/${var.project_name}:latest"
    }
  }


  app_settings = {
    WEBSITES_PORT = "8080"
  }
}