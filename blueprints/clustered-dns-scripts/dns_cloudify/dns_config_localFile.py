import subprocess, os, sys
from netaddr import *
from reverseZone_naming import reverseZone_name
curlybrace1="{"
curlybrace2="}"

def local_file_configure():
	domain_name= sys.argv[1]
	reverse_zone_file_name,reverse_zone_name=reverseZone_name()
	local_file_path="/etc/bind/named.conf.local"
	local_file_path_content = open(local_file_path, 'w')
	local_file_path_content.write("zone \"%s\" %s \n\ttype master;  \n        file \"/etc/bind/zones/%s\";  \t  # zone file path \n        allow-transfer %s none; %s;\t   \n%s;\n \nzone \"%s\" %s \n\ttype master;  \n        file \"/etc/bind/zones/%s\";  \n        allow-transfer %s none; %s ;\t   \n%s;\n" %(domain_name, curlybrace1,"db."+domain_name, curlybrace1,curlybrace2,curlybrace2,reverse_zone_name, curlybrace1, reverse_zone_file_name,curlybrace1,curlybrace2,curlybrace2))
	local_file_path_content.close()


def main():
	local_file_configure()

main()
