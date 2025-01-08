FROM python:3.12-slim

WORKDIR /app
COPY . /app

ENV PYTHONPATH=/app

RUN pip install flask

#Yet we don't have dependencies, but no doubt we will need some later on
RUN pip install --no-cache-dir -r requirements.txt

#I temporarily place the server on 127.0.0.1:5000
EXPOSE 5000

CMD ["python", "server/app.py"]
