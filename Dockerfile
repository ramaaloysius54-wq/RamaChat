FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir python-dotenv httpx pytest

COPY . /app

EXPOSE 4040

CMD ["python3", "server/otp_server.py"]
