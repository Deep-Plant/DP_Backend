from flask import (
    Blueprint,
    jsonify,
    request,
    session,
    redirect,
    url_for,
    render_template_string,
    current_app
)
from db_model import Meat,SexInfo,GradeInfo,SensoryEval,DeepAgingInfo,HeatedmeatSensoryEval,find_id
from utils import *
import uuid

create_api = Blueprint("create_api", __name__)

# 특정 육류의 기본 정보 생성
@create_api.route("/std_data",methods=["GET","POST"])
def add_specific_meat_data():
    db_session = current_app.db_session
    s3_conn = current_app.s3_conn
    firestore_conn = current_app.firestore_conn
    try:
        if request.method == "POST":
            # 1. Data Get
            data = request.get_json()
            id = data.get("id")
            meat = db_session.query(Meat).get(id)
            if meat.statusType == 2:
                return jsonify({"msg":"Already Confirmed Meat Std Data"}), 401
            # 1. DB merge
            new_meat = create_meat(meat_data=data,db_session = db_session)
            new_meat.statusType = 0
            db_session.merge(new_meat)

            # 2. Firestore -> S3
            transfer_folder_image(s3_conn=s3_conn,firestore_conn=firestore_conn,db_session=db_session,id=id,new_meat=new_meat,folder="qr_codes")
            db_session.commit()
            return jsonify({"msg":"Successfully Create or Update Meat data","id":id}),200
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        db_session.rollback()
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# 특정 육류의 딥 에이징 이력 생성
@create_api.route("/deepAging_data",methods=["GET","POST"])
def add_specific_deepAging_data():
    try:
        if request.method == "POST":
            db_session = current_app.db_session
            data = request.get_json()
            return create_specific_deep_aging_meat_data(data,db_session)
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# 특정 육류의 관능 검사 결과 생성
@create_api.route("/sensory_data",methods=["GET","POST"])
def add_specific_sensory_eval():
    try:
        if request.method == "POST":
            db_session = current_app.db_session
            s3_conn = current_app.s3_conn
            firestore_conn = current_app.firestore_conn
            data = request.get_json()
            return create_specific_sensoryEval(db_session,s3_conn,firestore_conn,data)
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# 특정 육류의 가열육 관능 검사 결과 생성
@create_api.route("/heatedmeat_data",methods=["GET","POST"])
def add_specific_heatedmeat_sensory_data():
    try:
        if request.method == "POST":
            db_session = current_app.db_session
            data = request.get_json()
            return create_specific_heatedmeat_seonsory_data(db_session,data)
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# 특정 육류의 실험실 데이터 생성
@create_api.route("/probexpt_data",methods=["GET","POST"])
def add_specific_probexpt_data():
    try:
        if request.method == "POST":
            db_session = current_app.db_session
            data = request.get_json()
            return create_specific_probexpt_data(db_session,data)
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# API helper
def create_meat(meat_data:dict,db_session):
    if meat_data is None:
        raise Exception("Invalid Meat Data")
    # 1. Get the ID of the record in the SexType table
    sex_type = (
        db_session.query(SexInfo).filter_by(value=meat_data.get("sexType")).first()
    )
    # 2. Get the ID of the record in the GradeNum table
    grade_num = (
        db_session.query(GradeInfo).filter_by(value=meat_data.get("gradeNum")).first()
    )
    # 3. meat_data에 없는 필드 추가

    # 4, meat_data에 있는 필드 수정
    for field in list(meat_data.keys()):
        if field == "sexType":
            try:
                item_encoder(meat_data, field, sex_type.id)
            except Exception as e:
                raise Exception("Invalid sex_type id")
        elif field == "gradeNum":
            try:
                item_encoder(meat_data, field, grade_num.id)
            except Exception as e:
                raise Exception("Invalid grade_num id")
        elif (
            field == "specieValue"
            or field == "primalValue"
            or field == "secondaryValue"
        ):
            item_encoder(
                meat_data,
                "categoryId",
                find_id(
                    meat_data.get("specieValue"),
                    meat_data.get("primalValue"),
                    meat_data.get("secondaryValue"),
                    db_session,
                ),
            )
        else:
            item_encoder(meat_data, field)

    # 5. meat_data에 없어야 하는 필드 삭제
    meat_data.pop("specieValue")
    meat_data.pop("primalValue")
    meat_data.pop("secondaryValue")

    # Create a new Meat object
    try:
        new_meat = Meat(**meat_data)
    except Exception as e:
        raise Exception("Wrong meat DB field items" + str(e))
    return new_meat

