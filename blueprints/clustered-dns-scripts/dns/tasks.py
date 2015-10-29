import subprocess, os, sys

curlybrace1="{"
curlybrace2="}"

def add_forwd_record():
	host_name_to_be_added= sys.argv[1]
	ip_addr_to_be_added= sys.argv[2]

	forwd_zone_file_path="/etc/bind/zones/db.cfy.org"
	forwd_zone_content = open(forwd_zone_file_path, 'a')
	forwd_zone_content.write("\n%s. \tIN \t A \t %s" % (host_name_to_be_added,ip_addr_to_be_added))       
	forwd_zone_content.close()
	subprocess.call("service bind9 reload", shell=True)

def add_rev_record():
	ip_addr_to_be_added= sys.argv[1]
	host_name_to_be_added= sys.argv[2]

	rev_zone_file_path="/etc/bind/zones/db.0"
	rev_zone_content = open(rev_zone_file_path, 'a')
	rev_zone_content.write("\n%s \t IN \t PTR \t %s" % (ip_addr_to_be_added,host_name_to_be_added))       
	rev_zone_content.close()
	subprocess.call("service bind9 reload", shell=True)

def main():
	add_rev_record()
	add_forwd_record()
