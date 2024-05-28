import json
import boto3
import os
import time
import logging
logging.basicConfig(   level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)
from datetime import datetime
datastore_id = os.environ['DATASTORE_ID']
data_access_role_arn = os.environ['DATA_ACCESS_ROLE']
s3_output_bucket = os.environ['OUTPUT_BUCKET']
region = os.environ['REGION']
account_id = os.environ['ACCOUNT_ID']
kms_key = os.environ['KMS_KEY']
kms_key_id = f'arn:aws:kms:{region}:{account_id}:key/{kms_key}'
def lambda_handler(event, context):
    logging.info('S3 event received ')     
    s3 = boto3.client('s3')
    healthlake = boto3.client('healthlake')
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    s3_url = f's3://{bucket}/{key}'
    s3_output_url = f's3://{s3_output_bucket}/'
    logging.info('Starting FHIR import job')
    pending_job = True
    while pending_job:
        progress_response = healthlake.list_fhir_import_jobs(DatastoreId=datastore_id, JobStatus='IN_PROGRESS')
        submitted_response = healthlake.list_fhir_import_jobs(DatastoreId=datastore_id, JobStatus='SUBMITTED')
        if not progress_response['ImportJobPropertiesList'] and not submitted_response['ImportJobPropertiesList']:
            pending_job = False
      
    status = ''
    try:
        response = healthlake.start_fhir_import_job(
            DatastoreId=datastore_id,
            InputDataConfig={'S3Uri': s3_url},
            JobOutputDataConfig={
                 "S3Configuration": {
                      "S3Uri": s3_output_url,
                      "KmsKeyId": kms_key_id
                  }
            },
             DataAccessRoleArn=data_access_role_arn
        )
        status = response['JobStatus']
        logging.info(f'FHIR import job status: {status}')
    except Exception as e:
        logging.error(f'Error starting FHIR import job: {e}')
        status = 'ERROR'
        return {
  'status': status
        }
    return {
        'status': status
    }
    