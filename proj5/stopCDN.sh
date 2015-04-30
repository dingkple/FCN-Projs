#! /bin/bash
hostnames=(ec2-52-0-73-113.compute-1.amazonaws.com
ec2-52-16-219-28.eu-west-1.compute.amazonaws.com
ec2-52-11-8-29.us-west-2.compute.amazonaws.com
ec2-52-8-12-101.us-west-1.compute.amazonaws.com
ec2-52-28-48-84.eu-central-1.compute.amazonaws.com
ec2-52-68-12-77.ap-northeast-1.compute.amazonaws.com
ec2-52-74-143-5.ap-southeast-1.compute.amazonaws.com
ec2-52-64-63-125.ap-southeast-2.compute.amazonaws.com
ec2-54-94-214-108.sa-east-1.compute.amazonaws.com)

while getopts "p:o:u:n:i:" arg
do
    case $arg in
        p) # Port
            # echo "port:$OPTARG"
            ;;
        o) # Origin server
            # echo "origin:$OPTARG"
            ;;
        u) # username
            username=$OPTARG
            # echo "username:$OPTARG"
            ;;
        n) # CDN-specific name
            # echo "name:$OPTARG"
            ;;
        i) #private key
            keyfile=$OPTARG
            # echo "keyfile:$OPTARG"
            ;;
        ?)
            echo "unkonw argument"
        exit 1
        ;;
        esac
done

for host in "${hostnames[@]}"
do
    echo 'Close ' $host
    ssh -i $keyfile $username@$host 'nohup killall python > /dev/null 2>&1 &'
    ssh -i $keyfile $username@$host  'rm -rf ~/scripts'
done

dnsserver=cs5700cdnproject.ccs.neu.edu
echo "Close " $dnsserver
ssh -i $keyfile $username@$dnsserver 'nohup killall python > /dev/null 2>&1 &'
ssh -i $keyfile $username@$dnsserver 'rm -rf ~/scripts'