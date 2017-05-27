# gpn17-badge-notification-server
## Setup
1. Import the postgresql schema ```schema.sql```
2. Copy the sample ```settings.py.sample``` to ```settings.py```
3. Configure the variables
4. Run ```main.py```

## Virtualenv
You can use python3's virtualenv to deploy the server.
1. ```virtualenv .```
2. ```source bin/activate```
3. ```ip install -r requirements.txt```
4. Proceed with regular setup

## Security
To use this server with your GPN17 Badge you need to configure a reverse proxy (for example nginx) with a working TLS setup.
Note that you need *at least* one of the following ciphers:
- ```TLS_RSA_AES128_CBC_SHA```
- ```TLS_RSA_AES256_CBC_SHA```




## Docker

Modify settings.py.docker, will be linked as settings.py in the container

Set Admin password
``` docker exec -it push_python /usr/src/app/manage_users.py create --admin admin ```
