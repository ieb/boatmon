import time
import logging
log = logging.getLogger(__name__)

from meter_api import Reader, Collector

class AM2020(Reader, Collector):

    def __init__(self, bus, address: int) -> None:
        self.bus = bus
        self.address = address
        self.humidity = 200
        self.temperature = 200
        self.update = 0
        self.wakeTries = 0
        self.tries = 0
        self.run = True



    def _wakeSensor(self):
        while True:
            try:
                self.wakeTries = self.wakeTries + 1
                self.bus.write_i2c_block_data(self.address, 0x00, [])
                break
            except IOError as e:
                log.debug(e, stack_info=True, exc_info=True)
        time.sleep(0.003)


    def read(self):

        log.debug(f'reading AM2020')
        self._wakeSensor()
        while True:
            try:
                self.tries = self.tries + 1
                self.bus.write_i2c_block_data(self.address, 0x03, [0x00, 0x04])
                break
            except IOError as e:
                log.debug(e, stack_info=True, exc_info=True)

        time.sleep(0.015)
        try:
            block = self.bus.read_i2c_block_data(self.address, 0, 6)
        except IOError as e:
            log.debug(e, stack_info=True, exc_info=True)
            return

        self.humidity = float(block[2] << 8 | block[3]) / 10
        self.temperature = float(block[4] << 8 | block[5]) / 10
        self.update = time.time()

    def collect(self, source) -> list[str]:
        now = time.time()
        nowSeconds = int(now)
        metrics = []
        if self.temperature < 200:
            metrics.append(f'temperature={self.temperature:.1f}')
        if self.humidity < 200:
            metrics.append(f'humidity={self.humidity:.1f}')
        self.temperature = 200
        self.humidity = 200
        if len(metrics) == 0:
            return []
        return [
            f'am2020,source={source} {",".join(metrics)} {nowSeconds}000000000'
        ]


if __name__ == '__main__':
    import smbus2
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)-10s %(message)s',
                        level=logging.DEBUG)
    i2cbus = 1 #Default
    bus = smbus2.SMBus(i2cbus)
    am2020 = AM2020(bus, 0x5C)
    am2020.read()
    print( '\n'.join(am2020.collect("test")))


