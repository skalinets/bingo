# create dockerfile for python app
FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt --no-cache-dir

COPY . .

CMD ["python", "main.py"]
