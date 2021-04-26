#!/bin/sh
set -e

cp_modules(){
	set ./modules/*.py
	if [ -e "$1" ]; then
		ln -ft hemppa/modules "$@" 
	fi
}

. ./.env
export MATRIX_ACCESS_TOKEN
export MATRIX_USER
export MATRIX_SERVER
export BOT_OWNERS
export TZ

cp_modules

cd hemppa
pipenv run python3 bot.py "$@"
