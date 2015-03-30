#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""

from IP import *
from struct import *
import random
import socket
import urlparse
import sys
import time
import re


MSS = 1450

MAX_WIN_SIZE = 30000

DEBUG = True
# DEBUG = False



class raw_TCP:
    """TCP implementation by raw sockets"""
    def __init__(self):
        self.ip = raw_ip()
        self.client_seq = random.randint(0, 65536)
        self.client_ack = self.client_seq
        self.base_seq = self.client_seq
        self.client_ack = 0
        self.server_seq = 0
        self.dest_ip = ''
        self.sent_packets = {}
        self.data_buffer = ' '
        self.cwd_size = 1
        self.port = random.randint(30000, 60000)
        self.shake_finished = False
        self.last_recv_time = 0
        self.data_recved = {}
        self.result = ''
        self.pkt_added = []
        self.chunked = False
        self.content_length = -1
        self.htmlStared = False



    def _decode_tcp_header(self, packet, mapRet):
        # mapRet = {}
        mapRet['src_port'] = (int(ord(packet[0])<<8)) + (int(ord(packet[1])))
        mapRet['dst_port'] = (int(ord(packet[2])<<8)) + (int(ord(packet[3])))
        mapRet['seq_num'] = (long(ord(packet[4])<<24)) + (long(ord(packet[5])<<16))
        mapRet['seq_num'] = mapRet.get('seq_num') + (long(ord(packet[6])<<8)) + (long(ord(packet[7])))
        mapRet['ack_num'] = (long(ord(packet[8])<<24)) + (long(ord(packet[9])<<16))
        mapRet['ack_num'] = mapRet.get('ack_num') + (long(ord(packet[10])<<8)) + (long(ord(packet[11])))
        # mapRet['ack'] = mapRet.get('ack_num') - SEQ_NUM
        mapRet['data_offset'] = (int(ord(packet[12])<<4))
        mapRet['ns'] = (int(ord(packet[12]) & int('00000001', 2)))
        mapRet['cwr'] = (int(ord(packet[13]) & int('10000000', 2)))>>7
        mapRet['ece'] = (int(ord(packet[13]) & int('01000000', 2)))>>6
        mapRet['urg'] = (int(ord(packet[13]) & int('00100000', 2)))>>5
        mapRet['ack'] = (int(ord(packet[13]) & int('00010000', 2)))>>4
        mapRet['psh'] = (int(ord(packet[13]) & int('00001000', 2)))>>3
        mapRet['rst'] = (int(ord(packet[13]) & int('00000100', 2)))>>2
        mapRet['syn'] = (int(ord(packet[13]) & int('00000010', 2)))>>1
        mapRet['fin'] = (int(ord(packet[13]) & int('00000001', 2)))
        mapRet['window_size'] = (int(ord(packet[14])<<8)) + (int(ord(packet[15])))
        mapRet['checksum'] = (int(ord(packet[16])<<8)) + (int(ord(packet[17])))
        mapRet['urg_pointer'] = (int(ord(packet[18])<<8)) + (int(ord(packet[19])))
        mapRet['data'] = packet[20:]
        return mapRet


    def _construct_flags(self, ftype):
        tcp_rst = 0
        tcp_urg = 0
        tcp_fin = 0
        tcp_syn = 0
        tcp_psh = 0
        tcp_ack = 0
        if ftype == 'syn':
            tcp_syn = 1
        elif ftype == 'ack_syn' or ftype == 'ack': 
            tcp_ack = 1
        elif ftype == 'send':
            tcp_ack = 1
            tcp_psh = 1
        elif ftype == 'fin_ack':
            tcp_fin = 1
            tcp_ack = 1
        elif ftype == 'ack_fin':
            tcp_ack = 1
        tcp_flags = tcp_fin + (tcp_syn << 1) + (tcp_rst << 2) + (tcp_psh <<3) + (tcp_ack << 4) + (tcp_urg << 5)
        return tcp_flags



    def _construct_tcp_header(self, user_data, ftype, seq = -1, ack = -1):
        if seq == -1 or ack == -1:
            seq = self.client_seq
            ack = self.server_seq
        tcp_doff = 5    #4 bit field, size of tcp header, 5 * 4 = 20 bytes
        tcp_dest = 80   # destination port
        tcp_window = socket.htons(20000)    #   maximum allowed window size
        tcp_check = 0
        tcp_urg_ptr = 0
        tcp_flags = self._construct_flags(ftype)
        tcp_seq = seq
        tcp_ack_seq = ack
        tcp_check = 0
        tcp_urg_ptr = 0
        tcp_offset_res = (tcp_doff << 4) + 0
        tcp_header = pack('!HHLLBBHHH', self.port, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, 
            tcp_flags,  tcp_window, tcp_check, tcp_urg_ptr)
        source_address = socket.inet_aton(self.ip.ethernet.src_ip_addr)
        dest_address = socket.inet_aton(self.dest_ip)
        placeholder = 0
        protocol = socket.IPPROTO_TCP
        tcp_length = len(tcp_header) + len(user_data)
        psh = pack('!4s4sBBH', source_address, dest_address , placeholder , protocol , tcp_length)
        psh = psh + tcp_header + user_data;
        if DEBUG:
            print psh
        tcp_check = checksum(psh)
        tcp_header = pack('!HHLLBBH' , self.port, tcp_dest, tcp_seq, tcp_ack_seq, tcp_offset_res, tcp_flags,  tcp_window) 
        tcp_header += pack('H' , tcp_check) + pack('!H' , tcp_urg_ptr)
        packet = tcp_header + user_data
        self.client_seq += len(user_data)
        if ftype == 'send':
            self.sent_packets[self.client_seq] = [time.time(), user_data, self.client_seq]
        return packet


    def _get_user_data(self):
        cur_seq = self.client_seq - self.base_seq
        acked = self.client_ack - self.base_seq
        available_size = min([self.cwd_size * MSS - acked, len(self.data_buffer) - cur_seq, MAX_WIN_SIZE, MSS])
        if DEBUG:
            print cur_seq,
        if DEBUG:
            print available_size
        current_data = self.data_buffer[cur_seq: cur_seq + available_size]
        res = ''
        if len(current_data) > MSS:
            res = current_data[:MSS]
            current_data = current_data[MSS:]
        else:
            res = current_data + ''
            current_data = ''
        if len(res) % 2 != 0:
            res += ' '
        if DEBUG:
            print 'length: ' + str(len(res))
        return res

    def _send_packet(self, ftype, retransmit = -1):
        packet = ''
        if retransmit != -1:
            print 'start retransmit: ' + str(retransmit)
            packet = self._construct_tcp_header(
                self.sent_packets.get(retransmit)[1],
                'ack',
                self.sent_packets.get(retransmit)[2],
                retransmit)
            self.ip.sent_packets(self.dest_ip, packet)

        elif ftype == 'syn':
            if DEBUG:
                print 'send syn'
            packet = self._construct_tcp_header('', 'syn')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'ack_syn':
            packet = self._construct_tcp_header('', 'ack_syn')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'ack':
            data = self._get_user_data()
            if DEBUG:
                print data
            if len(data) > 0:
                packet = self._construct_tcp_header(data, 'send')
            else:
                packet = self._construct_tcp_header(data, 'ack')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'fin_ack':
            if DEBUG:
                print 'finishing: '
            packet = self._construct_tcp_header('', 'fin_ack')
            self.ip.send_packet(self.dest_ip, packet)
        elif ftype == 'ack_fin':
            if DEBUG:
                print 'ack_fin'
            packet = self._construct_tcp_header('', 'ack_fin')
            self.ip.send_packet(self.dest_ip, packet)


    def _recv_packet(self):
        now = time.time()
        while True:
            cur = time.time()
            if cur - now > 180:
                if DEBUG:
                    print 'tcp error'
                sys.exit()
            if cur - now % 10 > 5:
                if DEBUG:
                    print 'tcp no data for %ds' % (cur - now)
                # continue
            mapRet, resp_packet = self.ip.receive_packet(self.dest_ip)
            if DEBUG:
                print 'got ip packet'
            if len(resp_packet) > 0:
                self.last_recv_time = time.time()
                response = self._decode_tcp_header(resp_packet, mapRet)
                if DEBUG:
                    print 'dst_port' + ' ' + str(response.get('dst_port'))
                if DEBUG:
                    print 'src_port' + ' ' + str(self.port)
                if response.get('dst_port') == self.port:
                    if DEBUG:
                        print 'got right port'
                        self.client_ack = response.get('ack_num')
                        self.server_seq = response.get('seq_num')
                    return response
                else:
                    if DEBUG:
                        print 'port err ' + str(response.get('src_port')) + str(self.port)


    def _check_retransmit(self):
        if DEBUG:
            print 'check for retransmit',
            print len(self.sent_packets),
            print self.sent_packets
        for pkt in self.sent_packets.keys():
            now = time.time()
            if now - self.sent_packets.get(pkt)[0] > 60:
                if DEBUG:
                    print 'preparing retransmit'
                self._send_packet('ack', pkt)
        if DEBUG:
            print 'end retransmit'


    def _hand_shake(self):
        response = {}
        self._send_packet('syn')
        sec = time.time()
        while True:
            cur_sec = time.time()
            if cur_sec - sec > 180:
                if DEBUG:
                    print 'timeout'
                sys.exit()
            response = self._recv_packet()
            if DEBUG:
                print response.get('ack')
            if DEBUG:
                print response.get('syn')
            if response.get('ack') == 1 and response.get('syn') == 1:
                if DEBUG:
                    print 'get syn_ack'
                self.client_seq = response.get('ack_num')
                self.server_seq = response.get('seq_num')
                self.server_seq += 1
                self._send_packet('ack_syn')
                self.shake_finished = True
                break
        

    def _start_communicating(self):
        self._hand_shake()
        if self.shake_finished:
            self._send_packet('ack')
            now = time.time()
            while True:
                self._check_retransmit()
                response = self._recv_packet()
                if DEBUG:
                    print 'begin processing'
                if response.get('ack') == 1 and response.get('psh') == 1:
                    ack_num = response.get('ack_num')
                    if ack_num in self.sent_packets.keys():
                        del self.sent_packets[ack_num]
                    seq = response.get('seq_num')
                    if not seq in self.data_recved.keys():
                        self.data_recved[response.get('seq_num')] = response.get('data')
                    else:
                        if DEBUG:
                            print 'dup pkt'
                    self._ack(response)
                elif response.get('ack') == 1 and response.get('fin') == 1:
                    if DEBUG:
                        print 'tearing down'
                    self.server_seq = response.get('seq_num')
                    self.client_ack = response.get('ack_num')
                    self._start_tear_down()
                    break
                if (len(self.result) == self.content_length \
                        or self.result.endswith('0\r\n\r\n')) \
                    and self.htmlStared:
                        if DEBUG:
                            print self.result.endswith('0\r\n\r\n')
                            print len(self.result)
                            print 'Time To End:'
                            print 'content_length',
                            print self.content_length
                            print 'Transfer-Encoding',
                            print self.result[-5:]
                        self._init_tear_down()
                        return self.get_result(), self.chunked
            return self.get_result(), self.chunked
        else:
            if DEBUG:
                print 'hand shake failed'

    def get_result(self):
        # data = ''
        # for k in sorted(self.data_recved.keys()):
        #     data += self.data_recved.get(k)
        data = self.result
        cnt = data.find('\r\n\r\n')
        if '200' not in data[:cnt]:
            print 'can not get the web page'
            sys.eixt(0)
        data = data[cnt+4:]
        if DEBUG:
            print data
        return data

    def _start_tear_down(self):
        if DEBUG:
            print self.client_ack
        self.server_seq += 1
        if DEBUG:
            print self.client_ack,
        if DEBUG:
            print self.server_seq
        self._send_packet('fin_ack')


    def _ack(self, response):
        seq = response.get('seq_num')
        if DEBUG:
            print seq
        # if DEBUG:
            # print ' '.join(map(str, self.data_recved.keys()))
        while seq in self.data_recved.keys():
            if seq not in self.pkt_added:
                self.result += self.data_recved.get(seq)
                self.pkt_added.append(seq)
                self.server_seq += len(self.data_recved.get(seq))
                seq = self.server_seq
            if self.content_length == -1 and not self.chunked:
                if 'Content-Length: ' in self.result:
                    if DEBUG:
                        print 'matching length: '
                        print self.result
                    cl = re.search(r'[.*?|\s]*Content-Length: ([\d]*)[\s\s].*?', self.result)
                    if DEBUG:
                        print cl
                        print cl.groups(0)
                    self.content_length = int(cl.groups(1)[0])
                    if DEBUG:
                        print self.content_length
                elif 'Transfer-Encoding' in self.result:
                    self.chunked = True
                if DEBUG:
                    print 'content_length',
                    print self.content_length
                    print 'Transfer-Encoding',
                    print str(self.chunked)
                    print 'recv_data_len:',
                    print len(self.result)
            if not self.htmlStared and '<!DOCTYPE' in self.result:
                self.htmlStared = True
            self._send_packet('ack')


    def _init_tear_down(self):
        print 'init tear down'
        self._send_packet('fin_ack')
        sec = time.time()
        while True:
            print 'waiting to fin'
            cur_sec = time.time()
            if cur_sec - sec > 180:
                if DEBUG:
                    print 'timeout'
                sys.exit()
            response = self._recv_packet()
            if response.get('fin') == 1 and response.get('ack') == 1:
                self.client_seq += 1
                self.server_seq += 1
                self._send_packet('ack_fin')
                print 'ack_fin sent'
                break




    def send(self, url, data):
        try:
            self.dest_ip = socket.gethostbyname(url.hostname)
            self.data_buffer += data
            if DEBUG:
                print 'started:',
                print self.dest_ip
                print self.data_buffer
            return self._start_communicating()
        except:
            print 'url error'
            sys.exit(0)


def get_http_header(url):
    # global USER_DATA

    url = urlparse.urlparse(url)
    path = url.path
    if path == "":
        path = "/"
    header = 'GET %s HTTP/1.1\r\n' % (path)
    # header += 'Host: %s\r\n' % (url.hostname)
    header += 'Connection: keep-alive\r\n'
    header += 'Cache-Control: max-age=0\r\n'
    header += 'Accept: text/html,application/xhtmlxml,application/xml;q=0.9,image/webp,*/*;q=0.8\r\n'
    header += 'Accept-Language: zh-CN,zh;q=0.8,en-US;q=0.6,en;q=0.4,zh-TW;q=0.2\r\n'
    header += "\r\n"
    if DEBUG:
        print 'header length: ' + str(len(header)) 
    if DEBUG:
        print header
    return header

if __name__ == '__main__':
    dest_ip = socket.gethostbyname('david.choffnes.com')
    t = raw_TCP(dest_ip)
    # t._hand_shake()
    data = get_http_header('http://david.choffnes.com')
    t.data_buffer += data
    t._start_communicating()





        