import threading
import time
import requests
import logging
from flask import Flask
from pathlib import Path

from .source import use_all

__VERSION__ = "0.0.1"


class Proxy():
    def __init__(self, ip, port, protocol="http"):
        self.ip = ip
        self.port = port
        if not protocol:
            protocol = "http"
        self.protocol = protocol
        self.delay = float('inf')
        self.last_ping = None
        self.create = time.ctime(time.time())

    def ping(self):
        logging.debug("Ping {}".format(str(self)))
        start = time.time()
        try:
            proxy = {
                'http': '{}'.format(str(self)),
                'https': '{}'.format(str(self))
            }
            '''head 信息'''
            head = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
                                   AppleWebKit/537.36 (KHTML, like Gecko) \
                                   Chrome/50.0.2661.102 Safari/537.36',
                    'Connection': 'keep-alive'}
            requests.get('http://icanhazip.com', headers=head, proxies=proxy)
            delay = time.time() - start
        except Exception:
            delay = float('inf')

        self.last_ping = time.ctime(time.time())
        self.delay = delay
        return delay

    def __str__(self):
        return '{}://{}:{}'.format(self.protocol, self.ip, self.port)

    def status(self):
        return str(self) + "-> delay: {}, last_ping: {}".format(self.delay,
                                                                self.last_ping)


class Server(threading.Thread):
    def __init__(self, pool, host="localhost", port=5555, debug=False):
        threading.Thread.__init__(self)
        self._app = Flask("BorxyServer")
        self._pool = pool
        self._init_app(self._app)
        self.debug = debug
        self.host = host
        self.port = port

    def _init_app(self, app):
        @app.route("/")
        def index():
            proxies = self._pool.jsonify()
            return {"proxies": proxies, "count": len(proxies)}

        @app.route("/usable")
        def usable():
            proxies = self._pool.jsonify(usable=True)
            return {"proxies": proxies, "count": len(proxies)}

    def run(self):
        self._app.run(host=self.host, port=self.port, debug=self.debug)


class Pool:
    def __init__(self, name="Proxy Pool"):
        self.name = name
        self._proxies = []

    def __str__(self):
        return ";".join([str(p) for p in self._proxies])

    def __getitem__(self, key):
        return self._proxies[key]

    def __len__(self):
        return len(self._proxies)

    @property
    def proxies(self):
        return self._proxies

    def append(self, proxy):
        if str(proxy) not in [str(i) for i in self._proxies]:
            self._proxies.append(proxy)
        else:
            logging.info("Proxy : " + str(proxy) + " already exists")
        return len(self._proxies)

    def sort(self):
        self._proxies.sort(key=lambda a: a.delay)

    def status(self):
        unusable = [p for p in self._proxies if p.delay == float('inf')]
        return "{} => Total: {} | Usable: {} | Unusable: {}\
                ".format(self.name, len(self._proxies),
                         len(self._proxies) - len(unusable), len(unusable))

    def jsonify(self, n=None, usable=False):
        if not n or n > len(self._proxies):
            n = len(self._proxies)
        return [{"ip": p.ip,
                 "port": p.port,
                 "protocol": p.protocol,
                 "delay": p.delay,
                 "last_ping": p.last_ping,
                 "create": p.create
                 }
                for p in self._proxies[:n]
                if not usable or not p.delay == float('inf')]

    def clear(self):
        length = len(self._proxies)
        self._proxies = [p for p in self._proxies if p.ping() != float('inf')]
        logging.info("Drop {} unsuable proxies, current {}"
                     .format(length - len(self._proxies), len(self._proxies)))


class Broxy(threading.Thread):
    def __init__(self, size=9, patch=9, debug=False,
                 server=True, cache="~/.broxy"):
        logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
        threading.Thread.__init__(self)
        self._pool = Pool()
        self._server = Server(self._pool) if server else None
        self._sources = {}
        self._fetcher = None
        self._running = False
        self.size = size
        self.patch = patch
        self.wait = 0
        self.cache = cache

    def source(self, override=False):
        def decorator(f):
            if override or f.__name__ not in self._sources.keys():
                self._sources[f.__name__] = f
                logging.info("Source {} registered!".format(f.__name__))
            else:
                logging.info("Source {} is already exist!".format(f.__name__))
            return f
        return decorator

    def new_fetcher(self):
        fetchers = [source() for source in self._sources.values()]
        while len(fetchers) > 0:
            for fetcher in fetchers:
                try:
                    yield next(fetcher)
                except StopIteration:
                    fetchers.remove(fetcher)

    def fetch(self, n=1):
        proxies = []
        while len(proxies) < n:
            try:
                proxies.append(next(self._fetcher))
            except (TypeError, StopIteration):
                logging.info("Generating fetcher...")
                self._fetcher = self.new_fetcher()
        for proxy in proxies:
            proxy = Proxy(proxy['ip'], proxy['port'],
                          proxy['protocol'] if 'protocol' in proxy.keys()
                          else None)
            if proxy.ping() != float('inf'):
                self._pool.append(proxy)
                logging.info("Usable proxy: " + str(proxy))
            else:
                logging.debug("Unusable proxy: " + str(proxy))
        return proxies

    def __getitem__(self, key):
        return self._pool[key]

    def __len__(self):
        return len(self._pool)

    def status(self):
        return self._pool.status()

    def stop(self):
        self._running = False

    def __del__(self):
        self.stop()

    def run(self):
        if len(self._sources) == 0:
            logging.warn("No regidtered source! exit...")
            return
        if self._server:
            self._server.start()
        self._running = True
        while self._running:
            count = len(self)
            if len(self) < self.size:
                self.fetch(self.patch)
                time.sleep(count)
            else:
                self._pool.clear()
                logging.info(self.status())
                time.sleep(count * 3)


def main():
    print("Broxy!")
    broxy = Broxy(debug=True)

    @broxy.source()
    def localhost():
        yield {"ip": "172.22.192.1", "port": 1080, "protocol": "socks5"}
        yield {"ip": "172.22.192.1", "port": 1081}
        yield {"ip": "localhost", "port": 1080, "protocol": "socks5"}
        yield {"ip": "localhost", "port": 1081}
        yield {"ip": "localhost", "port": 4780}
        yield {"ip": "localhost", "port": 4781, "protocol": "socks5"}

    use_all(broxy)
    broxy.start()


if __name__ == "__main__":
    p = Path("~/.broxy")
