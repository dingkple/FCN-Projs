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


while getopts "u:" arg
do
    case $arg in

        u) # username
            username=$OPTARG
            # echo "username:$OPTARG"
            ;;
        ?)
            echo "unkonw argument"
        exit 1
        ;;
        esac
done


for host in "${hostnames[@]}"
do
    echo "adding key " $host

    # scp ~/authorized_keys $username@$host 'mkdir ~/.ssh/'
    # ssh $username@$host "mkdir ~/.ssh"
    # ssh $username@$host "mkdir ~/.ssh"
    # scp ~/authorized_keys $username@$host:~/.ssh/
    ssh $username@$host "chmod -R 700 ~/.ssh"
done