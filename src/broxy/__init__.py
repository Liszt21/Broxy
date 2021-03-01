import threading
import time
import requests
import logging
from flask import Flask

__VERSION__ = "0.0.1"

class Proxy():
    def __init__(self, ip, port, protocol= "http"):
        self.ip = ip
        self.port = port
        self.protocol = protocol
        self.delay = -1
        self.last_ping = None
        self.ping()

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
        except Exception as err:
            logging.debug(err)
            delay = -1

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

    def init_app(self, app):
        @app.route("/")
        def index():
            return {"usable": 0, "proxies": []}


class Pool:
    def __init__(self):
        self._proxies = {}
        self._enabled = []
        self._fetcher = None
        self._getter = None
        self._tester = None

    def register(self, name, fn):
        # TODO check fn before register
        self._sources[name] = fn
        logging.debug("Register source : ", name)

    def enable(self, name):
        if name not in self._sources.keys():
            pass
        elif name in self._enabled:
            pass
        else:
            self._enabled.append(name)
            self.setFetcher(self._enabled)

    def disable(self, name):
        if name in self._enabled:
            pass
        elif name not in self._sources.key():
            pass
        else:
            self._enabled.pop(self._enabled.index(name))
            self.setFetcher(self._enabled)

    def genFetcher(self):
        span = 621
        while True:
            start = time.time()
            for name in self._enabled:
                proxies = self._sources[name].fn()
                for proxy in proxies:
                    # TODO check proxy before yield
                    logging.debug(proxy)
                    yield proxy
            rest = time.time() - start - span
            if rest > 0:
                span += 621
                time.sleep(rest)
            else:
                span -= 207

    def tojson(self):
        pass

    def fetch(self):
        pass

    def get(self):
        pass


class Broxy:
    def __init__(self):
        self._pool = Pool()
        self._sever = Server(self._pool)
        self._sources = {}
        self._thread = None

    def source(self, override=False):
        def decorator(f):
            if override or not f.__name__ in self._sources.keys():
                self._sources[f.__name__] = f
                self._fetcher = self.fetch()
            else:
                print("Source {} is already exist!".format(f.__name__))
            return f
        return decorator

    def fetch(self):
        for source in self._sources.values():
            for proxy in source():
                yield proxy

    def get(self, num=1):
        l = len(self._pool)
        return self._pool[: num if num < l else -1]

    def status(self):
        return "Pool   => total: {0}, usable: {1}\nSources=> total: {2}".format(
            len(self._pool), 0, len(self._sources)
        )

    def verify(self, p):
        return False

    def start(self):
        self._thread = threading.Thread(target=self.run)
        self._thread.start()
        self._app.run()

    def stop(self):
        if not self._thread:
            return
        stop_thread(self._thread)
        self._thread = None
        self._app.stop()
        print("Thread stopped")

    def __del__(self):
        self.stop()

    def run(self):
        if len(self._sources) == 0:
            return
        while len(self._pool) < 10:
            self._pool.append(next(self._fetcher))
            time.sleep(1)


def main():
    print("Broxy!")
    broxy = Broxy()

    @broxy.source()
    def test():
        for i in range(1234, 65536):
            yield {"ip": "1.2.3.4", "port": i, "protocol": "http"}

    @broxy.source()
    def localhost():
        yield {"ip": "localhost", "port": 1081}
        yield {"ip": "localhost", "port": 1080, "protocol": "socks5"}
        yield {"ip": "localhost", "port": 4780}
        yield {"ip": "localhost", "port": 4781}

def test():
    logging.basicConfig(level=logging.DEBUG)
    # proxy = Proxy("localhost", 1081)
    proxy = Proxy("192.168.48.1", 1081)
    print(proxy.status())

if __name__ == "__main__":
    # main()
    test()
