###########################################
## Enables unencrypted WinRM HTTP access ##
###########################################
# http://docs.getcloudify.org/3.3.1/agents/overview/
winrm quickconfig -q
winrm set winrm/config '@{MaxTimeoutms="1800000"}'
winrm set winrm/config/winrs '@{MaxMemoryPerShellMB="300";MaxShellsPerUser="2147483647"}'
winrm set winrm/config/service '@{AllowUnencrypted="true";MaxConcurrentOperationsPerUser="4294967295"}'
winrm set winrm/config/service/auth '@{Basic="true"}'
&netsh advfirewall firewall add rule name="WinRM 5985" protocol=TCP dir=in localport=5985 action=allow
