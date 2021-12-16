#send {user id, original language, target language, original message (audio file)} via JSON to S3

import boto3
import base64
import json

# specify credentials
aws_access_key_id=""
aws_secret_access_key=""
aws_session_token=""

#Creating Session With Boto3.
session = boto3.Session(
aws_access_key_id=aws_access_key_id,
aws_secret_access_key=aws_secret_access_key,
aws_session_token=aws_session_token
)

bucket_name = "walkietalkie.testupload" #name of your s3 bucket

audio = open('C:/Users/user/Desktop/transcribe-sample.mp3', 'rb')
payload = {}
payload['user_id'] = 1
payload['source_lang'] = "en"
payload['target_lang'] = "de"
payload['audio'] = base64.b64encode(audio.read()).decode('utf-8') #need to decode cause "binary is not JSON serializable"
js = json.dumps(payload)

#fileData = base64.b64decode(payload['audio']) #to read back

#Creating S3 Resource From the Session.
s3 = session.resource('s3')
object = s3.Object(bucket_name, "audio.json") #specify how file should be named
result = object.put(Body=js) #ContentType = 'application/json'

res = result.get('ResponseMetadata')
if res.get('HTTPStatusCode') == 200:
  print('File Uploaded Successfully')
else:
  print('File Not Uploaded')

