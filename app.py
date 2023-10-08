# 서버 메인 파일
from flask import Flask, current_app
from contextlib import closing
from flask_cors import CORS
from dotenv import load_dotenv
import os
from db_model import initialize_db

from firebase_connect import FireBase_
from s3_connect import S3_
from utils import logger

app = Flask(__name__)

def initialize_services():
    # 환경변수 다운로드
    load_dotenv()
    
    # RDS DB 연결
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DB_URI")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    # Using Flask's built-in extensions
    
    # Here, you can associate your objects with the application context.
    with app.app_context():
        current_app.db_session = initialize_db(app)
        current_app.s3_conn = S3_(
            s3_bucket_name=os.getenv("S3_BUCKET_NAME"),
            service_name="s3",
            region_name=os.getenv("S3_REGION_NAME"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        current_app.firestore_conn = FireBase_("serviceAccountKey.json")


# 6. Flask 객체 실행
if __name__ == "__main__":
     
    initialize_services()
    CORS(app)

    # 5. API Blueprint 연결
    from user_api import user_api
    from create_api import create_api
    from get_api import get_api
    from update_api import update_api
    from delete_api import delete_api
    
    app.register_blueprint(user_api, url_prefix="/user")  # user 관련 API
    app.register_blueprint(create_api, url_prefix="/meat/create")  # 육류 정보 조회 API
    app.register_blueprint(get_api, url_prefix="/meat/get")  # 육류 정보 조회 API
    app.register_blueprint(update_api, url_prefix="/meat/update")  # 육류 정보 수정 API
    app.register_blueprint(delete_api, url_prefix="/meat/delete")  # 육류 정보 삭제 API

    app.run(debug=True)
