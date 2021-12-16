import boto3

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

#Creating S3 Resource From the Session.
s3 = session.resource('s3')
object = s3.Object(bucket_name, "audio.mp3") #specify how file should be named
result = object.put(Body=open('C:/Users/user/Desktop/transcribe-sample.mp3', 'rb')) #path to local file

res = result.get('ResponseMetadata')
if res.get('HTTPStatusCode') == 200:
  print('File Uploaded Successfully')
else:
  print('File Not Uploaded')