def create_DeepAging(meat_data:dict):
    if meat_data is None:
        raise Exception("Invalid Deep Aging meat_data")
    for field in meat_data.keys():
        item_encoder(meat_data, field)
    meat_data["deepAgingId"] = str(uuid.uuid4())
    try:
        new_deepAging = DeepAgingInfo(**meat_data)
    except Exception as e:
        raise Exception("Wrong DeepAging DB field items: " + str(e))
    
def create_SensoryEval( meat_data: dict, seqno: int, id: str, deepAgingId: int):
    """
    db: SQLAlchemy db
    freshmeat_data: 모든 필드의 데이터가 문자열로 들어왔다고 가정!!
    seqno: 신선육 관능검사 seqno
    freshmeatId: 가열육 관능검사 seqno
    probexpt_seqno: 실험(전자혀) 관능 검사 seqno
    type: 0(신규 생성) or 1(기존 수정)
    """
    if meat_data is None:
        raise Exception("Invalid Sensory_Evaluate data")
    # 1. freshmeat_data에 없는 필드 추가
    item_encoder(meat_data, "seqno", seqno)
    item_encoder(meat_data, "id", id)
    item_encoder(meat_data, "deepAgingId", deepAgingId)
    # 2. freshmeat_data에 있는 필드 수정
    for field in meat_data.keys():
        if field == "seqno":  # 여기 있어도 걍 입력된걸 써라~
            pass
        elif field == "freshmeatId":  # 여기 있어도 걍 입력된걸 써라~
            pass
        elif field == "deepAgingId":
            pass
        else:
            item_encoder(meat_data, field)
    # Create a new Meat object
    try:
        new_SensoryEval = SensoryEval(**meat_data)
    except Exception as e:
        raise Exception("Wrong sensory eval DB field items" + str(e))
    return new_SensoryEval

def create_HeatemeatSensoryEval(meat_data: dict, seqno: int, id: str):
    """
    db: SQLAlchemy db
    heatedmeat_data: 모든 필드의 데이터가 문자열로 들어왔다고 가정!!
    seqno: 신선육 관능검사 seqno
    heatedMeatId: 가열육 관능검사 seqno
    probexpt_seqno: 실험(전자혀) 관능 검사 seqno
    type: 0(신규 생성) or 1(기존 수정)
    """
    if meat_data is None:
        raise Exception("Invalid Heatedmeat Sensory Evaluate data")
    # 1. heatedmeat_data에 없는 필드 추가
    item_encoder(meat_data, "seqno", seqno)
    item_encoder(meat_data, "id", id)
    # 2. heatedmeat_data에 있는 필드 수정
    for field in meat_data.keys():
        if field == "seqno":
            pass
        elif field == "id":
            pass
        else:
            item_encoder(meat_data, field)
    # Create a new Meat object
    try:
        new_heatedmeat = HeatedmeatSensoryEval(**meat_data)
    except Exception as e:
        raise Exception("Wrong heatedmeat sensory eval DB field items" + str(e))
    return new_heatedmeat

def create_ProbexptData(meat_data: dict, seqno: int, id: str):
    """
    db: SQLAlchemy db
    heatedmeat_data: 모든 필드의 데이터가 문자열로 들어왔다고 가정!!
    seqno: 신선육 관능검사 seqno
    heatedMeatId: 가열육 관능검사 seqno
    probexpt_seqno: 실험(전자혀) 관능 검사 seqno
    type: 0(신규 생성) or 1(기존 수정)
    """
    if meat_data is None:
        raise Exception("Invalid Heatedmeat Sensory Evaluate data")
    # 1. heatedmeat_data에 없는 필드 추가
    item_encoder(meat_data, "seqno", seqno)
    item_encoder(meat_data, "id", id)
    # 2. heatedmeat_data에 있는 필드 수정
    for field in meat_data.keys():
        if field == "seqno":
            pass
        elif field == "id":
            pass
        else:
            item_encoder(meat_data, field)
    # Create a new Meat object
    try:
        new_heatedmeat = HeatedmeatSensoryEval(**meat_data)
    except Exception as e:
        raise Exception("Wrong heatedmeat sensory eval DB field items" + str(e))
    return new_heatedmeat

