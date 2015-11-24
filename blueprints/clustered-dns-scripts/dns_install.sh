#! /bin/bash -e

ctx logger info "The script for installing DNS using BIND9 starts now!"

currCommand='apt-get install -y bind9 bind9utils bind9-doc'
if [ `whoami` != 'root' ]
then    
	currCommand="sudo ${currCommand}"
fi

${currCommand}



