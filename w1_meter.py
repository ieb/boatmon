import time
import os
import glob
from meter_api import Reader, Collector

import logging
log = logging.getLogger(__name__)



class OnewireTemp(Reader, Collector):
    def __init__(self) -> None:
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
        self.temperatures = {}

    def _read_temp_raw(self, device_file: str)  -> list[str]:
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def read(self) -> None:
        log.debug(f'reading OneWire')
        base_dir = '/sys/bus/w1/devices/'
        device_folders = glob.glob(base_dir + '28*')
        for device_folder in device_folders:
            device_name = device_folder.split('/')[-1]
            device_file = device_folder + '/w1_slave'

            lines = self._read_temp_raw(device_file)
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self._read_temp_raw(device_file)
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]

                self.temperatures[device_name] = float(temp_string) / 1000.0

    def collect(self, source) -> list[str]:
        now = time.time()
        nowSeconds = int(now)
        metrics = []
        for key,value in self.temperatures.items():
            if isinstance(value, (int, float)):
                metrics.append(f'{key}={value:.1f}')
        self.temperatures.clear()
        if len(metrics) == 0:
            return []
        return [
            f'w1temps,source={source} {",".join(metrics)} {nowSeconds}000000000'
        ]

if __name__ == '__main__':

    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)-10s %(message)s',
                        level=logging.DEBUG)
    oneWire = OnewireTemp()
    oneWire.read()
    print( '\n'.join(oneWire.collect("test")))




