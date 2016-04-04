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

  # Import the xWebsite module
  Import-DscResource -Module xWebAdministration

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

    # Configures the default IIS website
    xWebsite DefaultSite
    {
      Ensure      = "Present"
      Name        = "Default Web Site"
      State       = "Stopped"
      BindingInfo = MSFT_xWebBindingInformation
      {
        Protocol = "HTTP"
        Port     = $WebServerPort
      }
      DependsOn = "[WindowsFeature]IIS"
    }
  }
}
