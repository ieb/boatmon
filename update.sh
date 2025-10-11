#!/bin/bash 
git checkout . 1> /dev/null 2> /dev/null
berforeSha1=$(git rev-parse HEAD)
git pull > /dev/null
afterSha1=$(git rev-parse HEAD)
if [ "a${berforeSha1}" != "a${afterSha1}" ]
then
	echo Boatmon OTA New Version Detected
	uv sync
	killall -e /home/ieb/boatmon/.venv/bin/python3
fi