FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY node_battery/ node_battery/

ENTRYPOINT ["python", "-m", "node_battery.main"]
