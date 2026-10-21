<#
start_lens.ps1 - start the lens camera's video source: MediaMTX (RTSP on 127.0.0.1:8554 only) and lens\publisher.py.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_lens.ps1

Both run detached (they survive the Claude Code or PowerShell session) and log to run\lens\. Each is started only if
it is not already running, so running this again changes nothing. After the publisher (re)starts, XProtect resumes
recording lens_1 only about 10 s later (measured 2026-10-21): queue clips 15 s after a start, and keep it running. scripts\setup_lens.ps1 installs MediaMTX and adds
the lens_1 camera; run it once first. Stop both with: Get-Process mediamtx | Stop-Process; and end the python.exe
whose command line contains lens.publisher.
#>
$ErrorActionPreference = 'Stop'
$Repo = Split-Path $PSScriptRoot -Parent
$MediaMtx = 'C:\tools\mediamtx\v1.21.2\mediamtx.exe'
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
$Log = Join-Path $Repo 'run\lens'
New-Item -ItemType Directory -Force $Log | Out-Null

if (Get-Process mediamtx -ErrorAction SilentlyContinue) {
    Write-Host 'present: MediaMTX'
} else {
    if (-not (Test-Path $MediaMtx)) { throw "MediaMTX not found at ${MediaMtx}: run scripts\setup_lens.ps1 first" }
    Start-Process -FilePath $MediaMtx -ArgumentList (Join-Path $Repo 'lens\mediamtx.yml') -WorkingDirectory (Split-Path $MediaMtx) `
        -WindowStyle Hidden -RedirectStandardOutput "$Log\mediamtx.out.log" -RedirectStandardError "$Log\mediamtx.err.log" | Out-Null
    Write-Host 'started: MediaMTX'
}

$publisher = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object CommandLine -like '*lens.publisher*'
if ($publisher) {
    Write-Host "present: lens publisher (pid $($publisher.ProcessId -join ', '))"
} else {
    Start-Process -FilePath $Python -ArgumentList '-u', '-m', 'lens.publisher' -WorkingDirectory $Repo -WindowStyle Hidden `
        -RedirectStandardOutput "$Log\publisher.out.log" -RedirectStandardError "$Log\publisher.err.log" | Out-Null
    Write-Host 'started: lens publisher'
}
