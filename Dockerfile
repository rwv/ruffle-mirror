FROM node:alpine

RUN apk add --no-cache python3 

WORKDIR /app

COPY package.json /app/package.json
COPY .npmrc /app/.npmrc
COPY main.py /app/main.py

ENTRYPOINT ["python3", "/app/main.py"]