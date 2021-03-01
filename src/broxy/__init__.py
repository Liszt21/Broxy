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
        self.delay = float('inf')
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
        except Exception as error:
            logging.debug(error)
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

    def _init_app(self, app):
        @app.route("/")
        def index():
            proxies = self._pool.jsonify()
            return { "proxies" :proxies, "count": len(proxies) }

    def start(self):
        self._app.run()


class Pool:
    def __init__(self, name="Proxy Pool"):
        self.name=name
        self._proxies = []

    def __str__(self):
        return ";".join([ str(p) for p in self._proxies ])

    def __getitem__(self, index):
        l = len(self._proxies)
        if -l < index < l:
            return self._proxies[index]

    def __len__(self):
        return len(self._proxies)

    @property
    def proxies(self):
        return self._proxies

    def append(self, ip, port, protocol="http"):
        proxy = Proxy(ip, port, protocol)
        if str(proxy) not in [str(i) for i in self._proxies]:
            self._proxies.append(proxy)
        else:
            logging.info("Proxy : ", proxy, " already exists")

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
        self._proxies = [ p for p in self._proxies if p.delay != float('inf') ]

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
    # print(proxy.status())
    pool = Pool()
    pool.append("192.168.48.1", 1081)
    pool.append("192.168.48.1", 1080)
    # print(pool.status())
    # print(pool)
    # pool.sort()
    # pool.clear()
    # print(pool)
    
    print(pool.proxies)
    print(len(pool))
    
    # server = Server(pool)

    # server.start()

if __name__ == "__main__":
    # main()
    test()
