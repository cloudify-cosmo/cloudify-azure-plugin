#! /bin/bash

ctx logger info "Retrieving nodes_to_monitor and deployment_id"

NTM="$(ctx node properties nodes_to_monitor)"
ctx logger info "nodes_to_monitor = ${NTM}"
NTM=$(echo ${NTM} | sed "s/u'/'/g")
DPLID=$(ctx deployment id)
currVenv=/home/`whoami`/${DPLID}/env
ctx logger info "deployment_id = ${DPLID}, virtual env is ${currVenv}"
pipPath=/home/`whoami`/${DPLID}/env/bin/pip
ctx logger info "Running ${pipPath} install influxdb  ... "
${pipPath} install influxdb
statusCode=$?
if [ $statusCode -gt 0 ]; then 
  ctx logger info "Aborting due to a failure with exit code ${statusCode} in ${pipPath} install influxdb"
  exit ${statusCode}
fi

ctx logger info "Downloading scripts/healing/policy.py ..."
LOC=$(ctx download-resource scripts/healing/policy.py)

#nohup "${currVenv}/bin/python" ${LOC} "${NTM}" "${DPLID}" > /dev/null 2>&1 &
COMMAND="${currVenv}/python ${LOC} \"${NTM}\" ${DPLID} > /home/`whoami`/logfile"
crontab_file=/home/`whoami`/mycron
ctx logger info "Adding ${COMMAND} to ${crontab_file} ..."
echo "*/1 * * * * $COMMAND" >> ${crontab_file}
ctx logger info "Adding the task to the crontab ..."
crontab ${crontab_file}
ctx logger info "Done adding the task to the crontab - Starting the healing dog"
