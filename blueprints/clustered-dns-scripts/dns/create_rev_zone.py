import subprocess,os, sys
#This is a neww line I have added just now.
def creating_rev_zone():
	domain_name= sys.argv[1]
	old_file="/etc/bind/db.127"
	new_zone_file="/etc/bind/zones/db.0"
	subprocess.call("cp /etc/bind/db.127 new_zone_file",shell=True)
	
	old_file_content=open(old_file,'r')
	text_in_oldFile=old_file_content.read()
	old_file_content.close()

	new_zone_file_content=open(new_zone_file,'w')
	text_updated=text_in_oldFile.replace("localhost.",domain_name+".")
	text_modified=text_updated.replace("root.localhost.","admin."+domain_name+".")
	new_zone_file_content.write(text_modified)
	new_zone_file_content.close()

	# delete last 2 lines

	readFiles = open(new_zone_file,'r')
	lines = readFiles.readlines()
	readFiles.close()

	file_content = open(new_zone_file,'w')
	file_content.writelines([item for item in lines[:-2]])
	file_content.close()

	# Add few lines

	zoneFile_content = open(new_zone_file, 'a')
	zoneFile_content.write("\n \t IN \t NS \t %s   \n"% ("ns."+domain_name+"."))        
	zoneFile_content.close()


def main():
	creating_rev_zone()

main()
