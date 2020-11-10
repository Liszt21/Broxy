import threading
import time
import inspect
import ctypes
from flask import Flask

__VERSION__ = "0.0.1"

def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")
 
 
def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)

class Broxy():
    def __init__(self):
        self._pool = []
        self._sources = {}
        self._statistic = {}
        self._fetcher = None
        self._sever = None
        self._thread = None
        self._app = self.getApp()

    def getApp(self):
        app = Flask("Broxy")

        @app.route('/')
        def index():
            return "Broxy"

        @app.route('/pool')
        def pool():
            return { i:self._pool[i] for i in range(len(self._pool)) }

        return app

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
            
    def get(self,num=1):
        l = len(self._pool)
        return self._pool[:num if num < l else -1]

    def status(self):
        return "Pool   => total: {0}, usable: {1}\nSources=> total: {2}".format(len(self._pool), 0, len(self._sources))

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
        while(len(self._pool) < 10):
            self._pool.append(next(self._fetcher))
            time.sleep(1);

def main():
    print("Broxy!")
    broxy = Broxy()

    @broxy.source()
    def test():
        for i in range(1234, 65536):
            yield {
                "ip": "1.2.3.4",
                "port": i,
                "protocol": "http"
            }

    broxy.start()
    time.sleep(2)
    print(broxy.get(3))
    broxy.stop()

if __name__ == "__main__":
    main()
