#! /bin/bash

ctx logger info "The script for uninstalling DNS using BIND9 starts now!"

currCommand='service bind9 stop'
if [ `whoami` != 'root' ]
then    
	currCommand="sudo ${currCommand}"
fi

${currCommand}
