import asyncio
import aiohttp
import os
import signal
import faulthandler
import json
import subprocess
from asyncio.subprocess import PIPE, STDOUT
import time

from argparse import ArgumentParser



import logging

log = logging.getLogger(__name__)



NAME = os.path.basename(__file__)
VERSION = subprocess.run(["git", "rev-parse",  "HEAD"], capture_output=True, text=True).stdout.strip()



class StreamJournalLogs:
    def __init__(self, source, version, config, debug) -> None:
        self.lines = [
        ]
        self.debug = debug
        self.url = config['url']
        self.userId = config['userId']
        self.apiKey = config['apiKey']
        self.source = source
        self.version = version
        self.startTime = time.time()
        log.debug(f'Starting at {self.startTime}')
        self.lastTimeStamp = str(int(float(self.startTime*1000000000)))

    async def sendLines(self):
        payload = {
            'streams': [{
                "stream": { 
                    "source": self.source,
                },
                "values": self.lines,
            }]
        }
        log.debug(f'payload {payload}')
        if self.debug:
            self.lines.clear()
            return
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url,
                         headers = {
                           'Content-Type': 'application/json',
                           'Authorization': f'Bearer {self.userId}:{self.apiKey}'
                         },
                         json=payload) as resp:
                            log.debug(f'sent {resp.status}')
                            if resp.status == 204:
                                pass
                            else:
                                log.debug(payload)
                                log.debug(f'loki < {await resp.json()}')
                            self.lines.clear()

    def appendMessage(self, message):
        if message != None:
            parts = message.strip().split(" ",1)
            log.debug(parts)
            try:
                messageTime = float(parts[0])
                if messageTime < self.startTime:
                    # skip messages older than 30s before starting
                    # this ensures that the journal does not replay on a restart due to the read only root
                    # and allows for any delay in restart of the service
                    log.debug(f'skip {message}') 
                    return
                parts[0] = str(int(float(parts[0])*1000000000))
                self.lastTimeStamp = parts[0]
            except:
                parts[0] = self.lastTimeStamp
                log.debug('parse fail')
            self.lines.append(parts)

    async def streamLines(self):

        process = await asyncio.create_subprocess_exec(
            "/usr/bin/journalctl", "-o","short-unix", "-f", "--cursor-file=toloki",
            stdout=PIPE, stderr=STDOUT)
        message = None
        while True:
            try:
                line = await asyncio.wait_for(process.stdout.readline(), 10)
                if not line:
                    break
                # 1760282333.487648 boatmon systemd[1]: Started boatmon-ota.service - Boatmon OTA Update.
                # there may be continuation lines which start with a blank space.
                line = line.decode('utf-8')
                if line.startswith(' '):
                    # continuation, append to the message, if there is a current message
                    # otherwise drop until a timestamp is present
                    if message != None:
                        message = message + line
                        log.debug(f'Appended continuation {message}')
                else:
                    # next line, process the
                    self.appendMessage(message)
                    # start the next message
                    message = line
                    # send the lines if more than 10
                    if len(self.lines) > 10:
                        log.info(f'writing lines {len(self.lines)}')
                        await self.sendLines()
            except asyncio.TimeoutError:
                # no update after 10s
                # append the current message and send if there are mode
                self.appendMessage(message)
                message = None
                if len(self.lines) > 0:
                    log.debug(f'timeout flush lines {len(self.lines)}')
                    await self.sendLines()



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

    with open(args.secrets) as stream:
        secrets = json.load(stream)

    writer = StreamJournalLogs('luna', VERSION, secrets['loki'], args.debug)
    await writer.streamLines()


if __name__ == '__main__':
    asyncio.run(main())

