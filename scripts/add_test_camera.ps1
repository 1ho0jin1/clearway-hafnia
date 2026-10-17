<#
add_test_camera.ps1 - inject a video clip into XProtect as one more StableFPS test camera, so the Hafnia gateway (which
only fetches recorded XProtect video, xprotect://) can analyse it. The camera plays the clip in an endless loop.

Follows the organizers' own procedure (C:\hackathon\core\Configure-StableFPS.ps1): copy the clip next to the driver's
H.264 files, bump the versionid revision in StableFPS.xml, restart the Recording Server so it re-reads the file list,
then add one StableFPS hardware on its own 127.0.0.1 port and point its settings at the clip. Every step looks before
it acts, so running it again changes nothing.

    # 1. Convert any video to the driver's format: H.264 Annex B, no extension, named <width>x<height>_<name>
    ffmpeg -i in.mp4 -an -vf "fps=10,format=yuv420p" -c:v libx264 -profile:v main -crf 23 -bf 0 -g 10 `
           -keyint_min 10 -sc_threshold 0 -bsf:v h264_mp4toannexb -f h264 data\clips\1920x1080_my_camera
    # 2. Add it (run as the logged-in Administrator; MilestonePSTools refuses SYSTEM)
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\add_test_camera.ps1 `
           -Clip data\clips\1920x1080_my_camera -Port 105 -RestartRecordingServer

Without -RestartRecordingServer the script stops with exit code 3 when a restart is needed. The restart pauses every
camera, and recording, for about 2-3 minutes.

The 32-bit driver keeps every clip in RAM, 1.7 GB in total (StableFPS READ ME): keep clips small.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $Clip,
    [Parameter(Mandatory)] [ValidateRange(100, 199)] [int] $Port,
    [int] $Fps = 10,
    [string] $GroupName = 'Hackathon',
    [switch] $RestartRecordingServer
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$RsService = 'Milestone XProtect Recording Server'

function Write-Step([string]$Text) { Write-Host ('{0:HH:mm:ss} {1}' -f (Get-Date), $Text) }

function Get-RecordingServerStart {
    $svc = Get-CimInstance Win32_Service -Filter "Name='$RsService'"
    if ($svc.ProcessId) { (Get-CimInstance Win32_Process -Filter "ProcessId = $($svc.ProcessId)").CreationDate }
}

# Never stop the Recording Server within 90 s of its start: it can hang (organizers' finding, p006).
function Wait-RecordingServerSettled {
    $started = Get-RecordingServerStart
    if (-not $started) { return }
    $age = ((Get-Date) - $started).TotalSeconds
    if ($age -lt 90) {
        Write-Step ('Recording Server started {0:N0} s ago: waiting {1:N0} s' -f $age, (90 - $age))
        Start-Sleep -Seconds ([int][math]::Ceiling(90 - $age))
    }
}

function Restart-RecordingServer {
    Wait-RecordingServerSettled
    Write-Step 'stopping the Recording Server'
    $deadline = (Get-Date).AddSeconds(60)
    while ((Get-Service $RsService).Status -ne 'Stopped') {
        if ((Get-Date) -gt $deadline) {
            throw 'the Recording Server did not stop within 60 s. Do not retry: see the xprotect-hackathon skill, troubleshooting (restart the machine)'
        }
        if ((Get-Service $RsService).Status -eq 'Running') { try { Stop-Service $RsService -Force -ErrorAction Stop } catch { } }
        Start-Sleep -Seconds 5
    }
    Write-Step 'starting the Recording Server'
    Start-Service $RsService
    (Get-Service $RsService).WaitForStatus('Running', [TimeSpan]::FromMinutes(3))
}

# --- 1. The clip --------------------------------------------------------------------------------------------------
$clipFile = Get-Item $Clip
if ($clipFile.Extension) { throw "the clip must have no extension (H.264 Annex B named <width>x<height>_<name>): $($clipFile.Name)" }
if ($clipFile.Name -notmatch '^(\d+)x(\d+)_(.+)$') { throw "the clip name must be <width>x<height>_<name>: $($clipFile.Name)" }
$width, $height, $name = [int]$matches[1], [int]$matches[2], $matches[3]

# The driver folder may sit apart from the service exe (on the hackathon machines it is under Program Files (x86)).
$svc = Get-CimInstance Win32_Service -Filter "Name='$RsService'"
$nativeDrivers = @(
    (Join-Path (Split-Path ($svc.PathName -replace '^"([^"]+)".*$', '$1')) 'Drivers\NativeDrivers'),
    'C:\Program Files (x86)\Milestone\XProtect Recording Server\Drivers\NativeDrivers',
    'C:\Program Files\Milestone\XProtect Recording Server\Drivers\NativeDrivers'
) | Where-Object { Test-Path (Join-Path $_ 'StableFPS_DATA') } | Select-Object -First 1
if (-not $nativeDrivers) { throw 'StableFPS driver folder not found (is the StableFPS driver installed?)' }
$h264 = Get-ChildItem (Join-Path $nativeDrivers 'StableFPS_DATA') -Directory -Recurse -Depth 2 -Filter H264 |
    Where-Object { $_.FullName -notlike '*Edge*' } | Select-Object -First 1
if (-not $h264) { throw "StableFPS H264 folder not found under $nativeDrivers" }
$xml = 'resources\StableFPS.xml', 'StableFPS.xml' | ForEach-Object { Join-Path $nativeDrivers $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1

$target = Join-Path $h264.FullName $clipFile.Name
$have = Get-Item $target -ErrorAction SilentlyContinue
if ($have -and $have.Length -eq $clipFile.Length) {
    Write-Step "present: clip $($clipFile.Name)"
} else {
    Copy-Item $clipFile.FullName $target -Force
    Write-Step ('copied: clip {0} ({1:N1} MB)' -f $clipFile.Name, ($clipFile.Length / 1MB))
    # The Recording Server re-reads the file list only when the versionid changes. No BOM: the 32-bit driver parses it.
    $lines = Get-Content $xml
    $i = [array]::IndexOf(@($lines | ForEach-Object { $_ -match 'versionid=' }), $true)
    $old = $lines[$i]
    $lines[$i] = [regex]::Replace($old, '(versionid="\$Revision:\s*)(\d+)', { param($m) $m.Groups[1].Value + ([int]$m.Groups[2].Value + 1) })
    if ($lines[$i] -eq $old) { throw "could not bump the revision in: $($old.Trim())" }
    [IO.File]::WriteAllLines($xml, $lines, (New-Object Text.UTF8Encoding $false))
    Write-Step ('revision bumped: {0}' -f $lines[$i].Trim())
}

# --- 2. Restart the Recording Server if it has not read the current StableFPS.xml yet ---------------------------------
if ((Get-Item $xml).LastWriteTime -gt (Get-RecordingServerStart)) {
    if (-not $RestartRecordingServer) {
        Write-Step 'StableFPS.xml is newer than the running Recording Server: run again with -RestartRecordingServer'
        exit 3
    }
    Restart-RecordingServer
} else {
    Write-Step 'present: the running Recording Server already read StableFPS.xml'
}
Wait-RecordingServerSettled

# --- 3. Hardware, settings, camera, group ---------------------------------------------------------------------------
Import-Module MilestonePSTools
Connect-Vms -ServerAddress 'http://localhost' -AcceptEula | Out-Null
$rs = Get-VmsRecordingServer | Select-Object -First 1
$driver = Get-VmsHardwareDriver -RecordingServer $rs | Where-Object Name -like '*StableFPS*' | Select-Object -First 1
if (-not $driver) { throw 'StableFPS driver not found on the Recording Server' }
$address = "http://127.0.0.1:$Port"
$hw = Get-VmsHardware -RecordingServer $rs -EnableFilter All | Where-Object { ($_.Address -replace '/$', '') -ieq $address } | Select-Object -First 1
if ($hw) {
    Write-Step "present: hardware $($hw.Name) @ $address"
} else {
    # The driver does not check credentials (StableFPS READ ME); these are its documented placeholder values.
    $cred = New-Object PSCredential ('stablefps', (ConvertTo-SecureString 'stablefps' -AsPlainText -Force))
    $until = (Get-Date).AddMinutes(5)
    while ($true) {
        try { $hw = Add-VmsHardware -RecordingServer $rs -HardwareAddress $address -DriverNumber $driver.Number -Credential $cred -Name $name -ErrorAction Stop; break }
        catch {
            if ($_.Exception.Message -notmatch '60277|Unable to connect to the recording server' -or (Get-Date) -gt $until) { throw }
            Write-Step 'the Recording Server does not take hardware yet: retrying in 15 s'
            Start-Sleep -Seconds 15
        }
    }
    Write-Step "created: hardware $name @ $address"
}
if ($hw.Name -ne $name) { Set-VmsHardware -Hardware $hw -Name $name }
if (-not $hw.Enabled) { Set-VmsHardware -Hardware $hw -Enabled $true }

# StableFPS keeps its settings on the hardware. Right after a restart the Management Server may still hold the old
# file list and refuse the new file name: retry for up to 5 minutes (organizers' finding, p005).
$wanted = [ordered]@{ VideoCodec = 'H264'; VideoH264Files = $clipFile.Name; FPS = "$Fps"; Codec = 'h264'; FileName = $clipFile.Name }
for ($try = 1; ; $try++) {
    try {
        $settings = Get-HardwareSetting -Hardware $hw
        foreach ($k in $wanted.Keys) {
            if (-not $settings.PSObject.Properties[$k]) { continue }
            if ("$($settings.$k)" -eq $wanted[$k]) { continue }
            Set-HardwareSetting -Hardware $hw -Name $k -Value $wanted[$k]
            Write-Step "set: $k = $($wanted[$k])"
        }
        break
    } catch {
        if ($try -ge 10) { throw }
        Write-Step "settings refused ($($_.Exception.Message)): waiting 30 s, attempt $try/10"
        Start-Sleep -Seconds 30
    }
}

$cam = @(Get-VmsCamera -Hardware $hw -EnableFilter All) | Select-Object -First 1
if (-not $cam.Enabled) { $cam = Set-VmsCamera -InputObject $cam -Enabled $true -PassThru }
if ($cam.Name -ne $name) { $cam = Set-VmsCamera -InputObject $cam -Name $name -PassThru }
$group = Get-VmsDeviceGroup -Name $GroupName -Type Camera | Select-Object -First 1
if ($group -and "$($cam.Id)" -notin @(Get-VmsDeviceGroupMember -Group $group | ForEach-Object { "$($_.Id)" })) {
    Add-VmsDeviceGroupMember -Group $group -Device $cam
    Write-Step "added to device group $GroupName"
}

# --- 4. Proof: a live frame of the clip's size (a fresh StableFPS hardware streams a 640x480 test pattern first) ----
$until = (Get-Date).AddMinutes(3)
while ($true) {
    $snap = $null
    try { $snap = Get-Snapshot -Camera $cam -Live -LiveTimeoutMS 10000 } catch { }
    if ($snap -and $snap.Width -eq $width -and $snap.Height -eq $height) { break }
    if ((Get-Date) -gt $until) { throw ('no {0}x{1} live frame from {2} after 3 minutes (last: {3})' -f $width, $height, $name, $(if ($snap) { "$($snap.Width)x$($snap.Height)" } else { 'none' })) }
    Start-Sleep -Seconds 10
}
Write-Step ('ready: camera {0} (id {1}) plays {2} at {3} fps; live frame {4}x{5}' -f $cam.Name, $cam.Id, $clipFile.Name, $Fps, $snap.Width, $snap.Height)
Disconnect-Vms
