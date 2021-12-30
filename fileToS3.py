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

bucket_name = "audios.walkietalkie" #name of your s3 bucket

audio = open('C:/Users/user/Desktop/transcribe-sample.mp3', 'rb')

#Creating S3 Resource From the Session.
s3 = session.resource('s3')
object = s3.Object(bucket_name, "audio.mp3") #specify how file should be named
result = object.put(Body=audio.read(), Metadata={
      'user_id': "1",
      'source_lang': "1",
      'target_lang': "2",
      'room': "456"
    }) 

res = result.get('ResponseMetadata')
if res.get('HTTPStatusCode') == 200:
  print('File Uploaded Successfully')
else:
  print('File Not Uploaded')

#file = 'C:/Users/user/Desktop/transcribe-sample.mp3'
#payload = {}
#payload['user_id'] = 1
#payload['source_lang'] = "1" 
#payload['target_lang'] = "2"
#payload['audio'] = base64.b64encode(audio.read()).decode('utf-8') #need to decode cause "binary is not JSON serializable"
#js = json.dumps(payload)

#fileData = base64.b64decode(payload['audio']) #to read back

