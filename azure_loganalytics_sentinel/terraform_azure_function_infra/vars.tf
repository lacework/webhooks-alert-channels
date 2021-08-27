variable "SUBSCRIPTION_ID" {}
variable "TENANT_ID" {}

# GLOBAL VARIABLES
variable "RESOURCE_GROUP" {
  default = "lacework-functions-rg"
}
variable "LOCATION" {
  default = "East US"
}
variable "LOG_WORKSPACE_ID" {}
variable "LOG_WORKSPACE_KEY" {}
variable "LOG_WORKSPACE_TABLE" {
  default = "LaceworkEvents"
}