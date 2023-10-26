# Base Python Image
FROM python:3.10.11-slim
RUN apt-get update && apt-get install -y gcc libffi-dev musl-dev && apt-get clean && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /app

# 라이브러리 설치
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 파일 컨테이너 복사
COPY . .

# Flask 앱 실행
CMD ["gunicorn","app:app","-w","4","-b","0.0.0.0:8080"]