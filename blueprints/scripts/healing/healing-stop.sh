#! /bin/bash 
read PID < /home/`whoami`/pid_file
kill -9 $PID


