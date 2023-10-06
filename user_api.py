from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    render_template_string,
)
from db_model import (
    User,
    UserTypeInfo,
    item_encoder,
    to_dict,
    convert2datetime,
    convert2string,
)
import hashlib
import uuid
from datetime import datetime

user_api = Blueprint("user_api", __name__)


# 1. API
@user_api.route("/register", methods=["GET", "POST"])
def register_user_data():
    try:
        if request.method == "POST":
            data = request.get_json()
            user = create_user(data)
            from app import db_session

            db_session.add(user)
            db_session.commit()
            return jsonify({"msg": f"{data['userId']}"}), 200
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg": e})


@user_api.route("/get", methods=["GET", "POST"])
def read_user_data():
    try:
        if request.method == "GET":
            userId = request.args.get("userId")
            if userId:
                result = get_user(userId)
            else:
                result = _get_users_by_type()
            return jsonify(result), 200
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg": e})


@user_api.route("/update", methods=["GET", "POST"])
def update_user_data():
    try:
        if request.method == "POST":
            data = request.get_json()
            user = update_user(data, "old")
            from app import db_session

            db_session.merge(user)
            db_session.commit()
            return jsonify(get_user(data.get("userId"))), 200
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg": e})


@user_api.route("/id_check", methods=["GET", "POST"])
def check_duplicate():
    try:
        if request.method == "GET":
            id = request.args.get("userId")
            user = User.query.filter_by(userId=id).first()
            if user is None:
                return jsonify({"msg": "None Duplicated Id"}), 200
            else:
                return jsonify({"msg": "Duplicated Id"}), 401
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg": e})


@user_api.route("/pwd_check", methods=["GET", "POST"])
def check_pwd():
    try:
        if request.method == "POST":
            data = request.get_json()
            id = data.get("userId")
            password = data.get("password")
            user = User.query.filter_by(userId=id).first()
            if user is None:
                return (
                    jsonify(
                        {
                            "msg": f"No user data in Database",
                            "userId": id,
                        }
                    ),
                    404,
                )
            if user.password != hashlib.sha256(password.encode()).hexdigest():
                return (
                    jsonify(
                        {
                            "msg": f"Invalid password for userId",
                            "userId": id,
                        }
                    ),
                    401,
                )
            return jsonify(get_user(id)), 200
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg": e})


@user_api.route("/delete", methods=["GET", "POST"])
def delete_user():
    try:
        if request.method == "GET":
            id = request.args.get("userId")
            user = User.query.filter_by(userId=id).first()
            if user is None:
                return (
                    jsonify(
                        {
                            "msg": f"No user data in Database",
                            "userId": id,
                        }
                    ),
                    404,
                )
            from app import db_session

            try:
                db_session.delete(user)
                db_session.commit()
                return (
                    jsonify(
                        {
                            f"msg": f"User with userId has been deleted",
                            "userId": id,
                        }
                    ),
                    200,
                )
            except:
                db_session.rollback()
                raise Exception("Deleted Failed")

        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 401
    except Exception as e:
        return jsonify({"msg": e})


# 2. API Helper
def create_user(user_data: dict):
    try:
        for field, value in user_data.items():
            if field == "password":
                item_encoder(
                    user_data, field, hashlib.sha256(value.encode()).hexdigest()
                )
            elif field == "type":
                user_type = UserTypeInfo.query.filter_by(name=value).first()
                if user_type:  # check if user_type exists
                    item_encoder(user_data, field, user_type.id)
                else:
                    item_encoder(user_data, field, 3)
            else:
                item_encoder(user_data, field)
        new_user = User(**user_data)
        return new_user
    except Exception as e:
        raise Exception(str(e))


def update_user(user_data: dict):
    try:
        history = User.query.filter_by(userId=user_data.get("userId")).first()
        # 1. 기존 유저 없음
        if history == None:
            raise Exception(f"No User ID {user_data.get('userId')}")

        # 2. 기존 유저 있음
        for field, value in user_data.items():
            if field == "password":
                item_encoder(
                    user_data, field, hashlib.sha256(value.encode()).hexdigest()
                )
            elif field == "type":
                user_type = UserTypeInfo.query.filter_by(name=value).first()
                if user_type:  # check if user_type exists
                    item_encoder(user_data, field, user_type.id)
                else:
                    item_encoder(user_data, field, 3)
            elif field == "updatedAt":
                item_encoder(user_data, field, datetime.now())
            else:
                item_encoder(user_data, field)

        for attr, value in user_data.items():
            setattr(history, attr, value)
        return history

    except Exception as e:
        raise Exception(str(e))


def get_user(userId):
    try:
        from app import db_session

        userData = db_session.query(User).filter(User.userId == userId).first()
        userData_dict = to_dict(userData)
        userData_dict["createdAt"] = convert2string(userData_dict.get("createdAt"), 1)
        userData_dict["updatedAt"] = convert2string(userData_dict.get("updatedAt"), 1)
        userData_dict["loginAt"] = convert2string(userData_dict.get("loginAt"), 1)
        userData_dict["type"] = (
            db_session.query(UserTypeInfo)
            .filter(UserTypeInfo.id == userData_dict.get("type"))
            .first()
            .name
        )
        return userData_dict

    except Exception as e:
        raise Exception(str(e))


def _get_users_by_type():
    try:
        # UserType 별로 분류될 유저 정보를 담을 딕셔너리
        user_dict = {}

        # 모든 유저 정보를 조회
        users = User.query.all()

        # 조회된 유저들에 대하여
        for user in users:
            # 해당 유저의 UserType을 조회
            user_type = UserTypeInfo.query.get(user.type).name

            # user_dict에 해당 UserType key가 없다면, 새로운 리스트 생성
            if user_type not in user_dict:
                user_dict[user_type] = []

            # UserType에 해당하는 key의 value 리스트에 유저 id 추가
            user_dict[user_type].append(user.userId)

        return user_dict
    except Exception as e:
        raise Exception(str(e))
