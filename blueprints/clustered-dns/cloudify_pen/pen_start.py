import subprocess, os, sysfrom cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx
from lockfile import LockFile
from pen_servers import pen_servers_list

path_of_pen_script = "/root/pen_servers.py"

def start_pen(pen_servers_list):
	if not pen_servers_list:
		ctx.logger.info("No servers at back-end. Please add at least one server in order to start pen.") 
	else:
		lock=LockFile(path_of_pen_script)		
		subprocess.call("pidof pen > allpid.txt", shell=True)
		all_pid_file = open("/root/allpid.txt", 'r')
        	all_pid_file_content = all_pid_file.read()
        	all_pid_file.close()
		lock.acquire()
		pen_servers_list = [server + ":53 " for server in pen_servers_list]
		concatenated_servers = ''.join(pen_servers_list)
        	pen_command = "./pen -drUp /root/pid_file.txt 53 " + (concatenated_servers)
        	ctx.logger.info(pen_command)
        	path_to_pen = "/root/Git/pen"
        	os.chdir(path_to_pen)
        	subprocess.call(pen_command, shell=True)
        	kill_command = "kill " + all_pid_file_content
        	subprocess.call(kill_command, shell=True)
		lock.release()	

start_pen(pen_servers_list)
