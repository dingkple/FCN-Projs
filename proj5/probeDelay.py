import commands
import socket
import SocketServer
import time


MEASUREMENT_PORT = 55555


# extract delay from ping -c
def get_latency(ip_address):
    cmd = "scamper -c 'ping -c 1' -i %s |awk 'NR==2 {print $7}'|cut -d '=' -f 2" % (ip_address)
    res = commands.getoutput(cmd)
    if not res:
        res = 'inf'
    return res


class MeasureHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        target_ip = self.request.recv(1024).strip()
        print '[DEBUG]Client address: %s' % target_ip
        delay = get_latency(target_ip)
        print '[DEBUG]Latency: %s' % delay
        self.request.sendall(delay)


class MeasurementServer:
    def __init__(self, port=MEASUREMENT_PORT):
        self.port = port

    def start(self):
        server = SocketServer.TCPServer(('', self.port), MeasureHandler)
        server.serve_forever()


if __name__ == '__main__':
    measure_server = MeasurementServer()
    measure_server.start()