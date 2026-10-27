<#
setup_ntfy.ps1 - phone notifications through ntfy (https://ntfy.sh): create the topic names and the verdict secret
once, keep them in user-scope environment variables (never in the repository), and show what to subscribe to.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_ntfy.ps1            # create if missing, then show
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_ntfy.ps1 -Show      # show the topic to subscribe to
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_ntfy.ps1 -Test      # one sample push to the phone
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_ntfy.ps1 -Test -Listen 120   # ... and wait for a tap
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_ntfy.ps1 -Reset     # new names and secret

Variables (user scope, read by clearway/notify.py through config\owners.json):
  CLEARWAY_NTFY_URL        the topic the pushes go to, e.g. https://ntfy.sh/clearway-<random>
  CLEARWAY_NTFY_REPLY_URL  the topic the phone's Confirm / Reject buttons post to (<topic>-replies)
  CLEARWAY_NTFY_SECRET     signs the buttons' verdict tokens
On the phone: install the ntfy app (Android: Play Store or F-Droid; iOS: App Store), tap +, subscribe to the topic
name this script shows (server https://ntfy.sh). Or open https://ntfy.sh/<topic> in a browser. The topic name is
the credential: anyone who knows it can read the pushes, so do not put it in git, chat or a slide.
Shells started by Claude Code do not inherit user-scope variables: load them first (see CLAUDE.md, Commands).
#>
param([switch]$Show, [switch]$Test, [double]$Listen = 0, [switch]$Reset, [string]$Server = 'https://ntfy.sh')
$ErrorActionPreference = 'Stop'
$Repo = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Repo '.venv\Scripts\python.exe'

function Random-Hex([int]$bytes) {
    $buf = New-Object byte[] $bytes
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($buf)
    return ($buf | ForEach-Object { $_.ToString('x2') }) -join ''
}

$url = [Environment]::GetEnvironmentVariable('CLEARWAY_NTFY_URL', 'User')
$reply = [Environment]::GetEnvironmentVariable('CLEARWAY_NTFY_REPLY_URL', 'User')
$secret = [Environment]::GetEnvironmentVariable('CLEARWAY_NTFY_SECRET', 'User')
if ($Reset -or -not $url -or -not $reply -or -not $secret) {
    $topic = 'clearway-' + (Random-Hex 8)
    $url = "$($Server.TrimEnd('/'))/$topic"
    $reply = "$url-replies"
    $secret = Random-Hex 24
    [Environment]::SetEnvironmentVariable('CLEARWAY_NTFY_URL', $url, 'User')
    [Environment]::SetEnvironmentVariable('CLEARWAY_NTFY_REPLY_URL', $reply, 'User')
    [Environment]::SetEnvironmentVariable('CLEARWAY_NTFY_SECRET', $secret, 'User')
    Write-Host 'created: ntfy topic, reply topic and secret (user-scope environment variables)'
    $Show = $true
}
$env:CLEARWAY_NTFY_URL = $url
$env:CLEARWAY_NTFY_REPLY_URL = $reply
$env:CLEARWAY_NTFY_SECRET = $secret

if ($Show) {
    $topic = $url.Substring($url.LastIndexOf('/') + 1)
    Write-Host ''
    Write-Host "Subscribe on the phone (ntfy app, server $Server) to the topic:"
    Write-Host "    $topic"
    Write-Host "or open in a browser:  $url"
    Write-Host 'The Confirm / Reject buttons reply through the topic:'
    Write-Host "    $topic-replies   (nothing to subscribe to; the service follows it)"
    Write-Host ''
}
if ($Test -or $Listen -gt 0) {
    $argsList = @('-m', 'clearway.notify')
    if ($Test) { $argsList += '--test' }
    if ($Listen -gt 0) { $argsList += @('--listen', [string]$Listen) }
    & $Python @argsList
    exit $LASTEXITCODE
}
