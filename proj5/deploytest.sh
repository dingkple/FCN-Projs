#! /bin/bash
# ./[deploy|run|stop]CDN -p <port> -o <origin> -n <name> -u <username> -i <keyfile>

./deployCDN -p 40019 -o ec2-52-4-98-110.compute-1.amazonaws.com -n cs5700cdn.example.com -u zhikai -i ~/.ssh/id_rsa

ssh -i ~/.ssh/id_rsa zhikai@cs5700cdnproject.ccs.neu.edu "cd ~/scripts/; chmod 700 dnsserver; nohup ./dnsserver -p 40019 -n cs5700cdn.example.com > /dev/null 2>&1 &"