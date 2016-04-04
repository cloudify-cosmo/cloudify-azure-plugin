Configuration CloudifyExample
{
  param
  (
    # VM instance name
    [Parameter(Mandatory)]
    [ValidateNotNullOrEmpty()]
    [String]$MachineName,

    # Webapp port
    [Parameter(Mandatory)]
    [Int]$WebServerPort
  )

  Node $MachineName
  {
    # Install the IIS Role
    WindowsFeature IIS
    {
      Ensure = "Present"
      Name = "Web-Server"
    }

    # Install ASP.NET Framework v4.5
    WindowsFeature ASP
    {
      Ensure = "Present"
      Name = "Web-Asp-Net45"
    }

    # Configures IIS web management tools
    WindowsFeature WebServerManagementConsole
    {
      Name = "Web-Mgmt-Console"
      Ensure = "Present"
    }

    # Sets IIS HTTP binding port
    Script DeployWebPackage
    {
      GetScript = {
        @{
          Result = ""
        }
      }
      TestScript = {
        $false
      }
      SetScript = {
        Set-WebBinding -Name 'Default Web Site' -BindingInformation "*:80:" -PropertyName Port -Value $using:WebServerPort
        netsh advfirewall firewall add rule name="Cloudify HTTP Web Application" dir=in action=allow protocol=TCP localport=$using:WebServerPort
      }
    }
  }
}
