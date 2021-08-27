
resource "azurerm_resource_group" "func-rg" {
  name     = var.RESOURCE_GROUP
  location = var.LOCATION
}

resource "random_string" "random" {
  length  = 4
  special = false
  lower   = true
  upper   = false
}

resource "azurerm_storage_account" "func_storage_acc" {
  name                     = "functacc${random_string.random.result}"
  resource_group_name      = var.RESOURCE_GROUP
  location                 = var.LOCATION
  account_tier             = "Standard"
  account_replication_type = "LRS"

  depends_on = [azurerm_resource_group.func-rg]
}

resource "azurerm_storage_container" "func_storage_container" {
  name                  = "func-deployments"
  storage_account_name  = azurerm_storage_account.func_storage_acc.name
  container_access_type = "private"

  depends_on = [azurerm_resource_group.func-rg]
}


module "func" {
  source                    = "./modules/func"
  LOCATION                  = var.LOCATION
  RESOURCE_GROUP            = var.RESOURCE_GROUP
  STORAGE_ACC_NAME          = azurerm_storage_account.func_storage_acc.name
  STORAGE_ACC_KEY           = azurerm_storage_account.func_storage_acc.primary_access_key
  STORAGE_CONNECTION_STRING = azurerm_storage_account.func_storage_acc.primary_blob_connection_string
  LOG_WORKSPACE_ID          = var.LOG_WORKSPACE_ID
  LOG_WORKSPACE_KEY         = var.LOG_WORKSPACE_KEY
  LOG_WORKSPACE_TABLE       = var.LOG_WORKSPACE_TABLE
  depends_on = [azurerm_resource_group.func-rg]
}

# resource "null_resource" "lacework-webhook" {
#   provisioner "local-exec" {
#     command = "cd ../azure_function && func azure functionapp publish ${module.outputs.function-app-name.value}"
#   }
# }
output "function-app-name" {
  value = module.func.function-app-name
  description = "Deploy the code using the following command: cd ../azure_function && func azure functionapp publish <function app name>"
}