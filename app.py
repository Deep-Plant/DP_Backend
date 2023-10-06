# 서버 메인 파일
from flask import Flask
from flask_cors import CORS
import boto3
from dotenv import load_dotenv
import os
from db_model import initialize_db
from user_api import user_api
from create_api import create_api
from read_api import read_api
from update_api import update_api
from delete_api import delete_api
from firebase_model import FireBase_

# 1. 환경변수 다운로드
load_dotenv()
app = Flask(__name__)

# 2. RDS DB 연결
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db_session = initialize_db(app)

# 3. S3 연결
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("S3_REGION_NAME"),
)
# 4. Firebase Config
firestore_conn = FireBase_()

# 4. API Blueprint 연결
app.register_blueprint(user_api, url_prefix="/user")  # user 관련 API
app.register_blueprint(create_api, url_prefix="/meat/create")  # 육류 정보 조회 API
app.register_blueprint(read_api, url_prefix="/meat/read")  # 육류 정보 조회 API
app.register_blueprint(update_api, url_prefix="/meat/update")  # 육류 정보 수정 API
app.register_blueprint(delete_api, url_prefix="/meat/delete")  # 육류 정보 삭제 API

if __name__ == "__main__":
    app.run(debug=True)
