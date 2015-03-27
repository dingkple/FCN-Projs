
def ptest():
	for i in range(4):
		for j in range(4):
			try:
				if i == 2:
					break
				print str(i) + " " + str(j)
				return 
			finally:
				print 'byebye ' + str(j) + " " + str(i)
		print 'ending ' + str(i)


ptest()