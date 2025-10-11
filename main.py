import smbus2
import asyncio
import os
import signal
import faulthandler
import json

from argparse import ArgumentParser

from p8s_writer import P8sWriter
from os_meter import OsMeter
from w1_meter import OnewireTemp
from am2020_meter import AM2020
from bme280_meter import BME280Reader

from meter_api import ReaderTask, CollectorAggregate


import logging

log = logging.getLogger(__name__)



NAME = os.path.basename(__file__)
VERSION = '1.0'




async def main():

    parser = ArgumentParser(add_help=True)
    parser.add_argument('-d', '--debug', help='enable debug logging',
                        action='store_true')
    parser.add_argument('-c', '--config', help='configfile', action='append', default='config.json')
    parser.add_argument('-s', '--secrets', help='secrets', action='append', default='secrets.json')
    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s  %(levelname)s %(threadName)s [%(filename)s:%(lineno)s - %(funcName)10s()] %(name)-10s %(message)s',
                            level=(logging.DEBUG if args.debug else logging.INFO))


    log.info(f'{NAME} v{VERSION}')

    signal.signal(signal.SIGINT, lambda s, f: os._exit(1))
    faulthandler.register(signal.SIGUSR1)
    faulthandler.enable()

    '''with open(args.config) as stream:
        config = json.load(stream)'''
    with open(args.secrets) as stream:
        secrets = json.load(stream)


    i2cbus = 1 #Default
    address = 0x5C #AM2020 I2C Address
    bus = smbus2.SMBus(i2cbus)

    oneWire = OnewireTemp()
    am2020 = AM2020(bus, 0x5C)
    bmeReader = BME280Reader(bus, 0x76)

    i2cReaderTask = ReaderTask([am2020, bmeReader], 2)
    w1ReaderTask = ReaderTask([oneWire], 5)

    collectors = []



    collectors.append(oneWire)
    collectors.append(am2020)
    collectors.append(bmeReader)
    collectors.append(OsMeter())
    aggregate = CollectorAggregate(collectors)

    writer = P8sWriter('luna', aggregate,  secrets['p8s'], 120)
    await writer.run()


if __name__ == '__main__':
    asyncio.run(main())



'''
i = 1


while True:
    start = time.time()
    t, h, wakeTries, readTries = am2020.readTemperatureHumidity()
    temps = oneWire.read_temps()
    bmeData = bmeReader.read()
    end = time.time()
    c = end - start
    print(f"{i} t:{c:.3f}s ww:{wakeTries} rw:{readTries} Temperature:{t} °C Humidity:{h} %RH {temps} {bmeData}")
    i = i + 1
    time.sleep(5)
'''
