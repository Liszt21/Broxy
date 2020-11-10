__VERSION__ = "0.0.1"

class Broxy():
    def __init__(self):
        self._pool = []
        self._sources = {}
        self._statistic = {}
        self._fetcher = None

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
        pass

    def status(self):
        return "Pool   => total: {0}, usable: {1}\nSources=> total: {2}".format(len(self._pool), 0, len(self._sources))

    def verify(self, p):
        return False

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

    print(next(broxy._fetcher))
    print(next(broxy._fetcher))
    print(next(broxy._fetcher))

if __name__ == "__main__":
    main()
