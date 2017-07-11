import chaqer
from chaqer import Chaqer
import boto3
import os
import datetime
import pandas as pd
import botocore
import zipfile
import shutil
import rds_config
import pymysql
import logging
import csv

logging.basicConfig()

chaqerObject = Chaqer()
s3 = boto3.resource('s3')
client = boto3.client('s3')
srcBucket = str(os.environ.get('BUCKET'))
srcKey = str(os.environ.get('FILE'))
rds_host = rds_config.db_endpoint
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name
port = 3306

try:
    cnx = pymysql.connect(rds_host, user=name,passwd=password, db=db_name, connect_timeout=10)
except Exception as e:
    print e
    logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
    sys.exit()

curr = cnx.cursor()

Chuck=0
Shaq=0
colNames = ['Name','TimeStamp','ISO','Shaq','Chuck']
df = pd.DataFrame(columns=colNames)


localFilename = '/tmp/{}'.format(os.path.basename(srcKey))
try:
    s3.Bucket(srcBucket).download_file(srcKey, localFilename)
    print 'Succesfully downloaded in temp'
except botocore.exceptions.ClientError as e:
    if e.response['Error']['Code'] == "404":
        print("The object does not exist.")
    else:
        raise

with zipfile.ZipFile(localFilename) as zip_file:
    for member in zip_file.namelist():
        filename = os.path.basename(member)
        # skip directories
        if not filename:
            continue

        # copy file (taken from zipfile's extract)
        source = zip_file.open(member)
        target = file(os.path.join('/tmp/', filename), "wb")
        with source, target:
            shutil.copyfileobj(source, target)

videoName = str(os.environ.get('FILE'))
videoName = videoName.rsplit("/",2)[1]

for imgFile in os.listdir('/tmp/'):
    if imgFile.find("img") != -1:
        #img = str(f.key)
        Chuck = 0
        Shaq = 0
        mili = '000'
        time = 0
        img = '/tmp/'+imgFile
        print img
        ID = os.path.basename(imgFile)
        time = ID.split("_",1)[0]
        time = float(time)
        ISO = str(datetime.timedelta(seconds=time))
        strTime = ISO.rsplit(".",1)[0]
        try:
            mili = ISO.rsplit(".",1)[1]
            mili = mili[:-3]
        except:
            pass
        ISO = strTime+":"+mili
        #print timeStamp
        faceMatches = chaqerObject.identifyFacesS3('chaqer',img)

        if faceMatches == 0:
            Chuck = int(Chuck)
            Shaq = int(Shaq)
            df_toAppend = pd.DataFrame([[videoName,time,ISO,Shaq,Chuck]],columns=colNames)
            df = df.append(df_toAppend)
            continue

        for i in range(0,len(faceMatches)):
            if 'Chuck' in faceMatches[i]["Name"]:
                Chuck = 1
            elif 'Shaq' in faceMatches[i]["Name"]:
                Shaq = 1
        Chuck = str(Chuck)
        Shaq = str(Shaq)
        time = str(time)
        try:
            curr.execute("INSERT INTO Azure_Results VALUES(%s,%s,%s,%s,%s)", (videoName,float(time),ISO,int(Shaq),int(Chuck)))
        except:
            curr.execute("create table Azure_Results ( Name VARCHAR(255) NOT NULL, Time FLOAT NOT NULL, ISO VARCHAR(255),Shaq SMALLINT,Chuck SMALLINT)")
            curr.execute("INSERT INTO Azure_Results VALUES(%s,%s,%s,%s,%s)", (videoName,float(time),ISO,int(Shaq),int(Chuck)))
        cnx.commit()
        df_toAppend = pd.DataFrame([[videoName,time,ISO,Shaq,Chuck]],columns=colNames)
        df = df.append(df_toAppend)

# .execute("INSERT INTO table VALUES(%s,%s)", (int(id), string))

df.reset_index(inplace=True,drop=True)


resultFileName = '/tmp/Azure_' + videoName + '_result.csv'

f = open("%s"%resultFileName,"w+")
f.close()
df.to_csv("%s"%resultFileName)

# csv_data = csv.reader(file('%s'%resultFileName))
# for row in csv:
#     try:
#         curr..execute("INSERT INTO Azure_Results VALUES(%s,%s)", (videoName,float(time),))

uploadKeyName = srcKey.rsplit("/",1)[0] + "/Azure_Results.csv"
s3.meta.client.upload_file("%s"%resultFileName,srcBucket,uploadKeyName)
