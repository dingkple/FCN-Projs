import urllib



def test():
    url_count = 0
    while True:
        url = 'http://localhost:50011/wiki/Special:Random'
        response = urllib.urlopen(url)
        data = response.read()
        url_count += 1
        print url_count

test()
