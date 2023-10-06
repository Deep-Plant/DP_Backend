from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    render_template_string,
)
from db_model import Meat

create_api = Blueprint("create_api", __name__)

# 특정 육류의 기본 정보 생성
@create_api.route("/std_data",methods=["GET","POST"])
def add_specific_meat_data():
    try:
        if request.method == "POST":
            data = request.get_json()
            id = data.get("id")
            meat = Meat.query.get(id)
            if meat.statusType == 2:
                return jsonify({"msg":"Already Confirmed Meat Std Data"}), 401
            
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg":e})

# 특정 육류의 딥 에이징 이력 생성
@create_api.route("/deepAging_data",methods=["GET","POST"])
def add_specific_deepAging_data():
    try:
        if request.method == "GET":
            pass
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg":e})

# 특정 육류의 관능 검사 결과 생성
@create_api.route("/sensory_data",methods=["GET","POST"])
def add_specific_sensory_eval():
    try:
        if request.method == "GET":
            pass
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg":e})

# 특정 육류의 가열육 관능 검사 결과 생성
@create_api.route("/heatedmeat_data",methods=["GET","POST"])
def add_specific_heatedmeat_sensory_data():
    try:
        if request.method == "GET":
            pass
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg":e})

# 특정 육류의 실험실 데이터 생성
@create_api.route("/probexpt_data",methods=["GET","POST"])
def add_specific_probexpt_data():
    try:
        if request.method == "GET":
            pass
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        return jsonify({"msg":e})

