FROM python:latest
COPY . /app
WORKDIR /app
EXPOSE 8000
RUN pip install -r requirements.txt
CMD ["python3", "main.py"]
