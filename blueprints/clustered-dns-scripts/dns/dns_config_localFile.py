import subprocess, os, sys

curlybrace1="{"
curlybrace2="}"

def local_file_configure():
	domain_name= sys.argv[1]

	local_file_path="/etc/bind/named.conf.local"
	local_file_path_content = open(local_file_path, 'w')
	local_file_path_content.write("zone \"%s\" %s \n\ttype master;  \n        file \"/etc/bind/zones/%s\";  \t  # zone file path \n        allow-transfer %s none; %s;\t   \n%s;\n \nzone \"in-addr.arpa\" %s \n\ttype master;  \n        file \"/etc/bind/zones/db.0\";  \n        allow-transfer %s none; %s ;\t   \n%s;\n" %(domain_name, curlybrace1,"db."+domain_name, curlybrace1,curlybrace2,curlybrace2,curlybrace1, curlybrace1,curlybrace2,curlybrace2))
	local_file_path_content.close()


def main():
	local_file_configure()


main()
