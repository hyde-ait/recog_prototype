# 
FROM python:3.10-slim-buster

# 
COPY . /app
WORKDIR /app

# 
COPY requirements.txt requirements.txt

# update
RUN apt-get update 

# installer les librairies linux nécéssaires pour compiler les packages python
RUN apt-get install -y --no-install-recommends gcc libsasl2-dev python-dev libldap2-dev libssl-dev libsnmp-dev \
    && rm -rf /var/lib/apt/lists/*

# installer les packages python 
RUN pip install -r requirements.txt 

#supprimer les libraries linux
RUN apt-get purge -y --auto-remove gcc libsasl2-dev python-dev libldap2-dev libssl-dev libsnmp-dev

#installer coturn pour le serveur STUN/TURN
RUN apt-get install -y coturn && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

#Variables d'environnement concernant le serveur STUN/TURN
ENV TURN_PORT 3478
ENV TURN_PORT_START 10000
ENV TURN_PORT_END 20000
ENV TURN_SECRET mysecret99
ENV TURN_SERVER_NAME coturn
ENV TURN_REALM recog.coturn

ADD start_server.sh start_server.sh

RUN chmod +x start_server.sh

EXPOSE 8000

# Lancer le serveur coturn et le serveur FastAPI
CMD ["./start_server.sh"]


