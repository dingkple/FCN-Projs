import threading

global threadLock

"""

This class is to store the common-info for threads, including:
visited_urls: all the urls visited
url_stack: the urls waiting to be visited
secret_flag: the secret_flags already found
page_counter: the number of pages found now
flag_counter: the number of flags
is_flag_written: True iff any threads has written the flags on the disk
"""

class sharingInfo:

	def __init__(self):

		self.DATA_URL = 'http://cs5700sp15.ccs.neu.edu/'
		self.visited_urls = []
		self.url_stack = []
		self.secret_flag = {}
		self.page_counter = 0
		self.flag_counter = 0
		self.is_flag_written = False