def create_specific_deep_aging_meat_data(db_session,data):
    # 2. 기본 데이터 받아두기
    id = data.get("id")
    seqno = data.get("seqno")
    deepAging_data = data.get("deepAging")
    data.pop("deepAging", None)
    meat = db_session.query(Meat).get(id)  # DB에 있는 육류 정보
    if id == None:  # 1. 애초에 id가 없는 request
        raise Exception("No Id in Request Data")
    sensory_eval = db_session.query(SensoryEval).filter_by(
        id=id, seqno=seqno
    ).first()  # DB에 있는 육류 정보
    try:
        if deepAging_data is not None:
            if meat:  # 승인 정보 확인
                if meat.statusType != 2:
                    raise Exception("Not Confirmed Meat Data")
            if sensory_eval:  # 기존 Deep Aging을 수정하는 경우
                deepAgingId = sensory_eval.deepAgingId
                existing_DeepAging = db_session.query(DeepAgingInfo).get(deepAgingId)
                if existing_DeepAging:
                    for key, value in deepAging_data.items():
                        setattr(existing_DeepAging, key, value)
                else:
                    raise Exception("No Deep Aging Data found for update")
            else:  # 새로운 Deep aging을 추가하는 경우
                new_DeepAging = create_DeepAging(deepAging_data)
                deepAgingId = new_DeepAging.deepAgingId
                db_session.add(new_DeepAging)
                db_session.commit()
                new_SensoryEval = create_SensoryEval(
                    data, seqno, id, deepAgingId
                )
                db_session.merge(new_SensoryEval)
            db_session.commit()
        else:
            raise Exception("No deepaging data in request")
    except Exception as e:
        db_session.rollback()
        raise e
    return jsonify(id),200

def create_specific_sensoryEval(db_session,s3_conn,firestore_conn,data):
    # 2. 기본 데이터 받아두기
    id = data.get("id")
    seqno = data.get("seqno")
    deepAging_data = data.get("deepAging")
    data.pop("deepAging", None)
    meat = db_session.query(Meat).get(id)  # DB에 있는 육류 정보
    if id == None:  # 1. 애초에 id가 없는 request
        raise Exception("No ID data sent for update")

    sensory_eval = db_session.query(SensoryEval).filter_by(
        id=id, seqno=seqno
    ).first()  # DB에 있는 육류 정보
    try:
        if deepAging_data is not None:  # 가공육 관능검사
            if meat:  # 승인 정보 확인
                if meat.statusType != 2:
                    raise Exception("Not confirmed meat data")
            if sensory_eval:  # 기존 Deep Aging을 수정하는 경우
                deepAgingId = sensory_eval.deepAgingId
                new_SensoryEval = create_SensoryEval(
                    data, seqno, id, deepAgingId
                )
                db_session.merge(new_SensoryEval)
            else:  # 새로운 Deep aging을 추가하는 경우
                new_DeepAging = create_DeepAging(deepAging_data)
                deepAgingId = new_DeepAging.deepAgingId
                db_session.add(new_DeepAging)
                db_session.commit()
                new_SensoryEval = create_SensoryEval(
                     data, seqno, id, deepAgingId
                )
                db_session.merge(new_SensoryEval)
        else:  # 신선육 관능검사
            if meat:  # 수정하는 경우
                if meat.statusType == 2:
                    raise Exception("Already confirmed meat data")
            deepAgingId = None
            new_SensoryEval = create_SensoryEval(
                data, seqno, id, deepAgingId
            )
            db_session.merge(new_SensoryEval)
            meat.statusType = 0
            db_session.merge(meat)

        transfer_folder_image(
            s3_conn,firestore_conn,db_session,f"{id}-{seqno}", new_SensoryEval, "sensory_evals"
        )
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
    return jsonify(id)

def create_specific_heatedmeat_seonsory_data(db_session,data):
    # 2. 기본 데이터 받아두기
    id = data.get("id")
    seqno = data.get("seqno")
    meat = db_session.query(Meat).get(id)  # DB에 있는 육류 정보
    if meat:  # 승인 정보 확인
        if meat.statusType != 2:
            raise Exception("Not confirmed meat data")
    if id == None:  # 1. 애초에 id가 없는 request
        raise Exception("No ID data sent for update")
    try:
        new_HeatedmeatSensoryEval = create_HeatemeatSensoryEval(
            data, seqno, id
        )
        db_session.merge(new_HeatedmeatSensoryEval)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
    return jsonify(id)

def create_specific_probexpt_data(db_session,data):
    # 2. 기본 데이터 받아두기
    id = data.get("id")
    seqno = data.get("seqno")
    meat = db_session.query(Meat).get(id)  # DB에 있는 육류 정보
    if meat:  # 승인 정보 확인
        if meat.statusType != 2:
            raise Exception("Not confirmed meat data")
    if id == None:  # 1. 애초에 id가 없는 request
        raise Exception("No ID data sent for update")
    try:
        new_ProbexptData = create_ProbexptData(data, seqno, id)
        db_session.merge(new_ProbexptData)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e
    return jsonify(id)










