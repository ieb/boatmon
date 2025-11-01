#!/bin/bash 
while true
do
	git checkout . 1> /dev/null 2> /dev/null
	beforeSha1=$(git rev-parse HEAD)
	git pull > /dev/null
	afterSha1=$(git rev-parse HEAD)
	if [ "a${beforeSha1}" != "a${afterSha1}" ]
	then
		echo Boatmon OTA New Version Detected
		git log | head -3
		/home/ieb/.local/bin/uv sync
		killall -e /home/ieb/boatmon/.venv/bin/python3
		exit
	fi
	sleep 300
done