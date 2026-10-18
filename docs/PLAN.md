# Plan

Solo entry, 2026-10-18 → submission about 2026-10-30. Deliverable: this repository (a demo video is optional).
Judging weighs **creativity and validity** most; reproducibility counts, but a best-effort setup is enough.

## Concept: diagnose, don't just detect

Cheap checks on the machine notice that *something changed*. Hafnia explains *why*, and the cause decides *who* gets
the alarm and how urgent it is. This covers three of the organizers' example categories: intelligent alerting
(alarm verification and incident prioritization), camera intelligence (moved, blocked or tampered cameras), and
smart dashboards.

```
frames ─► Tier 0 (machine; CPU for camera health, GPU for incidents) ─► Router ─► Hafnia (keyword prompt) ─► XProtect alarm
             change detected, confidence        dedupe, severity,      cause or        unverified → verified
                                                budget, learned trust   confirmation   priority + owner + bookmark
                                                      ▲                      │
                                                      └── verdict = free label for tier 0 (learned trust) ◄┘
```

Why this split: in our measurements tier 0 is exact at *measuring* change (sharpness, contrast, shift, blocked area,
repeating frames), while Hafnia missed lens condensation on its own (`run/bench-20261015/compare.html`). Tier 0 points
Hafnia at the problem; Hafnia supplies the cause. Whether Hafnia can name the cause reliably is tested on day 3.

### Creative hooks

1. **Change → cause → owner.** Tampering or blocking → security, urgent. Condensation or dirt → maintenance, low. Fog
   → traffic operations, advisory. Accident → traffic operations, urgent.
2. **Learned trust.** Each Hafnia verdict labels a tier 0 detection. Per camera and event type the router keeps a
   precision estimate, adjusts thresholds, and spends budget where it matters. Claim to measure: requests per day fall
   over time while missed incidents stay flat.
3. **Cross-camera context** (optional extra). Fog on several cameras in an area is weather; on one camera it is the
   lens. Needs a small site map.

## Components

| # | Component | How |
|---|---|---|
| 1 | Frame source | Live JPEGs via the XProtect REST camera task `JpegGetLive`; rate measured on day 1. Fallback for high frame rates: MIP SDK (C#). |
| 2a | Tier 0, camera health (CPU, OpenCV) | Reference image per camera (by name). Sharpness (variance of the Laplacian), contrast, shift vs reference (feature matching), blocked area (detail lost in a region), repeating frame fingerprints (loop or replay). |
| 2b | Tier 0, incidents (GPU, CPU fallback) | Object detection and tracking; rules for sudden stop or collision, stopped vehicle, person on the road, throw or loitering at a building. Check the detector's licence (Ultralytics YOLO is AGPL-3.0). |
| 3 | Router | Dedupe per camera and event type (clips loop), severity and confidence, daily budget from `DailySummaryCount`, learned trust per camera and event type. |
| 4 | Hafnia prompts | One saved prompt per event type, sent with `PromptId` so gateway rules apply. Keywords: `ACCIDENT_CONFIRMED` / `NO_ACCIDENT`; `TAMPERING` / `CONDENSATION` / `WEATHER` / `VIEW_CLEAR`; `VANDALISM_CONFIRMED` / `NO_VANDALISM`. |
| 5 | XProtect plumbing | Tier 0 → analytics event → **unverified** alarm at low priority. Hafnia answer → alarm raised in priority, or closed as a false alarm (Alarms REST). We write a bookmark with the answer ourselves (Bookmarks REST): only webhook requests get one automatically. |
| 6 | Dashboard (served from the machine) | Camera health grid (reference vs live, scores, cause), timeline per incident with each tier's time, budget gauge, verified vs suppressed alarms, learned-trust table. Maybe embedded in Smart Client (web-page view item: to verify on 2026 R1). |
| 7 | Evaluation harness | Ground truth per clip (labelled offline, Opus as judge). Ablations: tier 0 only, Hafnia on everything, tiered, tiered with learned trust. Metrics: alarm precision and recall, false alarms suppressed, requests per day, time to alarm. |

## Clips

| Clip | Source | Use |
|---|---|---|
| 5 organizer cameras | on every machine | baseline; vandalism; condensation and fog for camera health |
| Tampering variants | generated with ffmpeg from the organizer clips (shifted or rotated, covered region, heavy blur, frozen frame, abrupt cut) | camera health; no licence issue, rebuildable on a fresh machine |
| Accident clip(s) | public footage with a licence that allows it: to find | incident detection |
| `construction_aerial` | the participant's (source: TODO) | "camera moved" test case, or drop it |

All clips go in with **one** Recording Server restart; afterwards a "test bench" camera swaps clips live.

## Schedule

| Day | Date | Work | Hafnia requests | Done when |
|---|---|---|---|---|
| 1 | Oct 18 | Push to GitHub. Hung-service fallback and batch support in `add_test_camera.ps1`. Generate tampering clips; find accident clips and check licences. One restart for the batch. Measure the `JpegGetLive` frame rate. | 0 | all clips play as cameras; frame rate known |
| 2 | Oct 19 | Tier 0 camera health and the labelled clip set; measured on all clips | 0 | tampered clips flagged, normal clips quiet; precision and recall recorded |
| 3 | Oct 20 | Prompt tuning (cause and accident prompts), Opus as judge | ~60 | ≥ 90% correct keyword, or a documented "Hafnia can't" with tier 0 rules as the fallback |
| 4 | Oct 21 | XProtect plumbing: basic user, analytics events, alarm definitions with priorities, Python helpers (events, alarms, bookmarks) | 0 | an alarm raised, re-prioritized and closed from Python |
| 5–6 | Oct 22–23 | **First slice:** camera health → router → Hafnia → alarm and bookmark; first ablation numbers | ~50 | tampering a camera gives a verified, prioritized alarm on its own |
| 7 | Oct 24 | Learned trust in the router, measured over a replayed day | ~40 | requests fall while recall holds |
| 8 | Oct 25 | GPU decision (driver install: ask first, may need a reboot) and a detection and tracking test | 0 | detection running at a known frame rate |
| 9–10 | Oct 26–27 | Incident detection (accident, vandalism, person on the road) through the router | ~60 | second story end to end, measured |
| 11 | Oct 28 | Dashboard | 0 (stored answers) | operator view complete |
| 12 | Oct 29 | Final evaluation and report; half-day best-effort `setup.ps1` and README; optional demo video | ~150 | measured results and charts committed |
| 13 | Oct 30 | Spare time, submission | | |

## Risks

| Risk | Fallback |
|---|---|
| `JpegGetLive` too slow | Camera health still works at 1 frame a second; incidents via MIP SDK (C#) |
| GPU driver needs a reboot | Scheduled after the first slice works; CPU detection at a low frame rate |
| Hafnia cannot name causes | Tier 0 rules decide the cause; report the measured result honestly |
| No licensed accident clip | Demo vandalism and person on the road instead |
