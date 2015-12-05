import sys, os, subprocess
from netaddr import *

user_network= sys.argv[1]
ip = IPNetwork(user_network)
octate = user_network.split(".")
network_valid=0
if IPAddress(ip.ip).is_private():
	if octate[0]==str(192):
		if ip.prefixlen>=16:
			print "\nNetwork accepted\n"
			network_valid=1
		else:
			print "\nPlease enter a valid PRIVATE IP-ADDRESS network\nPrivate networks can use IP addresses anywhere in the following ranges: \n192.168.0.0 - 192.168.255.255 (65,536 IP addresses) \n172.16.0.0 - 172.31.255.255 (1,048,576 IP addresses) \n10.0.0.0 - 10.255.255.255 (16,777,216 IP addresses)\n"
	if octate[0]==str(172):
		if ip.prefixlen>=20:
			print "\nNetwork accepted\n"
			network_valid=1
		else:
			print "\nPlease enter a valid PRIVATE IP-ADDRESS network\nPrivate networks can use IP addresses anywhere in the following ranges: \n192.168.0.0 - 192.168.255.255 (65,536 IP addresses) \n172.16.0.0 - 172.31.255.255 (1,048,576 IP addresses) \n10.0.0.0 - 10.255.255.255 (16,777,216 IP addresses)\n"
	if octate[0]==str(10):
		if ip.prefixlen>=8:
			print "\nNetwork accepted\n"
			network_valid=1
		else:
			print "\nPlease enter a valid PRIVATE IP-ADDRESS network\nPrivate networks can use IP addresses anywhere in the following ranges: \n192.168.0.0 - 192.168.255.255 (65,536 IP addresses) \n172.16.0.0 - 172.31.255.255 (1,048,576 IP addresses) \n10.0.0.0 - 10.255.255.255 (16,777,216 IP addresses)\n"
else:
	print "\nPlease enter a valid PRIVATE IP-ADDRESS network\nPrivate networks can use IP addresses anywhere in the following ranges: \n192.168.0.0 - 192.168.255.255 (65,536 IP addresses) \n172.16.0.0 - 172.31.255.255 (1,048,576 IP addresses) \n10.0.0.0 - 10.255.255.255 (16,777,216 IP addresses)\n"


if network_valid==1:
	os.chdir("/root")
	network_address_file= open("user_network_address", 'w')
	network_address_file.write(user_network)       
	network_address_file.close()
	network_valid=0


