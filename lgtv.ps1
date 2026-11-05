<#
.SYNOPSIS
  Control lgtv-tune on a rooted LG webOS TV from this PC (Windows PowerShell 5.1+).

.EXAMPLE
  .\lgtv.ps1 deploy                 copy the scripts to the TV and install the boot hook
  .\lgtv.ps1 apply                  apply everything now (the boot hook also does it ~1 min after each boot)
  .\lgtv.ps1 status                 what is applied, memory, swap
  .\lgtv.ps1 undo                   revert for this boot (the hook re-applies at next boot)
  .\lgtv.ps1 pause / resume         stop / start re-applying at boot
  .\lgtv.ps1 remove                 undo, delete the hook and the scripts from the TV
  .\lgtv.ps1 install-ipk app.ipk    install an external app (.ipk) on the TV
  .\lgtv.ps1 uninstall-app <id>     uninstall a homebrew or LG Store app
  .\lgtv.ps1 apps                   list the apps you can uninstall
  .\lgtv.ps1 cleanframe             copy look\cleanframe-lg to the TV and make CleanFrame the Home screen
  .\lgtv.ps1 cleanframe-undo        CleanYourTV's own home screen back
  .\lgtv.ps1 log | shell | reboot
#>
param(
  [Parameter(Position = 0)][string]$Command = 'status',
  [Parameter(Position = 1)][string]$Arg,
  [string]$TV = $(if ($env:LGTV_IP) { $env:LGTV_IP } else { '192.168.1.10' }),
  [string]$Key = "$env:USERPROFILE\.ssh\lgtv_root"
)
$ErrorActionPreference = 'Stop'
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path
$Remote = '/media/developer/lgtv-tune'
$Hook = '/var/lib/webosbrew/init.d/90-lgtv-tune'
$SshOpts = @('-i', $Key, '-o', 'IdentitiesOnly=yes', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=8', '-o', 'LogLevel=ERROR')

function Invoke-TV([string]$cmd) {
  # keep $cmd free of double quotes: Windows PowerShell 5.1 mangles them when passing arguments to ssh.exe
  & ssh @SshOpts "root@$TV" $cmd
  if ($LASTEXITCODE -ne 0) { throw "command on the TV failed (exit $LASTEXITCODE): $cmd" }
}
function Copy-ToTV([string[]]$files, [string]$dest) {
  & scp @SshOpts -q @files "root@${TV}:$dest"
  if ($LASTEXITCODE -ne 0) { throw "copy to the TV failed" }
}

if (-not (Test-Path $Key)) { throw "SSH key $Key not found. See README.md, 'One-time setup'." }

switch ($Command) {
  'deploy' {
    Invoke-TV "mkdir -p $Remote"
    Copy-ToTV (Get-ChildItem "$Here\tv" -File | ForEach-Object FullName) "$Remote/"
    # files edited on Windows may have CRLF line ends; the TV's shell needs LF
    Invoke-TV "cd $Remote && sed -i 's/\r$//' *.sh *.conf 90-lgtv-tune && chmod 755 *.sh 90-lgtv-tune && cp 90-lgtv-tune $Hook && chmod 755 $Hook && rm -f DISABLE && ls -l $Remote $Hook"
    Write-Host "Deployed. Run '.\lgtv.ps1 apply' to apply now; it also applies itself ~1 minute after every boot."
  }
  'apply'  { Invoke-TV "sh $Remote/tune.sh apply" }
  'status' { Invoke-TV "sh $Remote/tune.sh status" }
  'undo'   { Invoke-TV "sh $Remote/undo.sh" }
  'pause'  { Invoke-TV "touch $Remote/DISABLE"; Write-Host 'Paused: nothing is applied at the next boot. .\lgtv.ps1 resume to switch back on.' }
  'resume' { Invoke-TV "rm -f $Remote/DISABLE"; Write-Host 'Resumed: applied again at the next boot.' }
  'remove' {
    Invoke-TV "[ -f $Remote/undo.sh ] && sh $Remote/undo.sh; rm -f $Hook; rm -rf $Remote /tmp/lgtv-tune"
    Write-Host 'Removed. Reboot the TV to be sure everything is as LG ships it.'
  }
  'log'    { Invoke-TV 'tail -n 60 /var/lib/webosbrew/lgtv-tune.log' }
  'apps'   { Invoke-TV "sh $Remote/ipk.sh list" }
  'install-ipk' {
    if (-not $Arg -or -not (Test-Path $Arg)) { throw 'usage: .\lgtv.ps1 install-ipk <path\to\app.ipk>' }
    Copy-ToTV @((Resolve-Path $Arg).Path) '/tmp/lgtv-install.ipk'
    Invoke-TV "sh $Remote/ipk.sh install /tmp/lgtv-install.ipk"
  }
  'uninstall-app' {
    if ($Arg -notmatch '^[A-Za-z0-9._-]+$') { throw 'usage: .\lgtv.ps1 uninstall-app <appId>   (ids: .\lgtv.ps1 apps)' }
    Invoke-TV "sh $Remote/ipk.sh remove $Arg"
  }
  'cleanframe' {
    Invoke-TV "rm -rf $Remote/cleanframe $Remote/cleanframe-lg"
    & scp @SshOpts -q -r "$Here\look\cleanframe-lg" "root@${TV}:$Remote/"
    if ($LASTEXITCODE -ne 0) { throw 'copy to the TV failed' }
    Invoke-TV "mv $Remote/cleanframe-lg $Remote/cleanframe && ls $Remote/cleanframe"
    Invoke-TV "sh $Remote/cleanframe.sh install"
  }
  'cleanframe-undo' { Invoke-TV "sh $Remote/cleanframe.sh undo" }
  'shell'  { & ssh @SshOpts -t "root@$TV" }
  'reboot' { Invoke-TV 'reboot'; Write-Host 'Rebooting the TV.' }
  default  { Get-Help $MyInvocation.MyCommand.Path -Examples }
}
