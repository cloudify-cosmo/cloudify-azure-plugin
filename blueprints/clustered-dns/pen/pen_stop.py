import subprocess, os, sys

def main():
	subprocess.call("pidof pen > allpid.txt", shell=True)
	all_pid_file = open("/root/allpid.txt", 'r')
        all_pid_file_content = all_pid_file.read()
        all_pid_file.close()
	kill_command = "kill " + all_pid_file_content
	print kill_command
	subprocess.call(kill_command, shell=True)

main()
