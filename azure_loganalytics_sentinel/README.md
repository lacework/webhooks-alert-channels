# Webhook to Azure Log Analytics and Sentinel

This repo contains an Azure Function to be deployed in Azure as a serverless app using consumption plan (as we expect less than 1000 calls a day).
Deploying the terraform script will deploy the required resources and output the URL to be used in Lacework as the Alert Channel Webhook URL
The only inputs required are 
* Workspace ID
* Workspace key

Both will be stored as environment variables of the Azure Function execution environment (a consumption plan, as described in https://docs.microsoft.com/en-us/azure/azure-functions/consumption-plan)

## How to execute Terraform
First, Gather your log analytic's workspace ID and key following https://docs.microsoft.com/en-us/azure/azure-monitor/agents/log-analytics-agent#workspace-id-and-key
Now, create a func.tfvars

```
cd terraform_azure_function_infra
vi func.tfvars
```

Use the following syntax
```
SUBSCRIPTION_ID = "xxxxx"
TENANT_ID = "xxxx"
LOG_WORKSPACE_ID = "xxxxx"
LOG_WORKSPACE_KEY = "xxx"
```

Now execute terraform
```
terraform init 
terraform apply  -var-file=func.tfvars
```

Take the output and copy it, example 
```
Outputs:
function-app-name = "function-app-functacclc7f"
```

Now execute the Function App Code Review
```
cd ../azure_function && func azure functionapp publish function-app-functacclc7f
```