# Pi boat monitor

Uses a Raspberry Pi to remotely montor temperature and humdity sending metrics to a Grafana Cloud account, keeping below the free limit.

Below are my notes to reproduce to the setup.

# Pi Setup

Start with latest 64bit image on a Pi 3 B+ or later

## I2c sensors

* AD2020  address 5c  - allegedly not very accurate, but measurements indicate its stable
* BME280  address 7  - Do not mount close to the pi as if its warmed the humidity readings will be way out.
* DS3231 only if the network connection is not reliable on boot and ntp fails. TBH, needed since some parts do depend on time.

Check that they all respond 
    i2cdetect -y 1

## raspi-config Config

To setup

    sudo raspi-config 

** Interface Options -> enable i2c, 1w
** enable cli at start
** Advanced Options -> Set logging to volatile to minimise disk io

After setup, enable the overlay filesystem so that the flash drive does not fail

** Performance Options -> enable overlay once setup is complete. 

Also disabled gui login, turned off splash screen (cmdline.txt)

    sudo touch /etc/cloud/cloud-init.disabled
    sudo mount -o rw,remount /dev/mmcblk0p1 /boot/firmware
    sudo vi /boot/firmware/cmdline.txt

## Recovery from a bootloop

If the pi goes into a bootloop, mount the boot fs (fat) on a different machine and add init=/bin/bash to the end of the command line to boot into bash. The root file system has some flags that block it from being mounted on older kernels (bad superblock, but its not). Once booted into bash, you can remount rw, fix the boot loop problem (eg a service is restarting fast enough to cause a reboot), remove the init=/bin/bash from the command line and reboot.

eg

    # mount root rw
    mount -o rw,remount /dev/mmcblk0p2 /
    # fix bootloop
    vi /etc/systemd/services/boatmon.service
    # mount boot fs rw
    mount /dev/mmcblk0p2 /mnt
    # remove init=/bin/bash
    vi /mnt/cmdline.txt   
    sync 
    sync
    exit

The last exit will cause a kernel panic just power down and up again. Since init is not runnng, shutdown -r does not work.

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
     "loki": {
       "userId" : "199994",
       "apiKey": "<your api key>",
       "url": "https://<your loki host>/loki/api/v1/push"
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


    sudo cp shiplogs.service /etc/systemd/system
    sudo systemctl start shiplogs
    sudo systemctl enable shiplogs
    sudo systemctl status shiplogs    

## OTA Updates

Installations will pull ota updates via git pull. Should they fail and cause a restart of the main service repeatedly then the device will restart and reset the filesystem to a known working state to allow remote fixes. Not tested. A more complex blue green ota setup would have protected against this, but this is good enough for the moment.

## Ship logs

I tried Alloy, but it uses 24% of the RAM, so wrote some python that sends logs by tailing jounrnalctl, this uses 2% of the ram.



# todo

* [x] hwclock
* [x] convert to asyncio
* [x] send data to grafana
* [x] Implement service
* [x] Implement OTA updates
* [x] Ship logs
* [ ] move bme280 off board



test commit 
after after overlay fs enabled - 11/10/2025 12:05


