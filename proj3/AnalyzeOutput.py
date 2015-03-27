#!/bin/python
import os



def cal_tcp_res(filename, source, desti, result):
    tcpres = {}
    totalloss = 0
    totalsend = 0
    path = os.getcwd()
    path += "/severside/Documents/"
    # f = open(path + filename, 'r')
    f = open(filename, 'r')
    lines = f.readlines()
    src = '-s ' + str(source)
    dst = '-d ' + str(desti)
    acksrc = '-s ' + str(desti)
    ackdst = '-d ' + str(source)
    if source == 0:
        aa = '3'
    else:
        aa = '5'
    for l in lines:
        if 'tcp' in l or 'ack' in l:
            if ((l[0] == '+' and  src in l) or (l[0] == 'r' and dst in l) or 
                (l[0] == '+' and  acksrc in l) or (l[0] == 'r' and ackdst in l) or
                l[0] == 'd' ):
                res = l.split('-x')
                tcpseq = res[1].split()[2]
                if tcpseq not in tcpres.keys():
                    tcpres[tcpseq] = [[], [], [], [], []]
                if 'tcp' in res[0] or 'ack' in res[0]:
                    flag = 0
                    if 'ack' in res[0]:
                        flag = 2
                    if l[0] == '+':
                        tcpres[tcpseq][flag].append(res)
                    elif l[0] == 'r':
                        totalsend += 1
                        tcpres[tcpseq][flag+1].append(res)
                    elif l[0] == 'd' and res[0].split()[12] == aa:
                        totalloss += 1
                        totalsend += 1
                        tcpres[tcpseq][4].append(res)
                        tcpres[tcpseq][flag].pop()
    # for k in sorted(tcpres.keys()):
    #     for kk in tcpres.get(k):
    #         print kk
    # print len(tcpres.get(k))
    tput = cal_throughput(tcpres)
    ltc = cal_latency(tcpres)
    if totalsend != 0:
        lrt = float(totalloss) / totalsend
    else:
        lrt = 0
    rst = [tput, ltc, lrt]
    print rst
    result.append(rst)

def get_packet_size(l):
    res = int(l[0].split()[10])
    # print res
    return res

def get_time(l):
    return float(l[0].split()[2])

def cal_throughput(a_tcpres):
    tghp = 0
    for seq in a_tcpres.keys():
        for sp in a_tcpres.get(seq)[1]:
            tghp += get_packet_size(sp)
        for sp in a_tcpres.get(seq)[3]:
            tghp += get_packet_size(sp)
    return tghp

def cal_latency(a_tcpres):
    totaltime = 0
    num = 0
    for seq in a_tcpres.keys():
        ar = a_tcpres.get(seq)
        for i in range(len(ar[0])):
            totaltime += get_time(ar[1][i]) - get_time(ar[0][i])
        for i in range(len(ar[2])):
            totaltime += get_time(ar[3][i]) - get_time(ar[2][i])
        num = num + len(ar[0]) + len(ar[2])
    if num != 0:
        return totaltime / num
    else:
        return -1

def get_all_result():
    res03 = []
    res45 = []
    # for i in range(0, 40):
    #     astr = "out%02d.nam" % (i)
    #     print i,
    #     cal_tcp_res(astr, 0 , 3, res03)
    #     print i,
    #     cal_tcp_res(astr, 4 , 5, res45)
    
    # print result


get_all_result()





