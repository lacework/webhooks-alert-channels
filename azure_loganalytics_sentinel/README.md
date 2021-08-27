# Webhook to Azure Log Analytics and Sentinel

This repo contains an Azure Function to be deployed in Azure as a serverless app using consumption plan (as we expect less than 1000 calls a day).
Deploying the terraform script will deploy the required resources and output the URL to be used in Lacework as the Alert Channel Webhook URL
The only inputs required are 
* Workspace ID
* Workspace key

Both will be stored as environment variables of the Azure Function execution environment (a consumption plan, as described in https://docs.microsoft.com/en-us/azure/azure-functions/consumption-plan)
