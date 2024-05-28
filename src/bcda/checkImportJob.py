import json
import boto3
import time
import os
import logging
logging.basicConfig(   level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s',    datefmt='%Y-%m-%d %H:%M:%S')
logging.getLogger().setLevel(logging.INFO)
datastore_id = os.environ['DATASTORE_ID']
def lambda_handler(event, context):
    healthlake = boto3.client('healthlake')
    status = 'PENDING'
    pending_job = True
    logging.info("starting job to check status of Healthlake Import Job")
    while pending_job:
        progress_response = healthlake.list_fhir_import_jobs(DatastoreId=datastore_id, JobStatus='IN_PROGRESS')
        submitted_response = healthlake.list_fhir_import_jobs(DatastoreId=datastore_id, JobStatus='SUBMITTED')
        if not progress_response['ImportJobPropertiesList'] and not submitted_response['ImportJobPropertiesList']:
            pending_job = False
            logging.info("Healthlake Import Job is complete")
            status = 'SUCCESS'
       
    return {
        'status': status
    }
