#!/bin/bash

apt update && apt install -y postgresql-client
pip install -r requirements.txt

exec "$@"
