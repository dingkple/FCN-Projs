from struct import unpack
import math
import socket
import threading
import urllib2
import urllib
from bs4 import BeautifulSoup as Soup
import urlparse
import random

MEASUREMENT_PORT = 55555


dic_ip_delay = {}

hostnames = ["ec2-52-0-73-113.compute-1.amazonaws.com",
            "ec2-52-16-219-28.eu-west-1.compute.amazonaws.com",
            "ec2-52-11-8-29.us-west-2.compute.amazonaws.com",
            "ec2-52-8-12-101.us-west-1.compute.amazonaws.com",
            "ec2-52-28-48-84.eu-central-1.compute.amazonaws.com",
            "ec2-52-68-12-77.ap-northeast-1.compute.amazonaws.com",
            "ec2-52-74-143-5.ap-southeast-1.compute.amazonaws.com",
            "ec2-52-64-63-125.ap-southeast-2.compute.amazonaws.com",
            "ec2-54-94-214-108.sa-east-1.compute.amazonaws.com"]



MAP = {'52.74.143.5': (1.293100, 13.855800),
     '52.16.219.28': (53.333100, -6.248900),
     '52.0.73.113': (39.043700, -77.487500),
     '52.68.12.77': (35.685000, 139.751400),
     '52.64.63.125': (-33.866600, 151.208200),
     '52.28.48.84': (50.116700, 8.683300),
     '54.94.214.108': (-23.547500, -46.636100),
     '52.11.8.29': (45.839900, -119.700600),
     '52.8.12.101': (37.339400, -121.895000)}

host_ip = ['52.74.143.5'
     '52.16.219.28'
     '52.0.73.113'
     '52.68.12.77'
     '52.64.63.125'
     '52.28.48.84'
     '54.94.214.108'
     '52.11.8.29'
     '52.8.12.101']

# def is_private(ip):
#     f = unpack('!I', socket.inet_pton(socket.AF_INET, ip))[0]
#     private_ips = (
#         [3232235520, 4294901760],  # 192.168.0.0, 255.255.0.0
#         [2130706432, 4278190080],  # 127.0.0.0,   255.0.0.0
#         [167772160, 4278190080],  # 10.0.0.0,    255.0.0.0
#         [2886729728, 4293918720],  # 172.16.0.0,  255.240.0.0
#     )
#     for ip in private_ips:
#         if f & ip[1] == ip[0]:
#             return True
#     return False


class ProbeThread(threading.Thread):
    def __init__(self, host, target, execute_lock):
        threading.Thread.__init__(self)
        self.host = host
        self.target = target
        self.lock = execute_lock

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ip = socket.gethostbyname(self.host)
        try:
            sock.connect((ip, MEASUREMENT_PORT))
            sock.sendall(self.target)
            latency = sock.recv(1024)
        except socket.error as e:
            # print '[Error]Connect Measurer' + str(e)
            latency = 'inf'
        finally:
            sock.close()

        # print '[DEBUG]IP: %s\tLatency:%s' % (ip, latency)
        with self.lock:
            dic_ip_delay.update({ip: float(latency)})

# probe replica server using active measurement
def probe_delay_actively(target_ip_addr):
    lock = threading.Lock()
    threads = []

    for i in range(len(hostnames)):
        t = ProbeThread(hostnames[i], target_ip_addr, lock)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    # print '[DEBUG]Sorted Replica Server:', dic_ip_delay
    return dic_ip_delay

# probe replica server using geo loc
def probe_delay_geo(target_ip_addr):
    def get_location(_ip):
        res = geo_ip_lookup(_ip)
        return float(res.get('Latitude:')), float(res.get('Longitude:'))

    def get_distance(target, src):
        return math.sqrt(reduce(lambda x, y: x + y,
                                map(lambda x, y: math.pow((x - y), 2), target, src), 0))

    distance = {}
    for ip in MAP.keys():
        distance[ip] = 0
    target_loc = get_location(target_ip_addr)
    for ip, loc in MAP.iteritems():
        distance[ip] = get_distance(target_loc, loc)

    # print '[DEBUG]Sorted Replica Server:', distance
    return distance


def select_best_ip(target_ip_addr):
    result = probe_delay_actively(target_ip_addr)
    if len(set(result.values())) <= 1:
        ri = random.randomInt(0, 8)
        return host_ip[ri]
        # result = probe_delay_geo(target_ip_addr)
    sorted_result = sorted(result.items(), key=lambda e: e[1])
    # print sorted_result[0][0]
    return sorted_result[0][0]

# def geo_ip_lookup(ip_address):
#     newurl = URL % ip_address 
#     # print newurl
#     doc = Soup(urllib.urlopen(newurl))
#     # print doc
#     data = []
#     table = doc.find('table', attrs={'class':'ipinfo'})
#     # print table 
#     rows = table.findAll('tr')
#     # print rows
#     res = {}
#     for row in rows:
#         # print row
#         res[row.th.string] = row.td.string
#     # print res
#     return res


# def test():
#     res = {}
#     for host in hostnames:
#         host = urlparse.urlparse("http://%s" % (host))
#         ip = socket.gethostbyname(host.hostname)
#         # print ip
#         r = geo_ip_lookup(ip)
#         res[r.get("IP:")] = (r.get('Latitude:'), r.get('Longitude:'))
#     return res


if __name__ == '__main__':
    print '[DEBUG]Select replica server:'
    # print test((37.7749, -122.419), (38.7749, -121.419))
    print test()

