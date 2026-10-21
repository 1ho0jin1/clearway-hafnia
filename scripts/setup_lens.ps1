<#
setup_lens.ps1 - install the lens camera: MediaMTX, then camera lens_1 in XProtect reading rtsp://127.0.0.1:8554/lens1.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\setup_lens.ps1
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_lens.ps1     # then start the stream

The lens camera shows clips our code renders (lens\publisher.py), so Hafnia, which only reads XProtect recordings, can
be asked about them. Every step looks before it acts, so running this again changes nothing. No Recording Server
restart is needed: the Universal driver is part of the installed device pack.

1. MediaMTX (pinned release, SHA-256 checked) into C:\tools\mediamtx\<version>. It listens on 127.0.0.1 only
   (lens\mediamtx.yml), so Windows Firewall is not involved.
2. Hardware lens_1 on the Universal 1 channel driver at http://127.0.0.1:8554 (the driver needs credentials; MediaMTX
   ignores them, these are placeholders), stream 1 set to H.264, RTP over RTSP (TCP), path lens1, 10 fps.
3. Camera lens_1 in device group Hackathon, and our rule "Lens: record lens_1 always" (the default record-on-motion
   rule could miss the start of a clip that moves little; the idle stream between clips is a static frame and costs
   almost no storage).
#>
[CmdletBinding()]
param(
    [string] $MediaMtxVersion = 'v1.21.2',
    [string] $MediaMtxSha256 = 'a84224f5a490855684e62ba6fb71e80ea2a5e16aed61883bb58380290e93e467',
    [string] $Name = 'lens_1',
    [string] $RtspPath = 'lens1',
    [int] $RtspPort = 8554,
    [string] $GroupName = 'Hackathon'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
function Write-Step([string]$Text) { Write-Host ('{0:HH:mm:ss} {1}' -f (Get-Date), $Text) }

# --- 1. MediaMTX -------------------------------------------------------------------------------------------------------
$dir = "C:\tools\mediamtx\$MediaMtxVersion"
if (Test-Path "$dir\mediamtx.exe") {
    Write-Step "present: MediaMTX $MediaMtxVersion"
} else {
    New-Item -ItemType Directory -Force $dir | Out-Null
    $zip = "$dir\mediamtx_${MediaMtxVersion}_windows_amd64.zip"
    & curl.exe -sSL -o $zip "https://github.com/bluenviron/mediamtx/releases/download/$MediaMtxVersion/mediamtx_${MediaMtxVersion}_windows_amd64.zip"
    if ($LASTEXITCODE) { throw "MediaMTX download failed ($LASTEXITCODE)" }
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash
    if ($hash -ne $MediaMtxSha256) { Remove-Item $zip; throw "MediaMTX checksum mismatch: $hash" }
    Expand-Archive $zip -DestinationPath $dir -Force
    Write-Step "installed: MediaMTX $MediaMtxVersion in $dir"
}

# --- 2. Hardware and stream settings ----------------------------------------------------------------------------------
Import-Module MilestonePSTools
Connect-Vms -ServerAddress 'http://localhost' -AcceptEula | Out-Null
$rs = Get-VmsRecordingServer | Select-Object -First 1
$driver = Get-VmsHardwareDriver -RecordingServer $rs | Where-Object Name -eq 'Universal 1 channel driver' | Select-Object -First 1
if (-not $driver) { throw 'Universal 1 channel driver not found on the Recording Server' }
$address = "http://127.0.0.1:$RtspPort"
$hw = Get-VmsHardware -RecordingServer $rs -EnableFilter All | Where-Object { ($_.Address -replace '/$', '') -ieq $address } | Select-Object -First 1
if ($hw) {
    Write-Step "present: hardware $($hw.Name) @ $address"
} else {
    $cred = New-Object PSCredential ('lens', (ConvertTo-SecureString 'lens' -AsPlainText -Force))
    $hw = Add-VmsHardware -RecordingServer $rs -HardwareAddress $address -DriverNumber $driver.Number -Credential $cred -Name $Name
    Write-Step "created: hardware $Name @ $address"
}
if ($hw.Name -ne $Name) { Set-VmsHardware -Hardware $hw -Name $Name }
if (-not $hw.Enabled) { Set-VmsHardware -Hardware $hw -Enabled $true }

$cam = @(Get-VmsCamera -Hardware $hw -EnableFilter All) | Select-Object -First 1
$stream = Get-VmsCameraStream -Camera $cam | Where-Object Name -eq 'Video stream 1'
$wanted = @{ Codec = 'h264'; StreamingMode = 'RTP over RTSP (TCP)'; ConnectionURI = $RtspPath; RTSPPort = $RtspPort; FPS = 10 }
# Read-back shows display names (H.264, RTP/RTSP/TCP), so compare the two settings that are not enumerations.
if ($stream.Settings['ConnectionURI'] -ne $RtspPath -or [int]$stream.Settings['RTSPPort'] -ne $RtspPort -or $stream.Settings['StreamingMode'] -ne 'RTP/RTSP/TCP') {
    $stream | Set-VmsCameraStream -Settings $wanted
    Write-Step "set: stream 1 -> rtsp://127.0.0.1:$RtspPort/$RtspPath (H.264, RTP over RTSP/TCP, 10 fps)"
} else {
    Write-Step 'present: stream settings'
}

# --- 3. Camera name, group, recording rule ------------------------------------------------------------------------------
if (-not $cam.Enabled) { $cam = Set-VmsCamera -InputObject $cam -Enabled $true -PassThru }
if ($cam.Name -ne $Name) { $cam = Set-VmsCamera -InputObject $cam -Name $Name -PassThru }
$group = Get-VmsDeviceGroup -Name $GroupName -Type Camera | Select-Object -First 1
if ($group -and "$($cam.Id)" -notin @(Get-VmsDeviceGroupMember -Group $group | ForEach-Object { "$($_.Id)" })) {
    Add-VmsDeviceGroupMember -Group $group -Device $cam
    Write-Step "added to device group $GroupName"
}
$ruleName = "Lens: record $Name always"
if (Get-VmsRule | Where-Object DisplayName -eq $ruleName) {
    Write-Step "present: rule $ruleName"
} else {
    New-VmsRule -Name $ruleName -Properties @{
        Description = 'Our rule (hafnia-hackathon-2026): lens clips must be recorded whatever their motion.'
        StartRuleType = 'TimeInterval'; StopRuleType = 'TimeInterval'; Always = 'True'
        StartActions = 'StartRecording'; 'Start.StartRecording.Delay' = '0'; 'Start.StartRecording.DeviceIds' = "Camera[$($cam.Id)]"
        StopActions = 'StopRecording'; 'Stop.StopRecording.Delay' = '0'
    } | Out-Null
    Write-Step "created: rule $ruleName"
}
Write-Step "ready: camera $($cam.Name) (id $($cam.Id)); start the stream with scripts\start_lens.ps1"
Disconnect-Vms
