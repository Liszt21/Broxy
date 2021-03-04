import threading
import time
import requests
import logging
from flask import Flask

from .source import use_all

__VERSION__ = "0.0.1"

class Proxy():
    def __init__(self, ip, port, protocol= "http"):
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.delay = float('inf')
        self.last_ping = None

    def ping(self):
        logging.debug("Ping {}://{}:{}".format(self.protocol, self.ip,self.port))
        start = time.time()
        try:
            proxy = {
            'http': '{}://{}:{}'.format(self.protocol, self.ip,self.port),
            'https': '{}://{}:{}'.format(self.protocol, self.ip,self.port)
            }
            '''head 信息'''
            head = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36', 
                    'Connection': 'keep-alive'}
            p = requests.get('http://icanhazip.com', headers=head, proxies=proxy)
            delay = time.time() - start
        except Exception:
            logging.debug("Unusable proxy: {}".format(str(self)))
            delay = float('inf')

        self.last_ping = time.time()
        self.delay = delay
        return delay

    def __str__(self):
        return '{}://{}:{}'.format(self.protocol, self.ip,self.port)

    def status(self):
        return self.__str__() + "-> delay: {}, last_ping: {}".format(self.delay, self.last_ping)


class Server:
    def __init__(self, pool):
        self._app = Flask("BorxyServer")
        self._pool = pool
        self._init_app(self._app)
        self._thread = threading.Thread(target=self._app.run)

    def _init_app(self, app):
        @app.route("/")
        def index():
            proxies = self._pool.jsonify()
            return { "proxies" :proxies, "count": len(proxies) }

    def start(self):
        self._thread.start()


class Pool:
    def __init__(self, name="Proxy Pool"):
        self.name=name
        self._proxies = []

    def __str__(self):
        return ";".join([ str(p) for p in self._proxies ])

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
        return proxy.ping()

    def sort(self):
        self._proxies.sort(key=lambda a: a.delay)

    def status(self):
        unusable = [p for p in self._proxies if p.delay==-1]
        return "{} => Total: {} | Usable: {} | Unusable: {}".format(self.name, len(self._proxies), len(self._proxies) - len(unusable), len(unusable))

    def jsonify(self, n=None):
        l = len(self._proxies)
        if not n or n > l: n = l
        return [ {"ip":p.ip, "port":p.port, "protocol":p.protocol, "delay": p.delay, "last_ping": p.last_ping } for p in self._proxies[:n] ]

    def clear(self):
        pre = len(self)
        self._proxies = [ p for p in self._proxies if p.delay != float('inf') ]
        logging.info("Drop {} unsuable proxies".format(pre - len(self)))

class Broxy(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self._pool = Pool()
        self._sever = Server(self._pool)
        self._sources = {}
        self._fetcher = None
        self._running = False

    def source(self, override=False):
        def decorator(f):
            if override or not f.__name__ in self._sources.keys():
                self._sources[f.__name__] = f
                logging.info("Source {} registered!".format(f.__name__))
            else:
                logging.info("Source {} is already exist!".format(f.__name__))
            return f
        return decorator

    def new_fetcher(self):
        fetchers = [ source() for source in self._sources.values() ]
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
                logging.info("Regenerate fetcher...")
                self._fetcher = self.new_fetcher()
        for proxy in proxies:
            proxy = Proxy(proxy['ip'], proxy['port'], proxy['protocol'] if 'protocol' in proxy.keys() else None)
            delay = self._pool.append(proxy)
            if delay != float('inf'):
                logging.info("Usable proxy: " + str(proxy))
        return proxies
    
    def __getitem__(self, key):
        return self._pool[key]

    def __len__(self):
        return len(self._pool)

    def status(self):
        return "Pool   => total: {0}, usable: {1}\nSources=> total: {2}".format(
            len(self._pool), 0, len(self._sources)
        )

    def stop(self):
        self._running = False

    def __del__(self):
        self.stop()

    def run(self):
        if len(self._sources) == 0:
            return
        self._running= True
        while self._running:
            while len(self._pool) < 3:
                self.fetch(3)
            self._pool.clear()
            time.sleep(9)


def main():
    logging.basicConfig(level=logging.INFO)
    print("Broxy!")
    broxy = Broxy()

    @broxy.source()
    def localhost():
        yield {"ip": "localhost", "port": 1080, "protocol": "socks5"}
        yield {"ip": "localhost", "port": 1081}
        yield {"ip": "localhost", "port": 4780}
        yield {"ip": "localhost", "port": 4781, "protocol": "socks5"}

    use_all(broxy)
    broxy.run()

if __name__ == "__main__":
    print("main")
    main()
