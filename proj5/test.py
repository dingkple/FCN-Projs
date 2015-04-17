
import time

al = []

for i in range(100000000):
    al.append(i)


t1 = time.time()
t2 = 0
t3 = 0

print 'finding first',
if 0 in al:
    t2 = time.time()
    print t2 - t1

print 'finding last',
if 100000000-1 in al:
    t3 = time.time()
    print t3 - t2