
f = open('index.html', 'r')


data = ''.join(f.readlines())
pos = 0
chunked = ''
now = 0
while pos < len(data):
    pos = data.find('\r\n', now)
    # print da`ta[pos-4:pos+4]
    try:
        chunked += data[pos+2 : pos + 2 + int(data[now:pos], 16)]
        now = pos + int(data[now:pos], 16) + 4
    except ValueError:
        break
    # print chunked

print chunked