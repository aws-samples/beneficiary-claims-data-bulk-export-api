import requests
from requests.auth import HTTPBasicAuth
import json
import time
import boto3
import os
from datetime import datetime
from botocore.exceptions import ClientError
import logging
logging.basicConfig(   level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)
secret_name = os.environ['SECRET_NAME']
region = os.environ['REGION']
s3_bucket = os.environ['EXPORT_BUCKET']

def get_secret():
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region
    )
    try:
        get_secret_value_response = client.get_secret_value(
  SecretId=secret_name
        )
    except ClientError as e:
        raise e
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
    
def get_auth():
    secret = get_secret()
    client_id = secret['client_id']
    client_secret = secret['client_secret']
    url = 'https://sandbox.bcda.cms.gov/auth/token'
    auth = HTTPBasicAuth(client_id, client_secret)
    headers = {'accept':'application/json'}
    response = requests.post(url, auth=auth, headers=headers)
    logging.info(f'Authentication status is : {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        return data['access_token']
        
def check_job(url, access_token):
    headers = {
        'accept': 'application/fhir+json',
        'Authorization': f'Bearer {access_token}',
    }
    while True:
        response = requests.get(url, headers=headers)
        if response.content:
          data = json.loads(response.text)
          return data['output']
      
 
 # explain below code
 
def lambda_handler(event, context):
    
    logging.info(f'Inside main handler ')
    
    base_url = 'https://sandbox.bcda.cms.gov/api/v2'
    endpoint = '/Patient'
    access_token = get_auth()
    headers = {
        'accept': 'application/fhir+json',
        'Prefer': 'respond-async',
        'Authorization': f'Bearer {access_token}',
    }
    logging.info(f' Before making request to BCDA')
    if 'since' in event:
        since = event['since']
        params = {
            '_since': since,
        }
        
        response = requests.get(f'{base_url}{endpoint}/$export', headers=headers, params=params)
        
    else:
        response = requests.get(f'{base_url}{endpoint}/$export', headers=headers)
        
        logging.info(f'BCDA Response : {response.status_code}') 
        
    if response.status_code == 202:
        content_location = response.headers['Content-Location']
        job_output = check_job(content_location, access_token)
        for link in job_output:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Accept-Encoding': 'gzip',
            }
            logging.info("download data ")
            response = requests.get(link['url'], headers=headers)
            logging.info(f'BCDA API response " : {response.status_code}')
            if response.status_code == 200:
                date = datetime.now().strftime('%Y-%m-%d')
                s3 = boto3.client('s3')
                s3.put_object(Bucket=s3_bucket, Key=f'{date}/{os.path.basename(link["url"])}', Body=response.content)
                logging.info(" After putting data to s3 ")

    return {
        'statusCode': response.status_code
    }