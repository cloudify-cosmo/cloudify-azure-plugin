#! /bin/bash

echo "The script for uninstalling DNS using BIND9 starts now!"

currCommand='apt-get remove -y bind9 bind9utils bind9-doc'
if [ `whoami` != 'root' ]
then    
	currCommand="sudo ${currCommand}"
fi

${currCommand}

