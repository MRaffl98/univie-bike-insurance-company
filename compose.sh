#! /bin/sh

sudo docker-compose stop 
sudo docker-compose down
sudo docker-compose build --no-cache
sudo docker-compose up -d

