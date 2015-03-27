




def main():
	# print 'hello'
	a = raw_input()

	b = ''
	for i in range(len(a)):
		if i == 0 and a[i] == '9':
			b += a[i]
			continue
		if int(a[i])> 4:
			temp = 9 - int(a[i])
			b += str(temp)
		else:
			b += a[i]
	print b	

if __name__ == '__main__':
	main()