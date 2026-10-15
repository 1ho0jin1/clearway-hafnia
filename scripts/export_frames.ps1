<#
export_frames.ps1 - export recorded JPEG frames for every completed request in a benchmark run, so another model can
be shown the same clips Hafnia saw. Costs no Hafnia requests.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\export_frames.ps1 -RunDir run\bench-20261015

Writes <RunDir>\frames\clipNN\frame_NNN.jpg (neutral names: no camera name leaks into a blind evaluation) and
<RunDir>\frames\manifest.json, which maps clipNN to the request. Recordings are kept 24 hours: run it the same day.
#>
param(
    [Parameter(Mandatory)] [string] $RunDir,
    [double] $Interval = 0.5   # seconds between frames: 2 fps
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Import-Module MilestonePSTools
Connect-Vms -ServerAddress 'http://localhost' -AcceptEula | Out-Null

$rows = Get-Content (Join-Path $RunDir 'results.jsonl') -Encoding UTF8 | Where-Object { $_ } | ForEach-Object { $_ | ConvertFrom-Json } |
    Where-Object progress -eq 'Completed'
$framesDir = Join-Path $RunDir 'frames'
$manifest = @()
$n = 0
foreach ($r in $rows) {
    $n++
    $clip = 'clip{0:D2}' -f $n
    $dir = Join-Path $framesDir $clip
    if (Test-Path $dir) { Remove-Item $dir -Recurse -Force }
    New-Item -ItemType Directory -Force $dir | Out-Null

    $camera = Get-VmsCamera | Where-Object Name -eq $r.camera
    $end = [datetime]::Parse($r.clip_end_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal)
    $start = $end.AddSeconds(-[double]$r.clip_s)
    $null = $camera | Get-Snapshot -Timestamp $start -EndTime $end -Interval $Interval -Save -Path $dir -Quality 90

    $i = 0
    Get-ChildItem $dir -Filter *.jpg | Sort-Object Name | ForEach-Object { Rename-Item $_.FullName ('frame_{0:D3}.jpg' -f $i); $i++ }
    $manifest += [ordered]@{ clip = $clip; id = $r.id; label = $r.label; camera = $r.camera; clip_s = $r.clip_s
                             start_utc = $start.ToString('yyyy-MM-ddTHH:mm:ssZ'); end_utc = $r.clip_end_utc; frames = $i }
    '{0}: {1} {2}s -> {3} frames' -f $clip, $r.camera, $r.clip_s, $i
}
$manifest | ConvertTo-Json | Set-Content (Join-Path $framesDir 'manifest.json') -Encoding UTF8
Disconnect-Vms
