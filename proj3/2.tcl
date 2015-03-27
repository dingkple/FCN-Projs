



#Define a 'finish' procedure
proc finish {} {
        global ns nf
        $ns flush-trace
        #Close the NAM trace file
        close $nf
        #Execute NAM on the trace file
        # exec nam out.nam &
        exit 0
}




#Create a simulator object
set ns [new Simulator]

#Open the NAM trace file
# set rate [lindex $::argv 0]
set cbrrate [expr [lindex $::argv 0]]
set filename [format "out%02d.nam" $cbrrate]
puts $filename
set nf [open $filename w]
$ns namtrace-all $nf

#Define different colors for data flows (for NAM)
$ns color 1 Blue
$ns color 2 Red

#Create four nodes
set n1 [$ns node]
set n2 [$ns node]
set n3 [$ns node]
set n4 [$ns node]
set n5 [$ns node]
set n6 [$ns node]

#Create links between the nodes
$ns duplex-link $n1 $n2 10Mb 10ms DropTail
$ns duplex-link $n2 $n3 10Mb 10ms DropTail
$ns duplex-link $n5 $n2 10Mb 10ms DropTail
$ns duplex-link $n3 $n4 10Mb 10ms DropTail
$ns duplex-link $n3 $n6 10Mb 10ms DropTail




#Set Queue Size of link (n2-n3) to 10
$ns queue-limit $n2 $n3 100

#Give node position (for NAM)
$ns duplex-link-op $n1 $n2 orient right-down
$ns duplex-link-op $n5 $n2 orient right-up
$ns duplex-link-op $n2 $n3 orient right
$ns duplex-link-op $n3 $n4 orient right-up
$ns duplex-link-op $n3 $n6 orient right-down

#Monitor the queue for link (n2-n3). (for NAM)
$ns duplex-link-op $n2 $n3 queuePos 0.5


#Setup a TCP connection
set tcp1 [new Agent/TCP/Reno]
$tcp1 set class_ 2
$ns attach-agent $n1 $tcp1
set tcp2 [new Agent/TCPSink]
$ns attach-agent $n4 $tcp2
$ns connect $tcp1 $tcp2
$tcp1 set fid_ 3
$tcp2 set fid_ 4

# Setup a FTP over TCP connection
set ftp [new Application/FTP]
$ftp attach-agent $tcp1
$ftp set type_ FTP

set tcp3 [new Agent/TCP/Reno]
$tcp3 set class_ 2
$ns attach-agent $n5 $tcp3
set tcp4 [new Agent/TCPSink]
$ns attach-agent $n6 $tcp4
$ns connect $tcp3 $tcp4
$tcp3 set fid_ 5
$tcp4 set fid_ 6

# Setup a FTP over TCP connection
set ftp1 [new Application/FTP]
$ftp1 attach-agent $tcp1
$ftp1 set type_ FTP

# Setup a FTP over TCP connection
set ftp2 [new Application/FTP]
$ftp2 attach-agent $tcp3
$ftp2 set type_ FTP


#Setup a UDP connection
set udp [new Agent/UDP]
$ns attach-agent $n2 $udp
set null [new Agent/Null]
$ns attach-agent $n3 $null
$ns connect $udp $null
$udp set fid_ 2

#Setup a CBR over UDP connection
set cbr [new Application/Traffic/CBR]
$cbr attach-agent $udp
$cbr set type_ CBR
$cbr set packet_size_ 1000
$cbr set rate_ [expr $cbrrate * 0.3 * 1000000]
$cbr set random_ false


#Schedule events for the CBR and FTP agents
$ns at 0.1 "$cbr start"
$ns at 1.0 "$ftp1 start"
$ns at 1.0 "$ftp2 start"
$ns at 10.0 "$ftp1 stop"
$ns at 10.0 "$ftp2 stop"
$ns at 13.0 "$cbr stop"

#Detach tcp and sink agents (not really necessary)
$ns at 10 "$ns detach-agent $n1 $tcp1 ; $ns detach-agent $n4 $tcp2"
$ns at 10 "$ns detach-agent $n5 $tcp3 ; $ns detach-agent $n6 $tcp4"

#Call the finish procedure after 5 seconds of simulation time
$ns at 13.0 "finish"

#Print CBR packet size and interval
puts "CBR packet size = [$cbr set packet_size_]"
puts "CBR interval = [$cbr set interval_]"

#Run the simulation
$ns run

