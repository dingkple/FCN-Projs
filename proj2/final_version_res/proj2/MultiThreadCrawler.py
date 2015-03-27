import socket
import urlparse
import os
import re
import time
import htmlentitydefs
import threading
from Myurllib import Myurllib
from socket_http import 


class crawlerTread (threading.Thread):

	def __init__(self, threadID, name, counter):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.counter = counter


	def run(self):
		
