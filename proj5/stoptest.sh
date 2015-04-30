#! /bin/bash
# ./[deploy|run|stop]CDN -p <port> -o <origin> -n <name> -u <username> -i <keyfile>

./stopCDN.sh -p 40019 -o ec2-52-4-98-110.compute-1.amazonaws.com -n cs5700cdn.example.com -u zhikai -i ~/.ssh/id_rsa