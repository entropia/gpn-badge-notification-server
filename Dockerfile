#FROM python:alpine
FROM hypriot/rpi-alpine-scratch

RUN apk add -U python3-dev postgresql-dev gcc musl-dev

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN cp settings.py.sample settings.py

EXPOSE 5000

CMD [ "python3", "./main.py" ]
