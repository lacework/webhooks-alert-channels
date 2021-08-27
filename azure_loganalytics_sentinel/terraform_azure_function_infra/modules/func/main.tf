# Example in https://itnext.io/introduction-to-azure-functions-using-terraform-eca009ddf437

### INPUT VARs ###
variable "LOCATION" {}
variable "RESOURCE_GROUP" {}
variable "STORAGE_ACC_NAME" {}
variable "STORAGE_ACC_KEY" {}
variable "STORAGE_CONNECTION_STRING" {}
variable "LOG_WORKSPACE_ID" {}
variable "LOG_WORKSPACE_KEY" {}
variable "LOG_WORKSPACE_TABLE" {} 

data "azurerm_resource_group" "lacework-functions-rg" {
  name     = var.RESOURCE_GROUP
}

resource "azurerm_application_insights" "func_application_insights" {
  name                = "func-application-insights"
  location            = var.LOCATION
  resource_group_name = var.RESOURCE_GROUP
  application_type    = "other"
}

resource "azurerm_app_service_plan" "func_app_service_plan" {
  name                = "func-app-service-plan"
  location            = var.LOCATION
  resource_group_name = var.RESOURCE_GROUP
  kind                = "FunctionApp"
  reserved = true
  sku {
    tier = "Dynamic"
    size = "Y1"
  }
}

resource "azurerm_function_app" "func_function_app" {
  name                = "function-app-${var.STORAGE_ACC_NAME}"
  location            = var.LOCATION
  resource_group_name = var.RESOURCE_GROUP
  app_service_plan_id = azurerm_app_service_plan.func_app_service_plan.id
  app_settings = {
    FUNCTIONS_WORKER_RUNTIME = "python",
    AzureWebJobsStorage = var.STORAGE_CONNECTION_STRING,
    APPINSIGHTS_INSTRUMENTATIONKEY = azurerm_application_insights.func_application_insights.instrumentation_key,
    workspaceId  = var.LOG_WORKSPACE_ID,
    workspaceKey = var.LOG_WORKSPACE_KEY,
    tableName    = var.LOG_WORKSPACE_TABLE
  }

  os_type                    = "linux"
  storage_account_name       = var.STORAGE_ACC_NAME
  storage_account_access_key = var.STORAGE_ACC_KEY
  version                    = "~3"

  lifecycle {
    ignore_changes = [
      app_settings["WEBSITE_RUN_FROM_PACKAGE"]
    ]
  }
}

output "function-app-name" {
  value = resource.azurerm_function_app.func_function_app.name
  description = "Deploy the code using the following command: cd ../azure_function && func azure functionapp publish <function app name>"
}