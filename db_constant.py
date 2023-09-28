from datetime import datetime

species = ["소", "돼지"]
cattleLarge = [
    "안심",
    "등심",
    "채끝",
    "목심",
    "앞다리",
    "우둔",
    "설도",
    "양지",
    "사태",
    "갈비",
]
pigLarge = [
    "안심",
    "등심",
    "목심",
    "앞다리",
    "갈비",
    "삼겹살",
    "뒷다리",
]
cattleSmall = {
    0: ["안심살"],
    1: [
        "윗등심",
        "꽃등심",
        "아래등심",
        "살치살",
    ],
    2: ["채끝살"],
    3: ["목심살"],
    4: [
        "꾸리살",
        "부채살",
        "앞다리살",
        "갈비덧살",
        "부채덮개살",
    ],
    5: [
        "우둔살",
        "홍두깨살",
    ],
    6: [
        "보섭살",
        "설깃살",
        "설깃머리살",
        "도가니살",
        "삼각살",
    ],
    7: [
        "양지머리",
        "차돌박이",
        "업진살",
        "업진안살",
        "치마양지",
        "치마살",
        "앞치마살",
    ],
    8: [
        "앞사태",
        "뒷사태",
        "뭉치사태",
    ],
    9: [
        "본갈비",
        "꽃갈비",
        "참갈비",
        "갈빗살",
        "마구리",
        "토시살",
        "안창살",
        "제비추리",
    ],
}
pigSmall = {
    0: ["안심살"],
    1: [
        "등심살",
        "등심덧살",
    ],
    2: ["목심살"],
    3: [
        "앞다리살",
        "앞사태살",
        "항정살",
        "꾸리살",
        "부채살",
        "주걱살",
    ],
    4: ["갈비", "갈비살", "마구리"],
    5: [
        "삼겹살",
        "갈매기살",
        "등갈비",
        "토시살",
        "오돌삼겹살",
    ],
    6: [
        "볼기살",
        "설깃살",
        "도가니살",
        "홍두께살",
        "보섭살",
        "뒷사태살",
    ],
}
usrType = {0: "Normal", 1: "Researcher", 2: "Manager", 3: None}
sexType = {0: "수", 1: "암", 2: "거세", 3: None}
gradeNum = {0: "1++", 1: "1+", 2: "1", 3: "2", 4: "3", 5: None}
statusType = {0: "대기중", 1: "반려", 2: "승인"}
CATTLE = 0
PIG = 1

def safe_float(val):
    """
    Safe Float 변환
    """
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def safe_str(val):
    """
    safe STR 반환
    """
    try:
        if val is not None:
            return str(val)
        else:
            return None
    except Exception:
        return None


def safe_int(val):
    """
    Safe Float 변환
    """
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def safe_bool(val):
    """
    Safe Float 변환
    """
    try:
        return bool(val)
    except (ValueError, TypeError):
        return None
    
def convert2datetime(date_string, format):
    """
    String -> Datetime
    Params
    1. date_string: 날짜/시간 문자열
    2. format: date_string의 포맷 인덱스(1 or 2,,,)
    """
    if date_string == None:
        return date_string
    if format == 1:
        return datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S")
    elif format == 2:
        return datetime.strptime(date_string, "%Y%m%d")
    else:
        return None
    
def convert2string(date_object, format):
    """
    Datetime -> String
    Params
    1. date_object: datetime object
    2. format: desired string format (1 or 2)
    """
    if date_object is None:
        return date_object
    if format == 1:
        return date_object.strftime("%Y-%m-%dT%H:%M:%S")
    elif format == 2:
        return date_object.strftime("%Y%m%d")
    else:
        return str(date_object)
    
def item_encoder(data_dict, item, input_data=None):
    datetime1_cvr = ["createdAt", "loginAt", "updatedAt"]
    datetime2_cvr = ["butcheryYmd", "birthYmd", "date"]
    str_cvr = [
        "id",
        "userId",
        "traceNum",
        "farmAddr",
        "farmerNm",
        "name",
        "company",
        "jobTitle",
        "homeAddr",
        "imagePath",
        "xai_imagePath",
        "xai_gradeNum_imagePath"
    ]
    int_cvr = ["period", "minute", "seqno"]
    float_cvr = [
        "marbling",
        "color",
        "texture",
        "surfaceMoisture",
        "overall",
        "flavor",
        "juiciness",
        "tenderness",
        "umami",
        "palability",
        "L",
        "a",
        "b",
        "DL",
        "CL",
        "RW",
        "ph",
        "WBSF",
        "cardepsin_activity",
        "MFI",
        "Collagen",
        "sourness",
        "bitterness",
        "richness",
    ]
    bool_cvr = ["alarm"]
    if item in datetime1_cvr:
        data_dict[item] = convert2datetime(data_dict.get(item), 1)
    elif item in datetime2_cvr:
        data_dict[item] = convert2datetime(data_dict.get(item), 2)
    elif item in str_cvr:
        data_dict[item] = safe_str(data_dict.get(item))
    elif item in int_cvr:
        data_dict[item] = safe_int(data_dict.get(item))
    elif item in float_cvr:
        data_dict[item] = safe_float(data_dict.get(item))
    elif item in bool_cvr:
        data_dict[item] = safe_bool(data_dict.get(item))
    else:
        data_dict[item] = input_data


def to_dict(model_instance, query_instance=None):
    if hasattr(model_instance, "__table__"):
        return {
            c.name: getattr(model_instance, c.name)
            for c in model_instance.__table__.columns
        }
    else:
        cols = query_instance.column_descriptions
        return {cols[i]["name"]: model_instance[i] for i in range(len(cols))}
    
def calId(id, s_id, type):
    """
    category id 계산 함수
    Params
    1. id: 대분할 인덱스
    2. s_id: 소분할 인덱스
    3. type: 종 인덱스

    """
    return 100 * type + 10 * id + s_id