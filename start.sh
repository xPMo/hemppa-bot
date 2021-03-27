#!/bin/sh
set -xe

. ./.env
export MATRIX_ACCESS_TOKEN
export MATRIX_USER
export MATRIX_SERVER
export BOT_OWNERS
export TZ

cd hemppa
env | grep MATRIX
pipenv run python3 bot.py
