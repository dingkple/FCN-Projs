#!/usr/bin/env python
"""
Author:     Zhikai Ding
For:        CS5700 Proj4 RAW_SOCKET
version:    "1.0"
"""



# checksum functions needed for calculation checksum
def checksum(msg):
    s = 0
    # loop taking 2 characters at a time
    # print len(msg)
    for i in range(0, len(msg), 2):
        # print i
        w = ord(msg[i]) + (ord(msg[i+1]) << 8 )
        s = s + w
    s = (s>>16) + (s & 0xffff);
    s = s + (s >> 16);
    #complement and mask to 4 byte short
    s = ~s & 0xffff
    return s


def incoming_tcp_checksum(msg):
    s = 0
    len_of_msg = len(msg)
    i = 0
    while(len_of_msg >= 2):
        s += ord(msg[i]) + (ord(msg[i+1]) << 8 )
        i += 2
        len_of_msg -= 2
    if len_of_msg > 0:
        s += ord(msg[-1])
    s = (s >> 16) + (s & 0xffff)
    s += s >> 16
    return ~s&0xffff

















