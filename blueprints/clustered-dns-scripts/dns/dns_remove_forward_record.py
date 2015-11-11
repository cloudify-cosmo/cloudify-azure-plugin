import subprocess, os, sys
from reverseZone_naming import reverseZone_name
from netaddr import *

def remove_forward_record():
	host_name_to_be_removed= sys.argv[1]
	domain_name= sys.argv[2]

	os.chdir("/etc/bind/zones")
	forward_zone_file_name="db."+domain_name

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

def main():
	remove_forward_record()


main()
