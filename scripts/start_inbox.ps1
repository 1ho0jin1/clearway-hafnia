<#
start_inbox.ps1 - start the owner inbox (scripts\owner_inbox.py) on http://127.0.0.1:8770/: a stand-in for the owners'
own channels that receives Clearway's owner notifications (scripts\run_clearway.py --notify).

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_inbox.ps1

It runs detached, logs to run\inbox\, keeps what it received in run\inbox\received.jsonl (git-ignored: snapshots are
camera footage), and is started only if it is not already running. With CLEARWAY_HOOK_SECRET set in this session it
checks each message's signature (the same variable named as secret_env in config\owners.json). Stop it by ending the
python.exe whose command line contains owner_inbox.
#>
$ErrorActionPreference = 'Stop'
$Repo = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
$Log = Join-Path $Repo 'run\inbox'
New-Item -ItemType Directory -Force $Log | Out-Null

$inbox = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object CommandLine -like '*owner_inbox*'
if ($inbox) {
    Write-Host "present: owner inbox (pid $($inbox.ProcessId -join ', '))"
} else {
    Start-Process -FilePath $Python -ArgumentList '-u', (Join-Path $Repo 'scripts\owner_inbox.py') -WorkingDirectory $Repo `
        -WindowStyle Hidden -RedirectStandardOutput "$Log\inbox.out.log" -RedirectStandardError "$Log\inbox.err.log" | Out-Null
    Write-Host 'started: owner inbox on http://127.0.0.1:8770/'
}
