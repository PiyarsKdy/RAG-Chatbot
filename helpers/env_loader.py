import os
import openai
from dotenv import load_dotenv


load_dotenv()
aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
rds_host=os.getenv('RDS_HOST')
rds_port=os.getenv('RDS_PORT')
rds_user=os.getenv('RDS_USER')
rds_db_name=os.getenv('RDS_DB_NAME')
rds_password=os.getenv('RDS_PASSWORD')
openai.api_key = os.getenv("OPENAI_API_KEY")