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


    #########################################################################
    ## patch in LW calls here
    lacework_client = LaceworkClient(api_key=os.getenv("LW_API_KEY"),
                                    api_secret=os.getenv("LW_API_SECRET"),
                                    account=os.getenv("LW_ACCOUNT"))

    event_id = body["event_id"]
    event_details = get_event_details_for_id(lacework_client, event_id)
    merge_details_into_event_body(body, event_details)
    #########################################################################


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






def get_event_details_for_id(lacework_client, event_id):
    # Get event details for specified ID
    event_details = lacework_client.events.get_details(event_id)
    return event_details


## for demoing events generated by Polygraph on AWS CloudTrail
def demo_aws_anomaly_event(lacework_client):
    event_id = 131174

    ## This is an example webhook payload, prior to any additional decoration.
    body = {
        "event_title": "User used service in Region",
        "event_link": "https://customerdemo.lacework.net/ui/investigation/recents/EventDossier-131174",
        "lacework_account": "customerdemo",
        "event_source": "AWSCloudTrail",
        "event_description":"For account: 463783698038 ( tech-ally) : User IAMUser/463783698038:teresa.oreilly used api UntagResource for service kms.amazonaws.com in region us-west-2",
        "event_timestamp":"04 Apr 2022 16:00 GMT",
        "event_type": "Anomaly",
        "event_id": "131174",
        "event_severity": "4",
        "rec_id": ""
        }
    print (body)

    # call back to the LW API for more details
    event_details = get_event_details_for_id(lacework_client, event_id)

    # dive into the data
    entity_map = event_details["data"][0]["ENTITY_MAP"]
    # print (entity_map)

    # these are sections of this specific type of event data
    user_list = entity_map["CT_User"]
    region_list = entity_map["Region"]
    api_list = entity_map["API"]
    source_ip_address_list = entity_map["SourceIpAddress"]

    ## now we'll actually add some values to the payload, before shipping to Sentinel
    username = user_list[0]["USERNAME"]
    body["username"] = username

    region = region_list[0]["REGION"]
    body["region"] = region

    service = api_list[0]["SERVICE"]
    api = api_list[0]["API"]
    body["service"] = service
    body["api"] = api

    ip_address = source_ip_address_list[0]["IP_ADDRESS"]
    country = source_ip_address_list[0]["COUNTRY"]
    region = source_ip_address_list[0]["REGION"]

    body["ip_address"] = ip_address
    body["country"] = country
    body["region"] = region

    print ("")
    print ("-----------------------")
    print ("modified body: ")
    print ("")
    print (body)

    return body



## not yet built
def merge_details_into_event_body(body, event_details):
    return {}
    ##raise RuntimeError('function not yet ready')
