import subprocess, os, sys
from netaddr import *

def reverseZone_name():
	#os.chdir("/home/radhika/cloudify_dns/cloudify-azure-plugin/blueprints/clustered-dns-scripts/dns")
	os.chdir("/root")	
	network_address_file= open("user_network_address", 'r')
	network_address=network_address_file.read()       
	network_address_file.close()
	ip = IPNetwork(network_address)
	ip_address=IPAddress(ip.ip)
	octate = str(ip_address).split(".")
	if (int(ip.prefixlen)<16):
		reverse_zone_file_name="db."+octate[0]
		reverse_zone_name=octate[0]+"."+"in-addr.arpa"
	if (int(ip.prefixlen)>=16):
		if (int(ip.prefixlen)<24):
			reverse_zone_file_name="db."+octate[0]+"."+octate[1]
			reverse_zone_name=octate[1]+"."+octate[0]+"."+"in-addr.arpa"
		else:
			reverse_zone_file_name="db."+octate[0]+"."+octate[1]+"."+octate[2]
			reverse_zone_name=octate[2]+"."+octate[1]+"."+octate[0]+"."+"in-addr.arpa"
	return reverse_zone_file_name,reverse_zone_name
