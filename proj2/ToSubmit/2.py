import sys

def get_bul(pts, cos, gx, gy):
	buls = {}
	for co in cos:
		if co[0] - gx == 0:
			newl = sys.maxint
		else:
			newl = (1.0 * co[1] - gy) / (co[0] - gx)
		if buls.has_key(newl):
			buls[newl] = buls[newl] + 1
		else:
			buls[newl] = 1
	return len(buls)





def main():
	# print 'hello'ø
	n = raw_input()
	n = n.split()
	pts = n[0]
	gx = int(n[1])
	gy = int(n[2])
	cos = []
	for i in range(int(pts)):
		co = raw_input()
		co = co.split()
		co[0] = int(co[0])
		co[1] = int(co[1])
 		cos.append(co)
 	print get_bul(pts, cos, gx, gy)

if __name__ == '__main__':
	main()