import subprocess, os, sys
from lockfile import LockFile
from pen_servers import pen_servers_list

path_of_pen_script = "/root/pen_servers.py"

def add_node(current_pen_servers_list, current_pointer_record, server_present):
	if current_pointer_record in current_pen_servers_list:
		print "server already included at backend for round-robin configuration"
		server_present=1
		return server_present, current_pen_servers_list
	else:
		current_pen_servers_list += [current_pointer_record]
		print current_pen_servers_list
		pen_script = open(path_of_pen_script,'w')
        	pen_script.write("pen_servers_list=" + str(current_pen_servers_list))
        	pen_script.close()
		server_present=0
		return server_present, current_pen_servers_list

def main(pen_servers_list):
	server_is_present=0
	lock = LockFile(path_of_pen_script)
	lock.acquire()
	server_is_present, pen_servers_list = add_node(pen_servers_list, argv[1], server_is_present)
	if server_is_present==0:
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
