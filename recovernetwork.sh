#!/bin/bash
while true
do
  ping -c 1 8.8.8.8 > /dev/null

  if [ $? -ne 0 ]; then
    echo "Internet down, restarting NetworkManager..."
    echo systemctl restart NetworkManager
  fi
  sleep 120
done