import threading
import time
from globalVar import *



class dataWarehouse:

	def __init__(self):
		self.x = 0
		self.y = 100
		self.sum = []


class myThread(threading.Thread):
	def __init__(self, threadID, name, counter, data):
		global threadLock
		self.data = data
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter
		self.num = 0


	def run(self):
		global threadLock
		while self.counter:
			threadLock.acquire()
			print '%d %s' % (self.counter, self.name)
			self.counter -= 1
			self.data.x += 1
			self.data.y -= 1
			s = str(self.data.x) + '\t' +str(self.data.y) + '\t' + self.name
			self.data.sum.append(s)
			threadLock.release()
			# time.sleep(1)


def print_time(threadName, delay, counter):
	while counter:
		time.sleep(delay)
		print '%s: %s' % (threadName, time.ctime(time.time()))
		counter -= 1


threadLock = threading.Lock()

threads = []

data = dataWarehouse()

thread1 = myThread(1, 'thread-1', 5, data)

thread2 = myThread(2, 'thread-2', 5, data)

thread3 = myThread(3, 'thread-3', 5, data)

thread1.start()

thread2.start()

thread3.start()

threads.append(thread1)
threads.append(thread2)
threads.append(thread3)

for t in threads:
	t.join()

for s in data.sum:
	print s

print 'exiting main'