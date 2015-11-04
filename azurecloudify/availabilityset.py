import json
import requests



location = ''
subscription_id = ''
resource_group_name = ''
availability_set_name= ''
credentials = 'Bearer ' + auth.get_auth_token()
headers = {"Content-Type": "application/json", "Authorization": credentials}
availability_set_url = 'https://management.azure.com/subscriptions/'+subscription_id+'/resourceGroups/'+resource_group_name+'/providers/Microsoft.Compute/availabilitySets/'+availability_set_name+'?api-version='
availability_set_params = json.dumps({ 
   "name": availability_set_name, 
   "type": "Microsoft.Compute/availabilitySets", 
   "location": location
}
)
response_as = requests.put(url=availability_set_url, data=availability_set_params, headers=headers) 
print response_as.text 
