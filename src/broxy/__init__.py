__VERSION__ = "0.0.1"

def main():
    print("Broxy!")

class Broxy():
    def __init__(self):
        self._pool = []
        self._sources = {}
        self._statistic = {}

    def source(self, override=False):
        def decorator(f):
            if override or not f.__name__ in self._sources.keys():
                self._sources[f.__name__] = f
            else:
                print("Source {} is already exist!".format(f.__name__))
            return f
        return decorator

    def fetch(self):
        pass

    def get(self,num=1):
        pass

    def status(self):
        return "Pool   => total: {0}, usable: {1}\nSources=> total: {2}".format(len(self._pool), 0, len(self._sources))

    def verify(self, p):
        return False

if __name__ == "__main__":
    broxy = Broxy()

    @broxy.source()
    def test():
        return 1

    @broxy.source()
    def test():
        return 2

    print(broxy.status())

