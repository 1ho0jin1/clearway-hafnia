# Eleven cameras, dry run: hotspots (F9) and the M3 preflight (2026-10-26)

`scripts/run_clearway.py` on all eleven organizer cameras (the six synthetic incident clips at the loops setting, the
five street clips `busy_street`, `highway_traffic_overcast_weather`, `city_street_7_condensation_inside_housing`,
`vandalism`, `traffic_flows_in_the_open_lanes` at the real-camera setting, `--real`) for 3 minutes, `--alarms
--close-alarms-at-end --notify`, the stand-in answering: no Hafnia requests. The first run with scene images
(`cameras/`, the detector's slow background), which the shift summary's hotspots are drawn over.

- **Frames:** FrameBridge delivered 4.0-5.0 fps per camera with eleven cameras (about 45 fps in all; 9.8-9.9 fps each
  with six, `run/clearway-live-20261025T083623Z`). The service processed every frame it received: 0 dropped, lag about
  1 s, 0 errors. Detector and zone times are in seconds, so they hold; the danger zone looks at about 2.3 fps.
- **XProtect at start-up:** while eleven streams, the lens and the models started (the run's first 3 minutes), every
  XProtect call was slow: the first alarm took 116 s (trigger 60 s, snapshot 21 s, bookmarks 35 s), the second 15 s;
  from then on 0.2-0.3 s each. 8 alarms raised and closed, 0 errors. A 3-minute run's "card to XProtect alarm" (76 s
  median) is this start-up, not the steady state.
- **Cards:** 8 incidents on the six incident cameras (two pieces each on the tracks and the breakdown not merged), 17
  questions, 0 on the five street cameras: at the real-camera setting a change must last 15 s, longer than their 8 s
  loops (and `busy_street`'s 15.5 s), so they report nothing. 8 owner messages, all delivered.
- **Lens queue:** the start-up burst of 17 clips played one after another; the last waited 130 s.
- **Hotspots:** the summary page (`/summary`, "Where it keeps happening") shows each camera's scene with its spots
  outlined in the owner's priority colour and labelled with their counts, what was not an incident dashed grey, and
  the heat of every reported change (one hue, the same scale on every camera). On the gate the heat is the lit
  pavement the detector keeps reporting (the card's own box spans it).
