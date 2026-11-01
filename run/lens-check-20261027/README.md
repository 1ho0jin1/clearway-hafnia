# Lens check (2026-10-27): what `lens_1` recorded against what the publisher sent during M3

Done by the investigation of 2026-10-27, before M3's recordings expired
(24 h retention, about 14:16 UTC). No Hafnia requests. `export.ps1` saved one recorded frame per second of `lens_1`
around seven of M3's asked spans (`Get-Snapshot`, MilestonePSTools); `sheets.py` tiled them (rows marked REC, with
the recorded timestamp) under frames of the clip the publisher sent for that question (rows marked SENT, from the
spool AVI `run/lens/spool/<job>.avi`, with the span the publisher logged in `run/lens/played.jsonl`). The sheets are
footage, so they live in `frames/` (git-ignored).

## Result

The recording's timestamps do not follow the publisher's wall clock. Content the publisher wrote at wall time W is
found in the recording at an earlier timestamp. The offset (recorded time minus the wall time of the same content):

| Question | Asked span (UTC) | What the asked span held in the recording | Offset |
|---|---|---|---|
| cw-0001 tracks | 14:16:36-43 | the tracks clip (right) | about -0.3 s |
| cw-0004 gate | 14:17:10-14 | 1 s of the gate clip's end, then idle, then from 14:17:13.96 the **tracks** clip (published 14:17:21) | -3 s growing to -7 s |
| cw-0009 bin | 14:17:59-18:03 | idle, then from 14:18:01.0 the **breakdown** clip (published 14:18:10.3) | about -9.4 s |
| cw-0015 gate | 14:19:05-10 | idle frames only; the crowd clip (published 14:19:17.5) from 14:19:09.1 | about -8.4 s |
| cw-0022 tracks | 14:20:46-50 | idle, then from 14:20:49.0 the **roadworks** clip (published 14:20:56.2) | about -7.2 s |
| cw-0027 gate | 14:41:16-21 | the gate clip's last 3 s and idle (its first 1.5 s fell before the span) | about -1.5 s |
| cw-0032 e-scooter | 15:14:05-10 | the clip's last 2 s (scooter already gone) and idle: answered NONE | about -2.2 s |

So four of M3's six wrong answers (cw-0004, cw-0009, cw-0015, cw-0022) and one of its two "doubtful" NONEs (cw-0032)
were given on footage other than the clip that was asked about, and every answer, including the right ones outside
the start-up minutes, lost the first 1.5-3 s of its clip (the 2 s BEFORE margin) and gained idle frames at the end.
The publisher's log is right about what it sent and when (`played.jsonl` spans match the service's asked spans
within 1 s); the service's `lens.client.span()` assumes the recording runs 0.3 s *behind* the sending, and the
sign is the other way.

## Why (what is known)

- `run/lens/mediamtx.out.log`: XProtect's RTSP reader was too slow for MediaMTX during the start-up minutes, which
  discarded frames in bursts (14:16:42: 172 and 204 frames; 14:19:40: 98; 14:20:17: 238; 14:20:52: 24; and during
  the 14:10 preflight 39, 102, 327, 61, 5, 268). The Recording Server was starved.
- `lens/publisher.py` resynchronises instead of bursting when it falls more than 1 s behind, so under load the
  stream carries fewer frames than wall seconds; ffmpeg stamps the raw frames by count (`-r 10`, no
  `-use_wallclock_as_timestamps`), so the stream's own time falls behind the wall clock.
- The Universal driver evidently timestamps by the stream's time, not by arrival (arrival stamping could not put
  content before the moment it was written). How it re-anchors is not known: the offset shrank from about -9 s
  (14:18) to about -1.5 s (14:41) without an ffmpeg restart (one "starting ffmpeg" line since 2026-10-25 08:16) and
  without a new MediaMTX session.

## What to do (see the investigation report, section 4)

Do not trust the lens camera's time base. Ask about the source camera directly where the spot is large enough, and
when the lens is used, burn a machine-readable timecode into its frames and read one recorded frame back before
asking (or at least test ffmpeg's `-use_wallclock_as_timestamps 1` and keep idle gaps longer than the largest
offset, so a wrong span can only pull in idle frames, never a neighbouring clip).
