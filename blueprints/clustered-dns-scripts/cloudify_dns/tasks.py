import subprocess, os, sys
from reverseZone_naming import reverseZone_name
from netaddr import *
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
zone_files_path="/etc/bind/zones"
curlybrace1="{"
curlybrace2="}"

def add_forward_record():
	host_name_to_be_added= sys.argv[1]
	ip_address_to_be_added= sys.argv[2]
	domain_name= sys.argv[3]
	record_valid=1
	
	os.chdir("/root")
	network_address_file= open("user_network_address", 'r')
	network_address=network_address_file.read()       
	network_address_file.close()
	ip = IPNetwork(network_address)
	ip_address=IPAddress(ip_address_to_be_added)
	if ip_address_to_be_added in IPNetwork(network_address):
		zoneFile_name="db."+domain_name
		os.chdir("/etc/bind/zones")

		readFiles = open(zoneFile_name, 'r')
		forward_zone_file_content = readFiles.read()
		readFiles.close()
		
		if host_name_to_be_added in forward_zone_file_content:
			record_valid=0
			print "\nHostname is already entered in the database.\nSorry! Cannot enter duplicate records.\nPlease enter a different record\n"

		if ip_address_to_be_added in forward_zone_file_content:
			record_valid=0
			print "\nIP address is already entered in the database.\nSorry! Cannot enter duplicate records.\nPlease enter a different record\n"

		if record_valid==1:
			forward_zone_content = open(zoneFile_name, 'a')
			forward_zone_content.write("\n%s. \tIN \t A \t %s" % (host_name_to_be_added,ip_address_to_be_added))       
			forward_zone_content.close()
			print "\nThe forward record that you entered has been added!\n"
			subprocess.call("service bind9 reload",shell=True)
	else:
		print ("\nSorry, cannot accept this record! \nPlease enter an IP address within your entered zone! \nYour entered zone is: %s\n" % (IPNetwork(network_address))) 

def add_reverse_record():
	ip_address_to_be_added= sys.argv[1]
	host_name_to_be_added= sys.argv[2]
	record_valid=1
	ip_valid=0
	os.chdir("/root")
	network_address_file= open("user_network_address", 'r')
	network_address=network_address_file.read()       
	network_address_file.close()
	ip = IPNetwork(network_address)
	prefix_length=int(ip.prefixlen)
	ip_address=IPAddress(ip_address_to_be_added)

	if ip_address_to_be_added in IPNetwork(network_address):
		ip_valid=1
		reverse_zone_file_name,reverse_zone_name=reverseZone_name()
		os.chdir(zone_files_path)
		readFiles = open(reverse_zone_file_name, 'r')
		forward_zone_file_content = readFiles.read()
		readFiles.close()
		if host_name_to_be_added in forward_zone_file_content:
			record_valid=0
			print "\nHostname is already entered in the database.\nSorry! Cannot enter duplicate records.\nPlease enter a different record\n"
			
		if record_valid==1:
			octate = str(ip_address).split(".")
			if prefix_length<16:
				reverse_record=octate[3]+"."+octate[2]+"."+octate[1]
			elif prefix_length>=16 and prefix_length<24:
				reverse_record=octate[3]+"."+octate[2]
			else:
				reverse_record=octate[3]
		
			if reverse_record in forward_zone_file_content:
				record_valid=0
				print "\nIP address is already entered in the database.\nSorry! Cannot enter duplicate records.\nPlease enter a different record\n"

	else:
		print ("\nSorry, cannot accept this record! \nPlease enter an IP address within your entered zone! \nYour entered zone is: %s\n" % (IPNetwork(network_address))) 

	if ip_valid==1:
		if record_valid==1:
			reverse_zone_file_name,reverse_zone_name=reverseZone_name()
			os.chdir(zone_files_path)
			reverse_zone_file_path=reverse_zone_file_name
			reverse_zone_content = open(reverse_zone_file_path, 'a')
			reverse_zone_content.write("\n%s \t IN \t PTR \t %s" % (reverse_record,host_name_to_be_added))       
			reverse_zone_content.close()
			print "\nThe reverse record that you entered has been added!\n"
			subprocess.call("service bind9 reload",shell=True)

def remove_forward_record():
	host_name_to_be_removed= sys.argv[1]
	domain_name= sys.argv[2]

	os.chdir(zone_files_path)
	forward_zone_file_name="{0}{1}".format("db.",domain_name)

	readFiles = open(forward_zone_file_name,'r')
	forward_zone_file_content = readFiles.read()
	readFiles.close()

	readFiles = open(forward_zone_file_name,'r')
	lines = readFiles.readlines()
	readFiles.close()
	
	if host_name_to_be_removed in forward_zone_file_content:
		file_content = open(forward_zone_file_name,'w')
		for line in lines:
			if not host_name_to_be_removed in line:
				file_content.write(line)		
		file_content.close()
		print "\nThe forward record that you entered has been removed!\n"
	else:
		print "\nThe record you wanted to remove is already absent in the database!\n"		

def remove_reverse_record():
	host_name_to_be_removed= sys.argv[1]

	reverse_zone_file_name,reverse_zone_name=reverseZone_name()
	os.chdir(zone_files_path)
	readFiles = open(reverse_zone_file_name,'r')
	reverse_zone_file_content = readFiles.read()
	readFiles.close()

	readFiles = open(reverse_zone_file_name,'r')
	lines = readFiles.readlines()
	readFiles.close()
	
	if host_name_to_be_removed in reverse_zone_file_content:
		file_content = open(reverse_zone_file_name,'w')
		for line in lines:
			if not host_name_to_be_removed in line:
				file_content.write(line)		
		file_content.close()
		print "\nThe reverse record that you entered has been removed!\n"
	else:
		print "\nThe record you wanted to remove is already absent in the database!\n"



