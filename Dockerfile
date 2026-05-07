FROM python:3.12-slim
WORKDIR /app
COPY harness/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY harness/central.py .
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "central.py"]
