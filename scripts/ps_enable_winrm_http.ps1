###########################################
## Enables unencrypted WinRM HTTP access ##
###########################################

Set-Item WSMAN:\LocalHost\Service\AllowUnencrypted -Value $true
