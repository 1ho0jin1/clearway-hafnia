<#
open_board.ps1 - open the Clearway owner board (http://127.0.0.1:8765/, scripts\start_board.ps1) as its own window:
Microsoft Edge in app mode, no tabs or address bar, to sit beside XProtect Smart Client.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\open_board.ps1

Why not inside Smart Client: its HTML page view item shows standard display mode with the legacy Edge engine
(EdgeHTML, the Windows Community Toolkit's WebViewCompatible) and otherwise falls back to Internet Explorer in IE 7
mode, which cannot run the board. On this Windows Server 2022 machine it fell back every time: elevated (the built-in
Administrator), with the Administrators group removed, and at Medium integrity, with either rendering-engine value in
the view item (2026-10-25). The board stays a page of its own; alarms and bookmarks are in Smart Client.
#>
$ErrorActionPreference = 'Stop'
$Edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
if (-not (Test-Path $Edge)) { throw "Microsoft Edge not found at ${Edge}" }
try { Invoke-RestMethod 'http://127.0.0.1:8765/api/board' -TimeoutSec 5 | Out-Null }
catch { throw 'The board is not running: start it with scripts\start_board.ps1' }
Start-Process -FilePath $Edge -ArgumentList '--app=http://127.0.0.1:8765/', '--window-size=1600,900'
Write-Host 'opened: the Clearway board in its own window'
