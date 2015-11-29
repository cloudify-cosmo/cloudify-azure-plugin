import subprocess, os, sys
from cloudify.exceptions import NonRecoverableError,RecoverableError
from cloudify import ctx

def uninstall_pen():
	subprocess.call("pidof pen > allpid.txt", shell=True)
	all_pid_file = open("/root/allpid.txt", 'r')
        all_pid_file_content = all_pid_file.read()
        all_pid_file.close()
	kill_command = "kill " + all_pid_file_content
	ctx.logger.info(kill_command)
	subprocess.call(kill_command, shell=True)
	subprocess.call("rm -rf /root/Git", shell=True)


uninstall_pen()
