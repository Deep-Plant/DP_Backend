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
from db_model import Meat,SexInfo,GradeInfo,StatusInfo,SensoryEval,DeepAgingInfo,HeatedmeatSensoryEval,ProbexptData,User,decode_id
from user_api import get_user
from utils import *

get_api = Blueprint("get_api", __name__)
# 전체 육류 데이터 출력
@get_api.route("/")
def getMeatData():
    try:
        if request.method == "GET":
            db_session = current_app.db_session
            return get_range_meat_data(db_session,0,Meat.query.count()).get_json().get("meat_dict")

        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505
    
# 특정 ID에 해당하는 육류 데이터 출력
@get_api.route("/by_id")
def getMeatDataById():
    try:
        if request.method == "GET":
            db_session = current_app.db_session
            id = request.args.get("id")
            if id is None:
                raise Exception("Invalid Meat ID")
            result = get_meat(db_session, id)
            if result:
                try:
                    result["rawmeat_data_complete"] = (
                        all(
                            v is not None
                            for v in result["rawmeat"]["heatedmeat_sensory_eval"].values()
                        )
                        and all(
                            v is not None
                            for v in result["rawmeat"]["probexpt_data"].values()
                        )
                        and all(
                            v is not None
                            for v in result["rawmeat"]["sensory_eval"].values()
                        )
                    )
                except:
                    result["rawmeat_data_complete"] = False

                result["processedmeat_data_complete"] = {}
                for k, v in result["processedmeat"].items():
                    try:
                        result["processedmeat_data_complete"][k] = all(
                            all(vv is not None for vv in inner_v.values())
                            for inner_v in v.values()
                        )
                    except:
                        result["processedmeat_data_complete"][k] = False
                if not result["processedmeat_data_complete"]:
                    result["processedmeat_data_complete"] = False

                return jsonify(result)
            else:
                raise Exception(f"No Meat data found for {id}")
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# ID를 부분적으로 포함하는 육류 데이터 출력
@get_api.route("/by_partial_id")
def getMeatDataByPartialId():
    try:
        if request.method == "GET":
            db_session = current_app.db_session
            part_id = request.args.get("part_id")
            meats_with_statusType_2 = db_session.query(Meat).filter_by(statusType=2).all()
            meat_list = []
            for meat in meats_with_statusType_2:
                meat_list.append(meat.id)

            part_id_meat_list= [meat for meat in meat_list if part_id in meat]
            return jsonify({part_id: part_id_meat_list})
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# 범위에 해당하는 육류 데이터 출력
@get_api.route("/by_range_data")
def getMeatDataByRangeData():
    try:
        if request.method == "GET":
            db_session = current_app.db_session
            offset = request.args.get("offset")
            count = request.args.get("count")
            start = request.args.get("start")
            end = request.args.get("end")
            # filter
            farmAddr = safe_bool(request.args.get("farmAddr"))
            userId = safe_bool(request.args.get("userId"))
            type = safe_bool(request.args.get("type"))
            createdAt = safe_bool(request.args.get("createdAt"))
            statusType = safe_bool(request.args.get("statusType"))
            company = safe_bool(request.args.get("company"))
            return get_range_meat_data(offset,count,start,end,farmAddr,userId,type,createdAt,statusType, company,),200
        else:
            return jsonify({"msg": "Invalid Route, Please Try Again."}), 404
    except Exception as e:
        logger.exception(str(e))
        return jsonify({"msg": "Server Error","time":datetime.now().strftime("%H:%M:%S")}),505

# API Helper
def get_meat(db_session, id):
    # 1. 육류데이터 가져오기
    meat = db_session.query(Meat).filter(Meat.id == id).first()

    if meat is None:
        return None
    result = to_dict(meat)
    sexType = db_session.query(SexInfo).filter(SexInfo.id == result["sexType"]).first()
    gradeNum = (
        db_session.query(GradeInfo).filter(GradeInfo.id == result["gradeNum"]).first()
    )
    statusType = (
        db_session.query(StatusInfo)
        .filter(StatusInfo.id == result["statusType"])
        .first()
    )
    # 이미 있는거 변환
    result["sexType"] = sexType.value
    (
        result["specieValue"],
        result["primalValue"],
        result["secondaryValue"],
    ) = decode_id(result["categoryId"], db_session)
    result["gradeNum"] = gradeNum.value
    result["statusType"] = statusType.value
    result["createdAt"] = convert2string(result["createdAt"], 1)
    result["butcheryYmd"] = convert2string(result["butcheryYmd"], 2)
    result["birthYmd"] = convert2string(result["birthYmd"], 2)

    # 6. freshmeat , heatedmeat, probexpt
    result["rawmeat"] = {
        "sensory_eval": get_SensoryEval(db_session=db_session, id=id,seqno=0),
        "heatedmeat_sensory_eval": get_HeatedmeatSensoryEval(db_session=db_session, id =id, seqno = 0),
        "probexpt_data": get_ProbexptData(db_session=db_session, id = id, seqno= 0),
    }
    sensory_data = (
        db_session.query(SensoryEval).filter_by(id=id).order_by(SensoryEval.seqno.desc()).first()
    )  # DB에 있는 육류 정보
    if sensory_data:
        N = sensory_data.seqno
    else:
        N = 0

    result["processedmeat"] = {
        f"{i}회": {
            "sensory_eval": {},
            "heatedmeat_sensory_eval": {},
            "probexpt_data": {},
        }
        for i in range(1, N + 1)
    }
    for index in range(1, N + 1):
        result["processedmeat"][f"{index}회"]["sensory_eval"] = get_SensoryEval(
            db_session, id, index
        )
        result["processedmeat"][f"{index}회"][
            "heatedmeat_sensory_eval"
        ] = get_HeatedmeatSensoryEval(db_session, id, index)
        result["processedmeat"][f"{index}회"]["probexpt_data"] = get_ProbexptData(
            db_session, id, index
        )

    # remove field
    del result["categoryId"]
    return result

