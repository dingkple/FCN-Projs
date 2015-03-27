import sys

class Solution:
    # @return a tuple, (index1, index2)
    def findMin(self, num):
        low = 0
        high = len(num)-1
        mid = 0
        while low < high:
            mid = (low + high) / 2
            if num[mid] > num[high]:
                low = mid + 1
            else:
                high = mid
        return num[low]


s = Solution()

print s.findMin([4,5,6,7,9, 10,-1, 0,1,2])