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

## raspi-config Config

To setup

    sudo raspi-config 

** Interface Options -> enable i2c, 1w
** enable cli at start
** Advanced Options -> Set logging to volatile to minimise disk io

After setup, enable the overlay filesystem so that the flash drive does not fail

** Performance Options -> enable overlay once setup is complete. 


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


## OTA Updates

Installations will pull ota updates via git pull. Should they fail and cause a restart of the main service repeatedly then the device will restart and reset the filesystem to a known working state to allow remote fixes. Not tested. A more complex blue green ota setup would have protected against this, but this is good enough for the moment.

## Ship logs

Seems that using alloy is simplest, and it might also work better at monitoring local apps rather than sending the metrics direct. Perhaps could switch to alloy of os monitoring.  However, it uses 25% of the availalbe RAM in RSS, and was a pain to setup.  vs, the python app which is using 3% of the ram, and could as easilly make the API calls to the logs. Also, impossble to reconfigure remotely.

    sudo mkdir -p /etc/apt/keyrings/
    wget -q -O - https://apt.grafana.com/gpg.key | gpg --dearmor | sudo tee /etc/apt/keyrings/grafana.gpg > /dev/null
    echo "deb [signed-by=/etc/apt/keyrings/grafana.gpg] https://apt.grafana.com stable main" | sudo tee /etc/apt/sources.list.d/grafana.list
    sudo apt-get update
    sudo apt-get install alloy
    sudo systemctl start alloy
    sudo systemctl status alloy
    sudo systemctl enable alloy.service

Configure alloy adding any command line params like expose local port while setting up, be sure to remove the open port when done setting up.

    sudo vi /etc/default/alloy 

eg

    ## Path:
    ## Description: Grafana Alloy settings
    ## Type:        string
    ## Default:     ""
    ## ServiceRestart: alloy
    #
    # Command line options for Alloy.
    #
    # The configuration file holding the Alloy config.
    CONFIG_FILE="/etc/alloy/config.alloy"

    # User-defined arguments to pass to the run command.
    CUSTOM_ARGS="--server.http.listen-addr=0.0.0.0:12345"

    # Restart on system upgrade. Defaults to true.
    RESTART_ON_UPGRADE=true


Configure alloy to send logs to grafana cloud

      // Sample config for Alloy.
      //
      // For a full configuration reference, see https://grafana.com/docs/alloy
      logging {
        level = "warn"
      }
     
      // internal only
      prometheus.exporter.unix "default" {
        include_exporter_metrics = true
        disable_collectors       = ["mdadm"]
      }
     
      // internal only
      prometheus.scrape "default" {
        targets = array.concat(
          prometheus.exporter.unix.default.targets,
          [{
            // Self-collect metrics
            job         = "alloy",
            __address__ = "127.0.0.1:12345",
          }],
        )
    
        forward_to = [
        // TODO: components to forward metrics to (like prometheus.remote_write or
        // prometheus.relabel).
        ]
      }
    
      // read from journal d
      loki.source.journal "read"  {
        forward_to    = [loki.write.grafanacloud.receiver]
        relabel_rules = loki.relabel.journal.rules
        labels        = {component = "loki.source.journal"}
      }
     
      // manipulate the labels
      loki.relabel "journal" {
        forward_to = []
    
        rule {
          source_labels = ["__journal__systemd_unit"]
          target_label  = "unit"
        }
      }
      
     
    
      // write to grafana cloud
      // Get the credentials from https://grafana.com/orgs/<your grafana>/stacks/<stack id>
      // Be sure to select logs:write scope as a minimum, and ensure the region for the access 
      // policy is correct Access policies are here https://grafana.com/orgs/<your grafana>/access-policies
      loki.write "grafanacloud" {
        endpoint {
          url = "https://logs-prod-<your log fqdn>.grafana.net/loki/api/v1/push"
     
          basic_auth {
            username = "<your logging user name>"
            password = "<your api key>"
          }
        }
      }

When all configured, 

      sudo systemctl restart alloy
      sudo systemctl status alloy

check local logs

      journalctl -t

check metrics

      curl http://localhost:12345/metrics | grep 'logs-prod-'



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


test after over