def get_SensoryEval(db_session, id, seqno):
    sensoryEval_data = (
        db_session.query(SensoryEval)
        .filter(
            SensoryEval.id == id,
            SensoryEval.seqno == seqno,
        )
        .first()
    )
    if sensoryEval_data:
        sensoryEval = to_dict(sensoryEval_data)
        sensoryEval["createdAt"] = convert2string(sensoryEval["createdAt"], 1)
        if seqno != 0:  # 가공육인 경우
            sensoryEval["deepaging_data"] = get_DeepAging(
                db_session, sensoryEval["deepAgingId"]
            )
            del sensoryEval["deepAgingId"]
        return sensoryEval
    else:
        return None
    
def get_DeepAging(db_session, id):
    deepAging_data = (
        db_session.query(DeepAgingInfo)
        .filter(
            DeepAgingInfo.deepAgingId == id,
        )
        .first()
    )
    if deepAging_data:
        deepAging_history = to_dict(deepAging_data)
        deepAging_history["date"] = convert2string(deepAging_history.get("date"), 2)
        return deepAging_history
    else:
        return None
    
def get_HeatedmeatSensoryEval(db_session, id, seqno):
    heated_meat = (
        db_session.query(HeatedmeatSensoryEval)
        .filter(
            HeatedmeatSensoryEval.id == id,
            HeatedmeatSensoryEval.seqno == seqno,
        )
        .first()
    )
    if heated_meat:
        heated_meat_history = to_dict(heated_meat)
        heated_meat_history["createdAt"] = convert2string(
            heated_meat_history["createdAt"], 1
        )
        del heated_meat_history["imagePath"]
        return heated_meat_history
    else:
        return None
    
def get_ProbexptData(db_session, id, seqno):
    probexpt = (
        db_session.query(ProbexptData)
        .filter(
            ProbexptData.id == id,
            ProbexptData.seqno == seqno,
        )
        .first()
    )
    if probexpt:
        probexpt_history = to_dict(probexpt)
        probexpt_history["updatedAt"] = convert2string(probexpt_history["updatedAt"], 1)
        return probexpt_history
    else:
        return None
    
def get_range_meat_data(
        db_session,
        offset,
        count,
        start=None,
        end=None,
        farmAddr=None,
        userId=None,
        type=None,
        createdAt=None,
        statusType=None,
        company=None,
    ):
        offset = safe_int(offset)
        count = safe_int(count)
        start = convert2datetime(start, 1)
        end = convert2datetime(end, 1)
        # Base Query
        query = db_session.query(Meat).join(User, User.userId == Meat.userId)  # Join with User

        # Sorting and Filtering
        if farmAddr is not None:
            if farmAddr:  # true: 가나다순 정렬
                query = query.order_by(Meat.farmAddr.asc())
            else:  # false: 역순
                query = query.order_by(Meat.farmAddr.desc())
        if userId is not None:
            if userId:  # true: 알파벳 오름차순 정렬
                query = query.order_by(Meat.userId.asc())
            else:  # false: 알파벳 내림차순 정렬
                query = query.order_by(Meat.userId.desc())
        if type is not None:
            if type:  # true: 숫자 오름차순 정렬
                query = query.order_by(User.type.asc())
            else:  # false: 숫자 내림차순 정렬
                query = query.order_by(User.type.desc())
        if company is not None:
            if company:  # true: 가나다순 정렬
                query = query.order_by(User.company.asc())
            else:  # false: 역순
                query = query.order_by(User.company.desc())
        if createdAt is not None:
            if createdAt:  # true: 최신순
                query = query.order_by(Meat.createdAt.desc())
            else:  # false: 역순
                query = query.order_by(Meat.createdAt.asc())
        if statusType is not None:
            if statusType:  # true: 숫자 오름차순 정렬
                query = query.order_by(Meat.statusType.asc())
            else:  # false: 숫자 내림차순 정렬
                query = query.order_by(Meat.statusType.desc())

        # 기간 설정 쿼리
        if start is not None and end is not None:
            query = query.filter(Meat.createdAt.between(start, end))
        query = query.offset(offset * count).limit(count)

        # 탐색
        meat_data = query.all()
        meat_result = {}
        id_result = [data.id for data in meat_data]
        for id in id_result:
            meat_result[id] = get_meat(db_session, id)
            userTemp = get_user(db_session,meat_result[id].get("userId"))
            if userTemp:
                meat_result[id]["name"] = userTemp.get("name")
                meat_result[id]["company"] = userTemp.get("company")
                meat_result[id]["type"] = userTemp.get("type")
            else:
                meat_result[id]["name"] = userTemp
                meat_result[id]["company"] = userTemp
                meat_result[id]["type"] = userTemp
            del meat_result[id]["processedmeat"]
            del meat_result[id]["rawmeat"]

        result = {
            "DB Total len": db_session.query(Meat).count(),
            "id_list": id_result,
            "meat_dict": meat_result,
        }

        return jsonify(result)