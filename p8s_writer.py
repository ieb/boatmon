
import aiohttp
import asyncio
import time
import logging
import traceback
log = logging.getLogger(__name__)
import asyncio


from meter_api import Collector

class P8SMetricsMeter(Collector):
    def __init__(self):
        self.metrics = {
            'p8s.sent': 0,
            'p8s.exception': 0,
            'p8s.fail': 0,
            'p8s.ok': 0,
        }

    def inc(self, key):
        try:
            self.metrics[key] = self.metrics[key]+1
        except:
            self.metrics[key] = 1
    def collect(self, source):
        now = time.time()
        nowSeconds = int(now)
        metrics = []
        for fieldName, value in self.metrics.items():
            metrics.append(f'{fieldName}={value}')
        return [ f've_p8s,source={source} {",".join(metrics)} {nowSeconds}000000000' ]

 

class P8sWriter:

    def __init__(self, source, collector, config: dict, delay: float):
        self.collector = collector
        self.source = source
        self.url = config['url']
        self.userId = config['userId']
        self.apiKey = config['apiKey']
        self.metrics = P8SMetricsMeter()
        self.debug = 0
        self.delay = delay
        self.running = False

    async def run(self):
        self.running = True
        while(self.running):
            start = time.time()
            await self.update()
            elapsed = self.delay - (time.time() - start)
            if elapsed < 0:
                elapsed = 1
            await asyncio.sleep(elapsed)


    async def update(self):
        log.debug('starting update')
        try:
            status = []
            payload = self.collector.collect(self.source)
            payload.extend(self.metrics.collect(self.source))
            body = "\n".join(payload)
            try:
                if self.debug > 0:
                    log.info(f'p8s < {body}')


                async with aiohttp.ClientSession() as session:
                    async with session.post(self.url,
                         headers = {
                           'Content-Type': 'text/plain',
                           'Authorization': f'Bearer {self.userId}:{self.apiKey}'
                         },
                        data=str(body)) as resp:
                            log.debug(f'sent {resp.status}')
                            self.metrics.inc('p8s.sent')
                            if resp.status == 204:
                                self.metrics.inc('p8s.ok')
                                if self.debug > 0:
                                    log.info(f'p8s < {resp.status} {await resp.text()}')
                            else:
                                self.metrics.inc('p8s.fail')
                                log.info(body)
                                log.info(f'p8s < {await resp.json()}')
            except Exception as err:
                log.error(f'Update failed Exception')
                self.metrics.inc('p8s.exception')
                status.append('failed collection')
                traceback.print_exc()
            if len(status) > 0:
                log.error(status)
        except:
            traceback.print_exc()            
            log.error(f'Update failed')
        return True
