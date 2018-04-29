
FROM arm64v8/python:alpine3.7

RUN apk add -U python3-dev postgresql-dev gcc musl-dev

WORKDIR /usr/src/app

COPY . .
RUN pip3 install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD [ "python3", "./main.py" ]
