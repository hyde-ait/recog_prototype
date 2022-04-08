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

EXPOSE 8000

# Lancer le serveur FastAPI
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "server:app"]
