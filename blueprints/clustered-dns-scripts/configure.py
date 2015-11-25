import subprocess, os, sys
from netaddr import *
from reverseZone_naming import reverseZone_name
from azurecloudify import constants
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
curlybrace1="{"
curlybrace2="}"
zone_files_directory="/etc/bind/zones"


def configure_ipv4_mode():
	bind9_file="/etc/default/bind9"
	bind9_file_content=open(bind9_file,'w')
	bind9_file_content.write("# run resolvconf? \nRESOLVCONF=no \n \n# startup options bind9_filer the server \nOPTIONS=\"-4 -u bind\"")
	bind9_file_content.close

def options_file_configure(ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY]):	
	ip_address_of_server=ctx.instance.runtime_properties[constants.PRIVATE_IP_ADDRESS_KEY]
	options_file="/etc/bind/named.conf.options"
	options_file_content=open(options_file,'w')
	options_file_content.write("\noptions %s \n\t directory \"/var/cache/bind\"; \n\t recursion yes; \t \t # enables resursive queries \n\t allow-recursion %s any; %s; \t \t # allows recursive queries from \"any\" clients \n\t allow-recursion-on %s any; %s; \n\t listen-on %s %s; %s; \n\t allow-transfer %s none; %s; \t\t # disable zone transfers by default \n \n \t forwarders %s \n \t \t \t 8.8.8.8; \n \t \t \t 8.8.4.4;\n \t%s;\n%s;" % (curlybrace1, curlybrace1,curlybrace2,curlybrace1,curlybrace2,curlybrace1,ip_address_of_server, curlybrace2,curlybrace1,curlybrace2, curlybrace1,curlybrace2, curlybrace2))
	options_file_content.close()
	if (os.path.exists(zone_files_directory)):
		subprocess.call('rm -rf /etc/bind/zones', shell=True)
	os.mkdir(zone_files_directory)

def local_file_configure(argv[1]):
	domain_name= argv[1]
	reverse_zone_file_name,reverse_zone_name=reverseZone_name()
	local_file_path="/etc/bind/named.conf.local"
	local_file_path_content = open(local_file_path, 'w')
	local_file_path_content.write("zone \"%s\" %s \n\ttype master;  \n        file \"/etc/bind/zones/%s\";  \t  # zone file path \n        allow-transfer %s none; %s;\t   \n%s;\n \nzone \"%s\" %s \n\ttype master;  \n        file \"/etc/bind/zones/%s\";  \n        allow-transfer %s none; %s ;\t   \n%s;\n" %(domain_name, curlybrace1,"db."+domain_name, curlybrace1,curlybrace2,curlybrace2,reverse_zone_name, curlybrace1, reverse_zone_file_name,curlybrace1,curlybrace2,curlybrace2))
	local_file_path_content.close()



configure_ipv4_mode()
options_file_configure()
local_file_configure()	