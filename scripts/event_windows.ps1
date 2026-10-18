<#
event_windows.ps1 - write event-centred clip windows for injected cameras whose clips.json entry has an "impact" time.

For each such camera: grab the last loop (plus 1 s) of recorded frames at the clip's frame rate, find the frame that
matches the source frame at the impact (scripts\locate_event.py), and centre a window on it. Costs no Hafnia requests.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\event_windows.ps1 -Out run\<name>\windows.json [-Seconds 6]

Output: { "<camera>": { "start": "<UTC Z>", "end": "<UTC Z>", "event_utc": "...", "match_ratio": 0.12 } }
#>
param(
    [Parameter(Mandatory)] [string] $Out,
    [double] $Seconds = 6,
    [string] $Manifest = 'data\clips.json',
    [int] $Fps = 10
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$repo = Split-Path $PSScriptRoot -Parent
$clips = (Get-Content (Join-Path $repo $Manifest) -Raw | ConvertFrom-Json).clips | Where-Object { $_.PSObject.Properties['impact'] }
Import-Module MilestonePSTools
Connect-Vms -ServerAddress 'http://localhost' -AcceptEula | Out-Null

$result = [ordered]@{}
foreach ($c in $clips) {
    $cam = Get-VmsCamera | Where-Object Name -eq $c.camera | Select-Object -First 1
    $clipFile = Get-ChildItem (Join-Path $repo 'data\clips') -File | Where-Object Name -match ('_' + [regex]::Escape($c.camera) + '$') | Select-Object -First 1
    $tmp = Join-Path ([IO.Path]::GetTempPath()) ('frames_' + $c.camera)
    if (Test-Path $tmp) { Remove-Item $tmp -Recurse -Force }
    New-Item -ItemType Directory $tmp | Out-Null

    # One loop plus a second, ending 5 s ago (recorded for sure), one frame per source frame.
    $end = [DateTime]::UtcNow.AddSeconds(-5)
    $start = $end.AddSeconds(-([double]$c.seconds + 1))
    for ($t = $start; $t -lt $end; $t = $t.AddMilliseconds(1000 / $Fps)) {
        # A recorded snapshot is a VideoOS.Platform.Data.JPEGData: the image is in .Bytes (live ones use .Content).
        $snap = Get-Snapshot -Camera $cam -Timestamp $t -ErrorAction SilentlyContinue
        if (-not $snap -or -not $snap.Bytes) { continue }
        $ms = [long]([DateTimeOffset]$snap.DateTime.ToUniversalTime()).ToUnixTimeMilliseconds()
        [IO.File]::WriteAllBytes((Join-Path $tmp "$ms.jpg"), $snap.Bytes)
    }
    $count = @(Get-ChildItem $tmp -Filter *.jpg).Count
    if ($count -lt 10) { throw "only $count recorded frames for $($c.camera) between $start and $end UTC: is it recording?" }
    $m = py (Join-Path $PSScriptRoot 'locate_event.py') --clip $clipFile.FullName --at $c.impact --frames $tmp --fps $Fps | ConvertFrom-Json
    $event = [DateTimeOffset]::FromUnixTimeMilliseconds($m.best_ms).UtcDateTime
    $result[$c.camera] = [ordered]@{
        start = $event.AddSeconds(-$Seconds / 2).ToString('yyyy-MM-ddTHH:mm:ssZ')
        end = $event.AddSeconds($Seconds / 2).ToString('yyyy-MM-ddTHH:mm:ssZ')
        event_utc = $event.ToString('yyyy-MM-ddTHH:mm:ss.fffZ')
        match_ratio = $m.ratio; frames_compared = $m.frames
    }
    '{0}: event at {1:HH:mm:ss.f} UTC, match ratio {2} over {3} frames' -f $c.camera, $event, $m.ratio, $m.frames
    Remove-Item $tmp -Recurse -Force
}
Disconnect-Vms
[IO.File]::WriteAllText((Join-Path $repo $Out), ($result | ConvertTo-Json), (New-Object Text.UTF8Encoding $false))
