<#
start_board.ps1 - start the Clearway owner board (clearway\board.py) on http://127.0.0.1:8765/.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\start_board.ps1 [-Run run\clearway-live-<UTC>]

Without -Run the board follows the newest run\clearway-* folder and switches when a new run starts. It runs detached
(it survives the Claude Code or PowerShell session), logs to run\board\, and is started only if it is not already
running, so running this again changes nothing. It listens on 127.0.0.1 only: Smart Client on this machine shows it in
an HTML page view item. Stop it by ending the python.exe whose command line contains clearway.board.
#>
param([string]$Run = '')
$ErrorActionPreference = 'Stop'
$Repo = Split-Path $PSScriptRoot -Parent
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
$Log = Join-Path $Repo 'run\board'
New-Item -ItemType Directory -Force $Log | Out-Null

$board = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" | Where-Object CommandLine -like '*clearway.board*'
if ($board) {
    Write-Host "present: board (pid $($board.ProcessId -join ', '))"
} else {
    $source = if ($Run) { @('--run', $Run) } else { @('--latest') }
    Start-Process -FilePath $Python -ArgumentList (@('-u', '-m', 'clearway.board') + $source) -WorkingDirectory $Repo `
        -WindowStyle Hidden -RedirectStandardOutput "$Log\board.out.log" -RedirectStandardError "$Log\board.err.log" | Out-Null
    Write-Host 'started: board on http://127.0.0.1:8765/'
}
