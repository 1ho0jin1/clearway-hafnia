# The service below normal priority: XProtect's alarm actions back to a fifth of a second (2026-10-27)

`scripts/run_clearway.py` on all eleven organizer cameras (the five street clips `--real`), 6 minutes, `--alarms
--close-alarms-at-end`, no requests (a dry run's stand-in answers, and its alarms are real XProtect actions named
"[dry run]"). The service and FrameBridge run at below-normal process priority (`clearway/service.py`
`Service(below_normal=True)`, now the default; `--normal-priority` compares), so that XProtect's services and the
API Gateway are scheduled first on a machine our pipeline saturates (`run/clearway-dry-20261027T121705Z-width0`).

| | Clean live run, normal priority (`run/clearway-live-20261027T124112Z-clean`) | This run, below normal |
|---|---|---|
| Seconds per alarm raise (7 raises each) | 14-71, median 19 | 0.16-0.23, median 0.2 (the first, during start-up, 10 s) |
| Frames received per camera per second | 7.5-8.1 | 7.0-7.7 |
| Lens clock: frames per second, offset of the recording against the publisher | 6.2, +0.29 to +0.47 s | 6.7, +0.01 to +0.02 s |
| CPU: machine / Recording Server / FrameBridge / service | 100 / 1.6 / 29 / 54 % | 100 / 0.7 / 31 / 55 % |
| Cards, alarms, bookmarks, errors | 7, 7, 8, 0 | 7, 7, 8, 0 |

The machine is as full as before and our pipeline loses almost nothing, but everything that is not ours answers at
once: the API Gateway's REST calls (M3's 35-62 s per action were this, not XProtect being slow), the Recording
Server's RTSP reader of the lens stream (the lens recording's delivery latency gone), MediaMTX and ffmpeg. The lens
publisher stays at normal priority: it is a camera.
