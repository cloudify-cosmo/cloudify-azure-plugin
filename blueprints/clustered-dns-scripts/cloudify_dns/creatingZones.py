import subprocess,os, sys
from reverseZone_naming import reverseZone_name
from azurecloudify import constants
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from cloudify.decorators import operation
zone_files_path="/etc/bind/zones"


def creating_forward_zone(argv[1], argv[2]):
	domain_name= argv[1]
	ipaddr_nameServer= argv[2]
	old_file="/etc/bind/db.local"
	os.chdir(zone_files_path)
	new_zone_file="{0}{1}".format("db.",domain_name)
	subprocess.call("cp /etc/bind/db.local new_zone_file",shell=True)
	
	old_file_content=open(old_file,'r')
	text_in_oldFile=old_file_content.read()
	old_file_content.close()

	new_zone_file_content=open(new_zone_file,'w')
	text_updated=text_in_oldFile.replace("localhost.",domain_name+".")
	text_modified=text_updated.replace("root.localhost.","admin."+domain_name+".")
	new_zone_file_content.write(text_modified)
	new_zone_file_content.close()

	# delete last 3 lines

	readFiles = open(new_zone_file,'r')
	lines = readFiles.readlines()
	readFiles.close()

	file_content = open(new_zone_file,'w')
	file_content.writelines([item for item in lines[:-3]])
	file_content.close()

	# Add few lines

	zoneFile_content = open(new_zone_file, 'a')
	zoneFile_content.write("\n \t IN \t NS \t %s   \n%s \t IN \t A \t %s  \n"% ("ns."+domain_name+".","ns."+domain_name+".", ipaddr_nameServer))        
	zoneFile_content.close()
	print "\nThe forward zone is created and is now ready to accept your records!\nYou can add forward records any time!\n"


def creating_reverse_zone(argv[1]):
	domain_name= argv[1]
	old_file="/etc/bind/db.127"
	
	old_file_content=open(old_file,'r')
	text_in_oldFile=old_file_content.read()
	old_file_content.close()
	text_updated=text_in_oldFile.replace("localhost.",domain_name+".")
	text_modified=text_updated.replace("root.localhost.","admin."+domain_name+".")

	reverse_zone_file_name,reverse_zone_name=reverseZone_name()
	os.chdir(zone_files_path)
	new_zone_file_content=open(reverse_zone_file_name,'w')
	new_zone_file_content.write(text_modified)
	new_zone_file_content.close()

	# delete last 2 lines

	readFiles = open(reverse_zone_file_name,'r')
	lines = readFiles.readlines()
	readFiles.close()

	file_content = open(reverse_zone_file_name,'w')
	file_content.writelines([item for item in lines[:-2]])
	file_content.close()

	# Add few lines

	zoneFile_content = open(reverse_zone_file_name, 'a')
	zoneFile_content.write("\n \t IN \t NS \t %s   \n"% ("ns."+domain_name+"."))        
	zoneFile_content.close()
	print "\nThe reverse zone is created and is now ready to accept your records!\nYou can add reverse records any time!\n"


creating_forward_zone(argv[1],argv[2])
creating_reverse_zone(argv[1])

