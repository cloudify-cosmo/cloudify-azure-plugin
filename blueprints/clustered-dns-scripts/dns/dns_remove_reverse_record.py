import subprocess, os, sys
from reverseZone_naming import reverseZone_name
from netaddr import *
zone_files_path="/etc/bind/zones"

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

def main():
	remove_reverse_record()


main()
