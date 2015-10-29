import subprocess, os, sys

curlybrace1="{"
curlybrace2="}"

def add_forwd_record():
	host_name_to_be_added= sys.argv[1]
	ip_addr_to_be_added= sys.argv[2]
	domain_name= sys.argv[3]
	zoneFile_name="db."+domain_name

	os.chdir("/etc/bind/zones")
	forwd_zone_content = open(zoneFile_name, 'a')
	forwd_zone_content.write("\n%s. \tIN \t A \t %s" % (host_name_to_be_added,ip_addr_to_be_added))       
	forwd_zone_content.close()
	subprocess.call("service bind9 reload",shell=True)

def main():
	add_forwd_record()


main()
