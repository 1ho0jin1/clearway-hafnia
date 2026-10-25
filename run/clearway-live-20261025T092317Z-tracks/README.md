# Person on the tracks (F5): the danger-zone trigger, live (2026-10-25)

`scripts/run_clearway.py --cameras person_on_railway_tracks --answers hafnia --max-requests 3 --minutes 3 --alarms
--close-alarms-at-end`. **2 requests.**

## Why a trigger of its own

The change detector holds people back by design (a person standing still is not an obstruction), so it saw the
person on the tracks in only 1–2 of 20 loops (`run/ledger-F1`, `run/clearway-live-20261025T083623Z`). F5 adds a
person trigger (`tier0/zones.py`): YOLO11m looks for people on every 2nd frame (5 fps) of a camera with a danger zone;
a person whose feet (the bottom centre of the box) stay inside the zone's polygon for 1 s is reported to the ledger
like a change (pieces, recurrences, questions as usual); the occupation closes after 2 s with nobody inside.

**The polygon** (`config/zones.json`, the only per-camera setting, in shares of the image): everything beyond the near
platform's yellow tactile strip, the platform edge and the track bed, up to the far platform's wall: the rule "stay
behind the yellow line". The strip's track-side edge was fitted by colour on the camera's clip (x = 0.921 y + 31.5 px
at 832×480, 132 of 137 rows, 1.6 px spread). People on both platforms stay outside; the person in red is inside from
6.2 s into the loop (sitting on the edge, legs on the track) until 13.4 s (climbing onto the far platform). Offline,
4 loops: reported 4 of 4 times, at 7.2 s.

## Result

| | |
|---|---|
| Questions | 2: the zone trigger (`cw-0001`, box of the person) and a detector piece of the same moment (`cw-0002`) |
| Hafnia | PERSON_ON_TRACKS 2 of 2 (the stand-in agrees), 6.2 s each; the second merged into the first card |
| Hafnia's summary (in the alarm) | "A person in a red jacket crawls along the edge of the platform and settles onto the railway tracks, remaining there as the clip ends." |
| Card | one, 12 occurrences in 3 min; first card 20.3 s after the feet entered the zone, every later one 1.0 s after, no request |
| XProtect | one High alarm "Clearway: PERSON_ON_TRACKS, Rail control" on the camera, snapshot, bookmarks on the camera and on lens_1; 0.78 s for all of it (trigger 0.55 s, snapshot 0.12 s, bookmarks 0.11 s); closed by the test harness at the end |

The six-camera dry run with the trigger (`run/clearway-dry-20261025T091654Z`, no requests): the tracks card gathered
22 occurrences in 5 min (20 from the zone, 2 from the detector) instead of 2; the other five cameras as before; 6 of 6
alarms right.
