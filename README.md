# Pi boat monitor

Uses a Raspberry Pi to remotely montor temperature and humdity sending metrics to a Grafana Cloud account, keeping below the free limit.

# Pi Setup

Start with latest 64bit image on a Pi 3 B+ or later

## I2c sensors

* AD2020  address 5c
* BME280  address 7
* DS3231 only if the network connection is not reliable on boot and ntp fails

Check that they all respond 
    i2cdetect -y 1

## enable hw interfaces

* sudo raspi-config 
** Interface Options -> enable i2c, 1w
** Performance Options -> enable overlay once setup is complete. 
** enable cli at start
** Advanced Options -> Set logging to volatile to minimise disk io

## RTC

If the netework connection is dodgy on boot then having a RTC on i2c helps, once connected and confirmed

    sudo su - root
    echo dtoverlay=i2c-rtc,ds3231 >> /boot/firmware/config.txt
    shutdown -r now
    i2cdetect -y 1

check that location 68 shows UU

    sudo apt-get install util-linux-extra
    date

check date is correct then write to clock

    sudo hwclock -w

check offset is 0s

    sudo hwclock -r -v


# Python UV setup

Install UV in the user space (not root)

    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env

# App setup

## Fetch this code

    mkdir boatmon
    git clone https://github.com/ieb/boatmon.git
    cd boatmon
    uv sync
    source .venv/bin/activate

## Setup Secrets

    cat > secrets.json << EOF
    {
     "p8s": {
       "userId" : "199993",
       "apiKey": "<your api key>",
       "url": "https://<your influx host>/api/v1/push/influx/write"
     },
    }
    EOF

## Install services


    sudo cp boatmon.service /etc/systemd/system
    sudo systemctl start boatmon
    sudo systemctl enable boatmon
    sudo systemctl status boatmon    

    sudo cp boatmon-ota.service /etc/systemd/system
    sudo systemctl start boatmon-ota
    sudo systemctl enable boatmon-ota
    sudo systemctl status boatmon-ota    



# todo

* [x] hwclock
* [x] convert to asyncio
* [x] send data to grafana
* [x] Implement service
* [x] Implement OTA updates
* [ ] move bme280 off board


