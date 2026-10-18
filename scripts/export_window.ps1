<#
export_window.ps1 - save a camera's recorded frames between two UTC times as <unix-ms>.jpg files.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\export_window.ps1 -Camera test_04 `
        -Start 2026-10-18T14:24:03Z -End 2026-10-18T14:24:13Z -Out <folder> [-Fps 10]

Recorded snapshots are VideoOS.Platform.Data.JPEGData: the image is in .Bytes. Duplicate frames (the nearest frame
returned twice) are skipped. Recordings are kept 24 hours.
#>
param(
    [Parameter(Mandatory)] [string] $Camera,
    [Parameter(Mandatory)] [datetime] $Start,
    [Parameter(Mandatory)] [datetime] $End,
    [Parameter(Mandatory)] [string] $Out,
    [int] $Fps = 10
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Import-Module MilestonePSTools
Connect-Vms -ServerAddress 'http://localhost' -AcceptEula | Out-Null
$cam = Get-VmsCamera | Where-Object Name -eq $Camera | Select-Object -First 1
if (-not $cam) { throw "camera not found: $Camera" }
New-Item -ItemType Directory -Force $Out | Out-Null
$from = $Start.ToUniversalTime(); $to = $End.ToUniversalTime()
$n = 0
for ($t = $from; $t -lt $to; $t = $t.AddMilliseconds(1000 / $Fps)) {
    $snap = Get-Snapshot -Camera $cam -Timestamp $t -ErrorAction SilentlyContinue
    if (-not $snap -or -not $snap.Bytes) { continue }
    $ms = [long]([DateTimeOffset]$snap.DateTime.ToUniversalTime()).ToUnixTimeMilliseconds()
    $file = Join-Path $Out "$ms.jpg"
    if (Test-Path $file) { continue }
    [IO.File]::WriteAllBytes($file, $snap.Bytes)
    $n++
}
Disconnect-Vms
"$Camera`: $n frames"
