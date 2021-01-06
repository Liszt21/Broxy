import threading
import time
from flask import Flask

__VERSION__ = "0.0.1"


class Server:
    def __init__(self, pool, debug=False):
        self._app = Flask("BorxyServer")
        self._pool = pool

    def init_app(self, app):
        @app.route("/")
        def index():
            return {"usable": 0, "proxies": []}


class Pool:
    def __init__(self, debug=False):
        self._proxies = {}
        self._sources = {}
        self._enabled = []
        self._fetcher = None
        self._getter = None
        self._tester = None
        self.debug = debug

    def register(self, name, fn):
        # TODO check fn before register
        self._sources[name] = fn
        if self.debug:
            print("Register source : ", name)

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
                    if self.debug:
                        print(proxy)
                    yield proxy
            rest = time.time() - start - span
            if rest > 0:
                span += 621
                time.sleep(rest)
            else:
                span -= 207

    def _ping(self):
        pass

    def tojson(self):
        pass

    def fetch(self):
        pass

    def get(self):
        pass


class Broxy:
    def __init__(self, debug=False):
        self._pool = Pool(debug)
        self._sever = Server(self._pool, debug)

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

    broxy.start()
    time.sleep(2)
    print(broxy.get(3))
    broxy.stop()


if __name__ == "__main__":
    main()
