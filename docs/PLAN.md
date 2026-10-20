# Plan

Solo entry, 2026-10-18 → submission about 2026-10-30. Deliverable: this repository (a demo video is optional).
Judging weighs **creativity and validity** most; reproducibility counts, but a best-effort setup is enough.

**Scope (decided 2026-10-18): traffic incidents, analysed from what happens in the scene.** No camera-status checks
(fog, condensation, blocked, moved, tampered or looped feeds), and no crime or security incidents: every Hafnia model is
a traffic model, and it scored 0 of 8 on robberies and shootings while getting 8 of 9 accident answers right
(`run/bench-20261018`). Security rows in the tables below are out of scope.

## Concept: verified, prioritized incidents

Cheap detection on the machine proposes *candidate incidents* from what it sees. Hafnia verifies each candidate, names
its type and describes it, and the type decides who gets the alarm and how urgent it is. This covers the organizers'
"intelligent alerting" category (alarm verification and incident prioritization) and "smart dashboards"; a structured
incident record also touches "video summaries".

```
frames ─► Tier 0 (machine, GPU) ──────► Router ──────────────► Hafnia (keyword prompt) ──► XProtect alarm
          detection + tracking;         dedupe, severity,       verify, classify,          unverified → verified
          candidate + event time        budget, learned trust   describe                   priority + owner + bookmark
                                              ▲                        │
                                              └─ verdict = free label for tier 0 ◄┘
```

Why this split: tier 0 is fast and free but only sees boxes and tracks; Hafnia understands the scene but costs a
request and about 5 s. In our measurements Hafnia's answer depends on what the clip contains (the 5 s vandalism clip
missed the throw because of where the window fell). Tier 0 knows when the event happened, so it can choose the clip.

### Creative hooks

1. **Detect → verify → classify → route.** Accident or collision → traffic operations, urgent. Stopped vehicle → traffic
   operations, high. Person on the road → traffic operations, urgent. Vandalism → security, high. Not confirmed →
   alarm closed as a false alarm, kept for statistics.
2. **Event-centred clip windows.** Tier 0 sends the clip around the moment it detected the event instead of "the last
   N seconds". Measured against fixed windows on the same events.
3. **Learned trust.** Each Hafnia verdict labels a tier 0 detection. Per camera and event type the router keeps a
   precision estimate, adjusts thresholds, and spends budget where it matters. Claim to measure: requests per day fall
   over time while missed incidents stay flat.

## Components

