#! /bin/bash 
read PID < /tmp/pid_file
kill -9 $PID


