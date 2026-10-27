<#
setup.ps1 - set Clearway up on a Hafnia Hackathon machine (XProtect 2026 R1 and the Hafnia gateway already installed
by the organizers), from a fresh clone, in one go.

    powershell -NoProfile -ExecutionPolicy Bypass -File setup.ps1 [-NoPrompt] [-Ntfy] [-SkipModels] [-NoStart]

Every step looks before it acts, so running it again changes nothing (idempotent). Needs internet for the downloads
(python.org, pytorch.org, PyPI, gyan.dev, nuget.org, GitHub, the Hugging Face hub). Steps:

 1. Python 3.12 (the python.org installer, Authenticode-signed by the Python Software Foundation, with the py
    launcher) if the machine has none.
 2. The virtual environment .venv: torch 2.11.0 + torchvision (CUDA 12.8 wheels; they run on CPU too), then
    requirements.txt (Ultralytics, OpenCV, transformers, ...).
 3. ffmpeg 9.0.2 (gyan.dev essentials build, SHA-256 checked) portable in C:\tools\ffmpeg; nothing on PATH.
 4. The .NET 8 SDK (Microsoft's dotnet-install.ps1 into C:\tools\dotnet, per user) if no SDK is found, then
    FrameBridge (bridge\FrameBridge, the MIP .NET library live-frame bridge) built in Release.
 5. MilestonePSTools from the PowerShell Gallery if missing (the hackathon machines have it).
 6. The lens camera: MediaMTX (pinned, SHA-256 checked) and camera lens_1 with its always-record rule
    (scripts\setup_lens.ps1), then its stream started (scripts\start_lens.ps1).
 7. The model weights fetched once: YOLO11m (Ultralytics) and SigLIP 2 (Hugging Face), unless -SkipModels.
 8. The Hafnia gateway password into the user-scope environment variable HAFNIA_GW_PASSWORD, asked for at the
    console if it is not set (never written to a file; -NoPrompt skips the question).
 9. With -Ntfy: phone pushes (scripts\setup_ntfy.ps1: topic names and the verdict secret into user-scope variables).
10. The owner board started (scripts\start_board.ps1, http://127.0.0.1:8765/), unless -NoStart.
11. A check that costs no request: the cameras XProtect knows, the gateway's count for today.

Then: README.md, "Run it".
#>
[CmdletBinding()]
param(
    [switch] $NoPrompt,
    [switch] $Ntfy,
    [switch] $SkipModels,
    [switch] $NoStart,
    [string] $PythonVersion = '3.12.10',
    [string] $FfmpegVersion = '9.0.2',
    [string] $FfmpegSha256 = '60f467265b1e312373dbcd92200c2618a74850f98d3d078e94296bb3fa2047ba'
)
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$Repo = $PSScriptRoot
Set-Location $Repo
function Step([string]$Text) { Write-Host ('{0:HH:mm:ss} {1}' -f (Get-Date), $Text) }
function Fetch([string]$Url, [string]$To) {
    & curl.exe -sSL --fail -o $To $Url
    if ($LASTEXITCODE) { throw "download failed ($LASTEXITCODE): $Url" }
}

# --- 1. Python 3.12 ----------------------------------------------------------------------------------------------------
$py = Get-Command py -ErrorAction SilentlyContinue
$has312 = $false
if ($py) { $has312 = [bool]((& py -0p 2>$null) -match '3\.12') }
if ($has312) {
    Step 'present: Python 3.12 (py launcher)'
} else {
    $exe = Join-Path $env:TEMP "python-$PythonVersion-amd64.exe"
    Fetch "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe" $exe
    $sig = Get-AuthenticodeSignature $exe
    if ($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notlike '*Python Software Foundation*') {
        Remove-Item $exe; throw "the Python installer's signature is not the Python Software Foundation's ($($sig.Status))"
    }
    Start-Process -FilePath $exe -ArgumentList '/quiet', 'InstallAllUsers=1', 'Include_launcher=1', 'PrependPath=1', 'Include_test=0' -Wait
    Remove-Item $exe
    Step "installed: Python $PythonVersion"
}

# --- 2. The virtual environment ----------------------------------------------------------------------------------------
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
if (Test-Path $Python) {
    Step 'present: .venv'
} else {
    & py -3.12 -m venv (Join-Path $Repo '.venv')
    Step 'created: .venv'
}
& $Python -m pip install --quiet --upgrade pip
& $Python -c 'import torch, torchvision' 2>$null
if ($LASTEXITCODE) {
    Step 'installing: torch 2.11.0, torchvision 0.26.0 (CUDA 12.8 wheels, about 3 GB)'
    & $Python -m pip install --quiet torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
    if ($LASTEXITCODE) { throw 'torch install failed' }
} else { Step 'present: torch' }
& $Python -m pip install --quiet -r (Join-Path $Repo 'requirements.txt')
if ($LASTEXITCODE) { throw 'pip install -r requirements.txt failed' }
Step 'present: requirements.txt'

# --- 3. ffmpeg -----------------------------------------------------------------------------------------------------------
$FfmpegDir = "C:\tools\ffmpeg\ffmpeg-$FfmpegVersion-essentials_build"
if (Test-Path "$FfmpegDir\bin\ffmpeg.exe") {
    Step "present: ffmpeg $FfmpegVersion"
} else {
    New-Item -ItemType Directory -Force 'C:\tools\ffmpeg' | Out-Null
    $zip = "C:\tools\ffmpeg\ffmpeg-$FfmpegVersion-essentials_build.zip"
    Fetch "https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-$FfmpegVersion-essentials_build.zip" $zip
    $hash = (Get-FileHash $zip -Algorithm SHA256).Hash
    if ($hash -ne $FfmpegSha256) { Remove-Item $zip; throw "ffmpeg checksum mismatch: $hash" }
    Expand-Archive $zip -DestinationPath 'C:\tools\ffmpeg' -Force
    Remove-Item $zip
    Step "installed: ffmpeg $FfmpegVersion in $FfmpegDir"
}

# --- 4. The .NET 8 SDK and FrameBridge ---------------------------------------------------------------------------------
$dotnet = Get-Command dotnet -ErrorAction SilentlyContinue
$hasSdk = $false
if ($dotnet) { $hasSdk = [bool]((& dotnet --list-sdks 2>$null) -match '^8\.') }
if (-not $hasSdk -and (Test-Path 'C:\tools\dotnet\dotnet.exe')) {
    $dotnet = Get-Item 'C:\tools\dotnet\dotnet.exe'
    $hasSdk = [bool]((& 'C:\tools\dotnet\dotnet.exe' --list-sdks 2>$null) -match '^8\.')
}
if ($hasSdk) {
    Step 'present: .NET 8 SDK'
} else {
    $inst = Join-Path $env:TEMP 'dotnet-install.ps1'
    Fetch 'https://dot.net/v1/dotnet-install.ps1' $inst
    & $inst -Channel 8.0 -InstallDir 'C:\tools\dotnet' -NoPath
    Remove-Item $inst
    $dotnet = Get-Item 'C:\tools\dotnet\dotnet.exe'
    Step 'installed: .NET 8 SDK in C:\tools\dotnet'
}
$DotnetExe = if ($dotnet -is [System.Management.Automation.CommandInfo]) { $dotnet.Source } else { $dotnet.FullName }
$Bridge = Join-Path $Repo 'bridge\FrameBridge'
if (Test-Path "$Bridge\bin\Release\FrameBridge.exe") {
    Step 'present: FrameBridge.exe'
} else {
    & $DotnetExe build -c Release --nologo -v quiet $Bridge
    if ($LASTEXITCODE -or -not (Test-Path "$Bridge\bin\Release\FrameBridge.exe")) { throw 'FrameBridge build failed' }
    Step 'built: FrameBridge.exe (bridge\FrameBridge\bin\Release)'
}

# --- 5. MilestonePSTools -------------------------------------------------------------------------------------------------
if (Get-Module -ListAvailable MilestonePSTools) {
    Step 'present: MilestonePSTools'
} else {
    Install-Module MilestonePSTools -Scope CurrentUser -Force -AllowClobber
    Step 'installed: MilestonePSTools (PowerShell Gallery)'
}

# --- 6. The lens camera --------------------------------------------------------------------------------------------------
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo 'scripts\setup_lens.ps1')
if ($LASTEXITCODE) { throw 'scripts\setup_lens.ps1 failed' }
if (-not $NoStart) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo 'scripts\start_lens.ps1')
    if ($LASTEXITCODE) { throw 'scripts\start_lens.ps1 failed' }
}

