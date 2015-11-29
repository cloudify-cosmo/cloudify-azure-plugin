import sys, os, subprocess
from netaddr import *
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation


error_message="\nPlease enter a valid PRIVATE IP-ADDRESS network\nPrivate networks can use IP addresses anywhere in the following ranges: \n192.168.0.0 - 192.168.255.255 (65,536 IP addresses) \n172.16.0.0 - 172.31.255.255 (1,048,576 IP addresses) \n10.0.0.0 - 10.255.255.255 (16,777,216 IP addresses)\n"
correct_message="\nNetwork accepted\n"

def network_check(argv[1])
	user_network= argv[1]
	ip = IPNetwork(user_network)
	octate = user_network.split(".")
	network_valid=0
	if IPAddress(ip.ip).is_private():
		if octate[0]==str(192):
			if ip.prefixlen>=16:
				ctx.logger.info(correct_message)
				network_valid=1
			else:
				raise NonRecoverableError(error_message)
		if octate[0]==str(172):
			if ip.prefixlen>=20:
				ctx.logger.info(correct_message)
				network_valid=1
			else:
				raise NonRecoverableError(error_message)
		if octate[0]==str(10):
			if ip.prefixlen>=8:
				ctx.logger.info(correct_message)
				network_valid=1
			else:
				raise NonRecoverableError(error_message)
	else:
		raise NonRecoverableError(error_message)


	if network_valid==1:
		os.chdir("/root")
		network_address_file= open("user_network_address", 'w')
		network_address_file.write(user_network)       
		network_address_file.close()
		network_valid=0

network_check(argv[1])
