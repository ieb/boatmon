import logging
import asyncio


log = logging.getLogger(__name__)

class Reader:
    def read(self) -> None:
        pass

class Collector:
    def collect(self, source: str) -> list[str]:
        return []

class CollectorAggregate(Collector):
    def __init__(self, collectors) -> None:
        self.collectors = collectors

    def collect(self, source: str) -> list[str]:
        aggregate = []
        for collector in self.collectors:
            aggregate.extend(collector.collect(source))
        return aggregate



class ReaderTask:
    def __init__(self, readers: list[Reader], delay: float) -> None:
        self.readers = readers
        self.delay = delay
        self.run = True
        self.task = asyncio.create_task(self.read())


    async def read(self) -> None:
        while(self.run):
            log.debug(f'start read')
            for reader in self.readers:
                reader.read()
            log.debug(f'sleep')
            await asyncio.sleep(self.delay)

