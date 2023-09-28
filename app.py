# 서버 메인 파일
from flask import Flask
from flask_cors import CORS
import boto3
from dotenv import load_dotenv
import os

# 환경변수 다운로드
load_dotenv() 

app = Flask(__name__)
# RDS DB 연결
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# S3 연결
s3_client = boto3.client(
    "s3",
    aws_access_key_id= os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name = os.getenv("S3_REGION_NAME")
)

# API Blueprint 연결
if __name__ == "__main__":
    app.run(debug = True)