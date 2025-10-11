import time
import bme280
import logging
from meter_api import Collector, Reader
log = logging.getLogger(__name__)

class BME280Reader(Reader, Collector):
    def __init__(self, bus, address: int) -> None:
        self.bus = bus
        self.address = address
        self.update = 0
        self.data = None
        self.calibration_params = bme280.load_calibration_params(bus, address)
        self.run = True

    def read(self) -> None:
        log.debug(f'reading BME280')
        self.data = bme280.sample(self.bus, self.address, self.calibration_params)
        self.update = time.time()

    def collect(self, source) -> list[str]:
        if self.data == None:
            return []
        now = time.time()
        nowSeconds = int(now)
        metrics = []
        if self.data.temperature != None:
            metrics.append(f'temperature={self.data.temperature:.1f}')
        if self.data.humidity != None:
            metrics.append(f'humidity={self.data.humidity:.1f}')
        if self.data.pressure != None:
            metrics.append(f'pressure={self.data.pressure:.1f}')
        self.data = None
        if len(metrics) == 0:
            return []
        return [
            f'bme280,source={source} {",".join(metrics)} {nowSeconds}000000000'
        ]

if __name__ == '__main__':
    import smbus2

    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)-10s %(message)s',
                        level=logging.DEBUG)
    i2cbus = 1 #Default
    bus = smbus2.SMBus(i2cbus)
    bmeReader = BME280Reader(bus, 0x76)
    bmeReader.read()
    print( '\n'.join(bmeReader.collect("test")))


