FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy


WORKDIR /app

COPY "project01(storagevc)/requirements.txt" /tmp/p1.txt

COPY project02/requirements.txt /tmp/p2.txt

RUN pip install  -r /tmp/p1.txt -r /tmp/p2.txt

RUN playwright install --with-deps chromium

COPY "project01(storagevc)" "/app/project01(storagevc)"
COPY project02 /app/project02

WORKDIR /app/project02

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.fileWatcherType=none"]
