import commands


command_str = 'dig @localhost -p 50011 cs5700cdn.example.com'

count = 0
for i in range(1000):
    res = commands.getoutput(command_str)
    count += 1
    print count