FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY etl/ ./etl/
ENV ETL_DATA_DIR=/data
ENTRYPOINT ["python", "-m", "etl.cli"]
