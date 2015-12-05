import subprocess,os, sys
from lockfile import LockFile
from pen_servers import pen_servers_list

path_of_pen_script = "/root/pen_servers.py"

def remove_node(current_pen_servers_list, current_pointer_record, server_is_missing):
	if current_pointer_record not in current_pen_servers_list:
        	print "server already absent"
        	server_is_missing = 1
        	return server_is_missing, current_pen_servers_list
    	else:
        	current_pen_servers_list.remove(str(current_pointer_record))
        	print current_pen_servers_list
       		pen_script = open(path_of_pen_script,'w')
        	pen_script.write("pen_servers_list=" + str(current_pen_servers_list))
        	pen_script.close()
        	server_is_missing = 0
    		return server_is_missing, current_pen_servers_list

def main(pen_servers_list):
	server_is_absent = 0
    	pointer_record = sys.argv[1]
    	lock = LockFile(path_of_pen_script)
    	lock.acquire()
    	server_is_absent, pen_servers_list = remove_node(pen_servers_list, pointer_record, server_is_absent)
    	if server_is_absent == 0:
        	subprocess.call("pidof pen > allpid.txt", shell=True)
        	all_pid_file = open("/root/allpid.txt", 'r')
        	all_pid_file_content = all_pid_file.read()
        	all_pid_file.close()
        	pen_servers_list = [server + ":53 " for server in pen_servers_list]
        	concatenated_servers = ''.join(pen_servers_list)
        	pen_command = "./pen -drUp /root/pid_file.txt 53 " + (concatenated_servers)
        	print pen_command
        	path_to_pen = "/root/Git/pen"
        	os.chdir(path_to_pen)
        	subprocess.call(pen_command, shell=True)
        	kill_command = "kill " + all_pid_file_content
        	subprocess.call(kill_command, shell=True)
    	lock.release()

main(pen_servers_list)
