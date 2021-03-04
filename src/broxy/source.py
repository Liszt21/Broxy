import requests
from bs4 import BeautifulSoup

def use_kuaidaili(broxy):
    @broxy.source()
    def kuaidaili():
        base_url = "https://www.kuaidaili.com/free"
        for page in range(100):
            for section in ['inha', 'intr']:
                url = "{}/{}/{}".format(base_url, section, page + 1)
                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')
                for table in soup.find_all("table"):
                    for tr in table.find_all('tr')[1:]:
                        item = [i for i in tr.stripped_strings]
                        yield {'ip': item[0], "port": item[1], "protocol": item[3]}


def use_all(broxy):
    use_kuaidaili(broxy)


if __name__ == "__main__":
    url = "https://www.kuaidaili.com/free/inha/1"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    for table in soup.find_all("table"):
        for tr in table.find_all('tr')[1:]:
            item = [i for i in tr.stripped_strings]
            print({'ip': item[0], "port": item[1], "protocol": item[3]})
