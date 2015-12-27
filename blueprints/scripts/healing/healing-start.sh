#! /bin/bash

ctx logger info "Retrieving nodes_to_monitor and deployment_id"

NTM="$(ctx node properties nodes_to_monitor)"
ctx logger info "nodes_to_monitor = ${NTM}"
NTM=$(echo ${NTM} | sed "s/u'/'/g")
DPLID=$(ctx deployment id)
currVenv=/root/${DPLID}/env
ctx logger info "deployment_id = ${DPLID}, virtual env is ${currVenv}"
pipPath=${currVenv}/bin/pip
ctx logger info "Running ${pipPath} install influxdb  ... "
${pipPath} install influxdb
statusCode=$?
if [ $statusCode -gt 0 ]; then 
  ctx logger info "Aborting due to a failure with exit code ${statusCode} in ${pipPath} install influxdb"
  exit ${statusCode}
fi

ctx logger info "Downloading scripts/healing/healing.py ..."
LOC=$(ctx download-resource scripts/healing/healing.py)
status_code=$?
ctx logger info "ctx download-resource status code is ${status_code}"
ctx logger info "LOC is ${LOC}"

COMMAND="${currVenv}/bin/python ${LOC} \"${NTM}\" ${DPLID}"
crontab_file=/tmp/mycron
ctx logger info "Adding ${COMMAND} to ${crontab_file} ..."
echo "*/1 * * * * ${COMMAND}" >> ${crontab_file}
status_code=$?
ctx logger info "echo ${COMMAND} code is ${status_code}"
ctx logger info "Adding the task to the crontab : crontab ${crontab_file} ..."
sudo crontab ${crontab_file}
status_code=$?
ctx logger info "crontab ${crontab_file} status code is ${status_code}"
currCrontab=`sudo crontab -l`
ctx logger info "currCrontab is ${currCrontab}"
ctx logger info "Done adding the task to the crontab - Starting the healing dog"