| # | Component | How |
|---|---|---|
| 1 | Frame source | Live JPEGs via the XProtect REST camera task `JpegGetLive`; rate measured on day 1. Fallback for higher frame rates: MIP SDK (C#). Offline development reads video files directly. |
| 2 | Tier 0, incidents (GPU, CPU fallback) | Object detection and tracking. Rules: sudden stop or collision, stopped vehicle, person on the road, throw or loitering at a building. Each candidate carries a confidence and the event time. Check the detector's licence (Ultralytics YOLO is AGPL-3.0). |
| 3 | Router | Dedupe per camera and event type (clips loop), severity and confidence, daily budget from `DailySummaryCount`, learned trust per camera and event type, event-centred clip window. |
| 4 | Hafnia prompts | One saved prompt per event type, sent with `PromptId` so gateway rules apply, e.g. `ACCIDENT_CONFIRMED` / `NO_ACCIDENT`, `STOPPED_VEHICLE` / `TRAFFIC_NORMAL`, `PERSON_ON_ROAD` / `ROAD_CLEAR`, `VANDALISM_CONFIRMED` / `NO_VANDALISM`. Day 4 decides between one prompt (keyword + short description) and two requests (verify, then describe). |
| 5 | XProtect plumbing | Tier 0 → analytics event → **unverified** alarm at low priority. Hafnia answer → alarm raised in priority, or closed as a false alarm (Alarms REST). We write a bookmark with the answer ourselves (Bookmarks REST): only webhook requests get one automatically. |
| 6 | Dashboard (served from the machine) | Incident timeline with each tier's time, verified vs suppressed alarms, budget gauge, learned-trust table, incident records with Hafnia's description. Maybe embedded in Smart Client (web-page view item: to verify on 2026 R1). |
| 7 | Evaluation harness | Ground truth per clip (labelled offline, Opus as judge). Ablations: tier 0 only, Hafnia on everything, tiered, tiered with event-centred windows, tiered with learned trust. Metrics: alarm precision and recall, false alarms suppressed, requests per day, time to alarm. |

## Clips

| Clip | Source | Use |
|---|---|---|
| 5 organizer cameras | on every machine | `vandalism` (security), `traffic_flows_in_the_open_lanes` and `highway_traffic_overcast_weather` (normal traffic: false-alarm tests), `busy_street` (crowd, pedestrians) |
| Accident clip(s) | public footage with a licence that allows it: to find | the core traffic story |
| More incident clips | stopped vehicle, person on the road, other security events: to find, same licence check | broaden the labelled set |
| `construction_aerial` | the participant's (source: TODO) | probably not used (no incident) |

All new clips go in with **one** Recording Server restart; afterwards a "test bench" camera swaps clips live.

## Schedule

| Day | Date | Work | Hafnia requests | Done when |
|---|---|---|---|---|
| 1 | Oct 18 | Push to GitHub. Hung-service fallback and batch support in `add_test_camera.ps1`. Find accident and incident clips, check licences, convert. One restart for the batch. Measure the `JpegGetLive` frame rate. | 0 | clips play as cameras; frame rate known |
| 2 | Oct 19 | GPU decision (driver install: ask first, may need a reboot); detection and tracking running offline on the clips | 0 | detector and tracker at a known frame rate |
| 3 | Oct 20 | Tier 0 incident rules and the labelled clip set; offline evaluation | 0 | precision and recall per event type recorded |
| 4 | Oct 21 | Hafnia prompt tuning (verify and classify), Opus as judge; fixed vs event-centred window experiment | ~80 | ≥ 90% correct keyword on the labelled clips, window effect measured |
| 5 | Oct 22 | XProtect plumbing: basic user, analytics events, alarm definitions with priorities, Python helpers (events, alarms, bookmarks) | 0 | an alarm raised, re-prioritized and closed from Python |
| 6–7 | Oct 23–24 | **End-to-end slice, live:** tier 0 → router → Hafnia → alarm and bookmark; first ablation numbers | ~60 | an incident on a camera gives a verified, prioritized alarm on its own |
| 8 | Oct 25 | Learned trust in the router, measured over a replayed day | ~40 | requests fall while recall holds |
| 9–10 | Oct 26–27 | Dashboard | 0 (stored answers) | operator view complete |
| 11 | Oct 28 | Final evaluation and report | ~150 | measured results and charts committed |
| 12 | Oct 29 | Half-day best-effort `setup.ps1` and README; optional demo video | ~20 | documented setup |
| 13 | Oct 30 | Spare time, submission | | |

## Risks

| Risk | Fallback |
|---|---|
| No licensed accident clip | Vandalism, stopped vehicle and person on the road carry the demo |
| `JpegGetLive` too slow | Lower frame rate for slow events; MIP SDK (C#) for fast ones |
| GPU driver needs a reboot | Ask first; meanwhile CPU detection at a low frame rate |
| Hafnia misclassifies incidents | Report the measured accuracy honestly; keep tier 0's type with a lower priority |

## Status and TODO (2026-10-19)

Done: Hafnia benchmarks (latency, recognition, event-centred windows, models), tier 0 offline (4 of 5 accidents),
FrameBridge live frames at 10 fps, the live pipeline end to end (`run/live-20261018T142327Z`), the pipeline page, and
the measured comparison below.

Note on numbers from the test cameras: they loop 12–17 s clips, so a "5-minute run" replays each accident about 20
times and a 36 s span holds 2–3 replays. Count accident cameras caught, not impacts or raw candidates.

### Measured: tiered vs Hafnia-only polling (`run/compare-20261019/README.md`)

Same 36 s of recording on 7 cameras (5 accident, 2 normal traffic); ground truth located by frame matching.

| | Hafnia-only polling (6 s windows) | Tiered |
|---|---|---|
| Hafnia requests | 42 | 5 |
| Accident cameras caught | 5 of 5 | 3 of 5 |
| Alarms raised | 21 | 3 |
| False alarms | 2 | 0 |
| Median impact → verdict | 9.8 s | 7.8 s (plus an unverified alarm in under 1 s, live) |

Tiered misses: `test_01` (tier 0 never detects the struck rider) and `test_03` (router: Hafnia rejected a candidate
4.6 s before the impact, and muting that spot and the camera suppressed the real impact's 32 candidates).

### TODO

- [ ] **Router: after a rejection, mute only candidates inside the window Hafnia already checked**; later candidates
      get their own check. Would have recovered `test_03` and caught `test_05` at its first impact.
- [ ] **Re-run the tiered side of `scripts/bench_tiered_vs_polling.py` after the router fix** (about 5–10 requests)
      and update `run/compare-20261019` or add a new run; goal 4 of 5 accident cameras, still 0 false alarms.
- [ ] Router: check the daily budget before `decide()` (today `decide()` counts the request and starts the cooldown
      even when the budget check then blocks it).
- [ ] Router: use tier 0's score and candidate type; rank candidates across cameras when the budget is tight.
- [ ] Recall: tier 0 misses `test_01`. Options: a low-rate polling fallback per camera (polling caught every accident
      camera, so a few checks an hour would cap the miss time cheaply), better small-object detection, an aftermath
      trigger. Measure the fallback's cost and recall with the same benchmark.
- [ ] Learned trust: per camera and spot, how often Hafnia agreed with tier 0, feeding thresholds (today: only muting
      rejected spots for 10 minutes).
- [ ] The free description contradicted a confirmed accident: test a description prompt that assumes the accident, or
      put only the verified label on the alarm.
- [ ] Aftermath candidates (people around a fallen bike): their own incident type, or accepted as closed.
- [ ] Operator dashboard from the pipeline page, live.
- [ ] Footage sources and licences for `data/` (needed before any frames are shared).
