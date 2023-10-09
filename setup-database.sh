#!/bin/bash

source .env

docker run --name road_elevation_analyser -e POSTGRES_USER=$DB_USERNAME -e POSTGRES_PASSWORD=$DB_PASSWORD -e POSTGRES_DB=$DB_NAME -d postgis/postgis