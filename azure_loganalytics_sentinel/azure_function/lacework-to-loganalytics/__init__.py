# Modules to support run the script
import datetime
import logging
import json
import requests
import datetime
import hashlib
import hmac
import base64
import re
import os
import azure.functions as func

# An example JSON object with a Lacework Event
json_data = [
{
    "event_title": "Compliance Changed",
    "event_link": "https://myLacework.lacework.net/ui/investigate/Event/120884?startTime=1565370000000&endTime=1565373600000",
    "lacework_account": "myLacework",
    "event_source": "AzureCompliance",
    "event_description":"Azure Account myLacework Pay-As-You-Go: Azure_CIS_2_1 Ensure that standard pricing tier is selected changed from compliant to non-compliant",
    "event_timestamp":"27 May 2021 17:00 GMT",
    "event_type": "Compliance",
    "event_id": "120884",
    "event_severity": "4",
    "rec_id": "Azure_CIS_2_1"
    }
]

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    # Define the application settings (environmental variables) for the Workspace ID, Workspace Key, <Data Source> API Key(s) or Token, URI, and/or Other variables. Reference:  https://docs.microsoft.com/azure/azure-functions/functions-reference-python 

    # The following variables are required by the Log Analytics Data Collector API functions below. Reference: https://docs.microsoft.com/azure/azure-monitor/platform/data-collector-api
    customer_id = os.environ['workspaceId'] 
    shared_key = os.environ['workspaceKey']
    log_type = os.environ['tableName']
    
    #see Lacework's webhook format in https://support.lacework.com/hc/en-us/articles/360034367393-Webhook
    logging.info("BODY received:")
    logging.debug(req.get_body())
    body = req.get_body()
    #body = json.dumps(req.get_body().decode())
    post_data(customer_id, shared_key, body, log_type)
    logging.info("Message was forwarded to Log Analytics workspace "+customer_id)

    #return
    return func.HttpResponse(
        json.dumps({
            'method': req.method,
            'url': req.url,
            'headers': dict(req.headers),
            'params': dict(req.params),
            'get_body': req.get_body().decode()
        })
    )
# https://medium.com/slalom-build/reading-and-writing-to-azure-log-analytics-c78461056862    
# Required Function to build the Authorization signature for the Azure Log Analytics Data Collector API. 
# References: https://docs.microsoft.com/azure/azure-monitor/platform/data-collector-api 
# and https://docs.microsoft.com/azure/azure-functions/functions-reference-python#environment-variables

def build_signature(customer_id, shared_key, date, content_length, method, content_type, resource):
    x_headers = 'x-ms-date:' + date
    string_to_hash = method + "\n" + str(content_length) + "\n" + content_type + "\n" + x_headers + "\n" + resource
    bytes_to_hash = bytes(string_to_hash, encoding="utf-8")  
    decoded_key = base64.b64decode(shared_key)
    encoded_hash = base64.b64encode(hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()).decode()
    authorization = "SharedKey {}:{}".format(customer_id,encoded_hash)
    return authorization

# Required Function to create and invoke an API POST request to the Azure Log Analytics Data Collector API. Reference: https://docs.microsoft.com/azure/azure-functions/functions-reference-python#environment-variables

def post_data(customer_id, shared_key, body, log_type):
    method = 'POST'
    content_type = 'application/json'
    resource = '/api/logs'
    rfc1123date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    content_length = len(body)
    signature = build_signature(customer_id, shared_key, rfc1123date, content_length, method, content_type, resource)
    #uri = logAnalyticsUri + resource + "?api-version=2016-04-01"
    uri = 'https://' + customer_id + '.ods.opinsights.azure.com' + resource + '?api-version=2016-04-01'

    headers = {
        'content-type': content_type,
        'Authorization': signature,
        'Log-Type': log_type,
        'x-ms-date': rfc1123date
    }
    try:
        response = requests.post(uri, data=body, headers=headers)
    except Exception as err:
        logging.error("Error during sending logs to Azure Sentinel: {}".format(err))
    else:
        if (response.status_code >= 200 and response.status_code <= 299):
            logging.info("logs have been successfully sent to Azure Sentinel.")
        else:
            logging.error("Error during sending logs to Azure Sentinel. Response code: {}".format(response.status_code))