# --- 7. Model weights ----------------------------------------------------------------------------------------------------
if ($SkipModels) {
    Step 'skipped: model weights (-SkipModels)'
} else {
    Step 'fetching if missing: YOLO11m (models\yolo11m.pt) and SigLIP 2 (Hugging Face cache); a few minutes the first time'
    & $Python -c "from ultralytics import YOLO; YOLO('models/yolo11m.pt'); from tier0.memory import Embedder; Embedder(); print('models ready')"
    if ($LASTEXITCODE) { throw 'model download failed' }
}

# --- 8. The gateway password ---------------------------------------------------------------------------------------------
if ([Environment]::GetEnvironmentVariable('HAFNIA_GW_PASSWORD', 'User')) {
    Step 'present: HAFNIA_GW_PASSWORD (user-scope environment variable)'
} elseif ($NoPrompt) {
    Step 'missing: HAFNIA_GW_PASSWORD (set it: [Environment]::SetEnvironmentVariable("HAFNIA_GW_PASSWORD", "<password>", "User"))'
} else {
    $secure = Read-Host -AsSecureString 'Hafnia gateway password (the tray icon > Hafnia VLM Settings; stored as a user-scope environment variable, not in a file)'
    $plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure))
    if ($plain) {
        [Environment]::SetEnvironmentVariable('HAFNIA_GW_PASSWORD', $plain, 'User')
        Step 'set: HAFNIA_GW_PASSWORD'
    }
}
$env:HAFNIA_GW_PASSWORD = [Environment]::GetEnvironmentVariable('HAFNIA_GW_PASSWORD', 'User')

# --- 9. Phone pushes (optional) ------------------------------------------------------------------------------------------
if ($Ntfy) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo 'scripts\setup_ntfy.ps1')
}

# --- 10. The owner board -------------------------------------------------------------------------------------------------
if (-not $NoStart) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo 'scripts\start_board.ps1')
}

# --- 11. Check (no request) ----------------------------------------------------------------------------------------------
Step 'checking XProtect and the gateway (no request)'
& $Python (Join-Path $Repo 'scripts\check_setup.py')
if ($LASTEXITCODE) { throw 'scripts\check_setup.py: XProtect could not be reached' }
Step 'done. Next: README.md, "Run it" (a dry run costs no request)'
