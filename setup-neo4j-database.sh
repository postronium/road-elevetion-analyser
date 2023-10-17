#!/bin/bash

source .env

docker run -p 7474:7474 -p 7687:7687 neo4j