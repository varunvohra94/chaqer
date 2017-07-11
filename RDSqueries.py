import sys
import rds_config
import pymysql
import logging
import os

logging.basicConfig()

rds_host = rds_config.db_endpoint
name = rds_config.db_username
password = rds_config.db_password
db_name = rds_config.db_name
port = 3306

logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    conn = pymysql.connect(rds_host, user=name,passwd=password, db=db_name, connect_timeout=10)
except Exception as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySql instance.")
    sys.exit()


cur = conn.cursor()

cur.execute("select * from AWSResults")
for row in cur:
    #item_count += 1
    #logger.info(row)
    print(row)
