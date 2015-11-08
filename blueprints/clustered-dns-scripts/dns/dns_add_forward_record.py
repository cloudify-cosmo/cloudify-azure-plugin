import subprocess, os, sys
from reverseZone_naming import reverseZone_name
from netaddr import *

curlybrace1="{"
curlybrace2="}"

def add_forwd_record():
	host_name_to_be_added= sys.argv[1]
	ip_address_to_be_added= sys.argv[2]
	domain_name= sys.argv[3]

	
	os.chdir("/root")
	network_address_file= open("user_network_address", 'r')
	network_address=network_address_file.read()       
	network_address_file.close()
	ip = IPNetwork(network_address)
	ip_address=IPAddress(ip_address_to_be_added)
	if ip_address_to_be_added in IPNetwork(network_address):
		zoneFile_name="db."+domain_name
		os.chdir("/etc/bind/zones")
		forward_zone_content = open(zoneFile_name, 'a')
		forward_zone_content.write("\n%s. \tIN \t A \t %s" % (host_name_to_be_added,ip_address_to_be_added))       
		forward_zone_content.close()
		subprocess.call("service bind9 reload",shell=True)
	else:
		print ("\nSorry, cannot accept this record! \nPlease enter an IP address within your entered zone! \nYour entered zone is: %s\n" % (IPNetwork(network_address))) 
		

def main():
	add_forwd_record()


main()
