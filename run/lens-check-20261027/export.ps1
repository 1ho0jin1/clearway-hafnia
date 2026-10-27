$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
Import-Module MilestonePSTools
Connect-Vms -ServerAddress 'http://localhost' -AcceptEula | Out-Null
$cam = Get-VmsCamera | Where-Object Name -eq 'lens_1' | Select-Object -First 1
if (-not $cam) { throw "lens_1 not found" }
$root = $args[0]
$spans = @(
  @{ id='cw-0001'; s='2026-10-26T14:16:36Z'; e='2026-10-26T14:16:44Z' },
  @{ id='cw-0004'; s='2026-10-26T14:17:08Z'; e='2026-10-26T14:17:26Z' },
  @{ id='cw-0009'; s='2026-10-26T14:17:57Z'; e='2026-10-26T14:18:15Z' },
  @{ id='cw-0015'; s='2026-10-26T14:19:03Z'; e='2026-10-26T14:19:20Z' },
  @{ id='cw-0022'; s='2026-10-26T14:20:44Z'; e='2026-10-26T14:21:00Z' },
  @{ id='cw-0027'; s='2026-10-26T14:41:14Z'; e='2026-10-26T14:41:24Z' },
  @{ id='cw-0032'; s='2026-10-26T15:14:03Z'; e='2026-10-26T15:14:13Z' }
)
foreach ($sp in $spans) {
  $dir = Join-Path $root $sp.id
  New-Item -ItemType Directory -Force $dir | Out-Null
  $from = [datetime]::Parse($sp.s, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal)
  $to = [datetime]::Parse($sp.e, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::AdjustToUniversal)
  $n = 0
  for ($t = $from; $t -lt $to; $t = $t.AddMilliseconds(1000)) {
    $snap = Get-Snapshot -Camera $cam -Timestamp $t -ErrorAction SilentlyContinue
    if (-not $snap -or -not $snap.Bytes) { continue }
    $ms = [long]([DateTimeOffset]$snap.DateTime.ToUniversalTime()).ToUnixTimeMilliseconds()
    $file = Join-Path $dir "$ms.jpg"
    if (Test-Path $file) { continue }
    [IO.File]::WriteAllBytes($file, $snap.Bytes)
    $n++
  }
  "$($sp.id): $n frames"
}
Disconnect-Vms
