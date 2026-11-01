# Plan B: near-miss observatory (proposal, 2026-10-20; revised 2026-10-21)

Status: **proposal, not decided.** `docs/PLAN.md` (verified, prioritized accident alarms) stays the current plan until
the participant chooses. Submission about 2026-10-30. Judging weighs creativity and validity most.

**In one paragraph.** Crashes are rare; near misses happen every hour. Tier 0 measures every interaction between road
users for free. Hafnia checks a random sample of the near misses tier 0 flags, so the dashboard shows near-miss
counts with confidence intervals instead of raw detector output. The accident pipeline we already have stays as the
real-time top layer. The 500-a-day allowance stops being something to work around and becomes the design: we do not
need Hafnia to check every event, only enough of them to make the counts trustworthy. A **lens camera** makes the
checks better: Hafnia only sees what XProtect records, so we render what it should look at (the candidate's region,
enlarged, in slow motion, with the road users marked) and play that back as a camera of its own.

## Why consider a change (research, 2026-10-19 and 10-21)

- **Our current concept is Milestone's own pitch.** Hafnia was fine-tuned for "alert validation" (an upstream alert
  goes in, confirm or discard comes out) and Milestone advertises "+4.4% alert-verification accuracy". NVIDIA's VSS
  blueprint ships an alert-verification service. Judges from Milestone and NVIDIA know "detector → VLM verifies".
- **Search and Q&A are taken.** Milestone announced AI Search in March 2026.
- **Hafnia's trained formats** (Milestone's technical article): clips of about 30 s at 2 fps; three JSON tasks:
  AlertValidation (alert type and confidence in; `confirm`/`discard`, reason, evidence frames out), MonitoringSummary
  (weather, light, visibility, road state, event counts) and IncidentReport (type, parties, key moments, cause).
  None of our prompts use them yet.
- **No product or paper found that audits near-miss counts with a VLM.** A Kansas DOT study notes that the accuracy of
  commercial near-miss tools has not been independently checked.

A measured ML contribution (the lens) matters most if it is shown as a product capability ("verdicts stay right at
night and for small road users"), not as a benchmark score.

## What a near miss is, and who needs it

A near miss (a *traffic conflict*) is a moment when two road users would have collided had neither braked, swerved or
changed speed: a turning car cuts across a cyclist who brakes hard; a pedestrian steps out and a car stops just short.
Measured from tracks with surrogate safety measures:

- **Time to collision (TTC):** seconds until they would collide if both kept speed and direction.
- **Post-encroachment time (PET):** the gap between the first road user leaving a spot and the second arriving there.
- FHWA's SSAM tool counts a conflict at TTC ≤ 1.5 s and PET ≤ 5 s by default.

Why it matters: an intersection has a handful of reported crashes a year, so judging its safety from crash records
takes years and comes after people are hurt. Near misses are far more frequent, so weeks of video give a usable
signal: to rank intersections (Bellevue screened 40 cameras, Ann Arbor 61 under a federal Safe Streets grant, Fremont
37 with Derq), to judge a fix in weeks instead of years, and to see which conflict type needs fixing.

**Users:** traffic-safety engineers and planners, not control-room operators. A near miss is not dispatched, so the
output is a dashboard and report. Crashes stay real-time alarms for the operator.

**Where Hafnia adds value:** track-based conflict detection produces false conflicts (lost tracks, occlusion, box
jitter, boxes that overlap only in perspective). Hafnia answers whether someone really braked, swerved or jumped aside.

## Concept: the safety pyramid

```
                 crash       Tier 0 candidate → Hafnia check (every one) → XProtect alarm      real time
                 ─────       (the existing pipeline in incident/, scripts/run_live.py)
            near miss        Tier 0 candidate → lens clip → Hafnia checks a random sample →    hourly
           ───────────       estimated count ± 95% interval per camera, type, hour; bookmarks
      every interaction      Tier 0 only (tracks, PET, TTC): exposure, conflict-rate base      free
   ───────────────────────
```

Budget: crash checks come first. Audits get what is left of the day's cap, paced over the hours left, so no request
goes unused at midnight. A reserve stays for the demo day.

## How the estimate works

- **Strata:** camera × conflict type (vehicle–pedestrian, vehicle–cyclist, vehicle–vehicle) × severity (PET bins, e.g.
  < 1 s, 1–2 s, 2–5 s).
- **Candidates:** N_h tier 0 candidates in stratum h. Hafnia checks n_h of them at random.
  Precision p̂_h = confirmed / n_h. Estimated near misses N̂ = Σ N_h·p̂_h.
  Variance Σ N_h²·p̂_h(1 − p̂_h)/n_h · (1 − n_h/N_h). Neyman allocation: n_h ∝ N_h·√(p_h(1 − p_h)).
- **Misses:** a small random sample of windows where tier 0 flagged nothing, so the estimate also covers near misses
  tier 0 missed. Their rate is probably low and its interval wide; report it as it is.
- **What the number means:** near misses *as Hafnia judges them*. Hafnia's agreement with reference labels is measured
  separately (E1) and reported next to every estimate.

## The lens: control what Hafnia sees

The gateway only accepts `xprotect://` clips, so Hafnia can only judge pixels XProtect recorded. The lens is one extra
XProtect camera whose video we render at run time:

```
source camera frames (FrameBridge, 10 fps) ─► lens renderer (T4) ─► ffmpeg ─► MediaMTX rtsp://127.0.0.1:8554/lens1
                                                                                          │
Hafnia ◄─ xprotect://…/lens_1?StartTime…EndTime (the span the clip played) ◄─ XProtect records lens_1 (Universal driver)
```

- **Transformations, most promising first:** crop and enlarge the candidate's region (Hafnia samples about 2 fps from
  clips like ours, and small road users lose pixels: our `test_01` miss); slow motion around the event (more sampled
  frames during the impact; the event-centred window result points the same way); boxes drawn on the involved road
  users (Set-of-Mark-style visual prompting); low-light enhancement or denoising for night and fog (least certain:
  Hafnia was trained on real CCTV including night, and restoration can add artefacts it never saw).
- **Cost:** a clip plays in real time, so a lens verdict comes about 10–16 s after the clip is rendered (estimate).
  That suits audits and second looks (tier 0 confident, plain check says NONE), not every real-time crash check.
- **How it is measured:** E6 below, the same windows with and without each transformation.
- **Setup:** MediaMTX (one exe, bound to 127.0.0.1, so no firewall change), the Universal 1-channel driver already
  installed on the Recording Server (no restart needed to add hardware), a setup script in `scripts/`.

## Components

| # | Component | Reuse | New work |
|---|---|---|---|
| 1 | Footage: long intersection video played as cameras | `scripts/add_test_camera.ps1`, `scripts/annexb_normalize.py` | Find, licence-check, convert. One Recording Server restart (ask first). StableFPS keeps all clips in RAM, 1.7 GB in total. |
| 2 | Conflict measures | `tier0/` (YOLO11m + ByteTrack, 22 frames/s on the T4) | Image-plane PET: the bottom centre of each box as the ground point, a grid of cells, two road users in one cell ≤ 1.5 s apart with headings ≥ 30° apart (so lane-following does not count). Severity higher with a sharp deceleration (`sharp_decel` exists). Optional: a homography from 4 clicked points per camera for metres and TTC. Thresholds to tune. |
| 3 | Candidate store | – | One JSONL row per candidate: camera, time, type, PET, tracks, boxes, stratum, audit state, Hafnia answer. |
| 4 | Auditor | `hafnia/gateway.py`, `incident/verify.ask` | Budget-aware random sampler per stratum. 6 s window centred on the conflict (event-centred windows measured best, `run/bench-20261018b`), sent plain or through the lens. |
| 5 | Estimator | – | Per-stratum estimates and intervals, recomputed hourly. |
| 6 | Dashboard (served from the machine) | the pipeline page in `scripts/viz_pipeline.py` | Conflict heatmap on the camera image, hourly counts with error bars, tier 0 raw count vs estimate, a list of checked near misses with frames and Hafnia's answer, budget gauge. |
| 7 | XProtect | `hafnia/xprotect_rest.py` (bookmarks, alarms) | A bookmark per confirmed near miss, findable in Smart Client Search. Crash alarms unchanged. |
| 8 | Crash layer | `incident/`, `scripts/run_live.py` | Prompt upgrade (below) and the router fix from `docs/PLAN.md`; daily cap shared with the auditor. |
| 9 | Lens camera | FrameBridge frames, `tier0/` boxes | MediaMTX setup, the lens publisher (renders and streams clips, logs each clip's UTC span), the `lens_1` camera, recording for it. |

### Prompts to test

AlertValidation style (wording to test in the pilot; the trained prompt text is not published):

> You are a CCTV traffic analyst. Validate an upstream alert. Upstream alert: near miss between a car and a pedestrian
> around the middle of this clip, confidence 0.62. A near miss means two road users come close to colliding and at
> least one has to brake hard, swerve or jump aside. Reply with exactly one word: NEAR_MISS if confirmed, COLLISION if
> they actually collide, NORMAL if the interaction is ordinary.

Variant: the same, but asking for JSON with `decision` (`confirm` | `discard`) and `reason`, as in training. Parse in
code either way. Gateway rules would match a keyword anywhere in the answer; audits do not need them.

Crash layer, also to test (about 30 requests, on the windows already located in `run/bench-20261018b`):
AlertValidation with tier 0's candidate type and score in place of today's one-word list (which still offers ROBBERY,
SHOOTING and others that are out of scope), and IncidentReport given the confirmed type in place of "Describe what
happens in this video." The second should stop the description contradicting the verdict
(`run/live-20261018T142327Z`).

## Footage

Near misses need long normal traffic with many interactions, not crashes, which makes footage easier to find.

| Source | What | Licence | Use |
|---|---|---|---|
| **Wikimedia Commons, "Street in Mumbai (video) 02" and "03"** (Nicolas Vigier, 2016) | Fixed cameras at busy Mumbai junctions. 02: elevated view, daylight, 3:03, 960×540; per frame (YOLO11m, 1 fps) about 16 people, 8 motorbikes, 19 cars, 1–2 buses, people crossing between moving vehicles. 03: street level, night, 3:31, about 15 people, 2.5 motorbikes, 3.6 cars | **CC0** | **G1 pick: the densest interactions found, cleanest licence.** Short: they loop every 3–3.5 min |
| **Wikimedia Commons, "Straßenverkehr in Düsseldorf"** (Slick, 2014) | Fixed camera at a tram junction (Worringer Platz), daylight, 4:35, 1280×720; about 6 people, 0.7 bicycles, 7.5 cars per frame, cars turning across tram tracks | **CC0** | **G1 pick** (European daylight scene) |
| MERL Street Scene (Zenodo 10870472) | One fixed oblique view of a two-lane street with bike lanes, 81 sequences, 202,545 frames at 15 fps (3.75 h), 1280×720 JPEG frames; quiet: mostly parked cars, about 1 person per frame | CC BY-SA 4.0 | Long normal footage for false candidates per hour; its anomaly labels (e.g. jaywalking) as a side set. Single sequences readable by range requests from the 49 GB zip |
| US DOT Intersection Safety Challenge, Stage 1B | Staged pedestrian and cyclist conflicts and non-conflicts at FHWA's test intersection, 8 CCTV cameras, 720p/1080p, runs of 1–2 min, **labelled**; validation set 41 runs (28.6 GB), sample 3.5 GB | Unverified: dataset pages say only "Rights: public" | Ground truth for G2 if the licence is confirmed |
| NGSIM Lankershim / Peachtree (US DOT) | 25–36 min per camera, 640×480, 10 fps | CC BY-SA 4.0 on data.transportation.gov (the original contractor metadata says CC BY 2.0) | **Rejected for near misses:** the cameras look almost straight down from 30–36 storeys; YOLO11m finds no road users (2026-10-21 sample), pedestrians are invisible |
| Sofia Macedonia square (Commons) | 7:21, 1080p | CC BY 3.0 (a second upload says CC BY-SA 3.0) | Rejected: edited from several shots, not one camera |
| YouTube CC BY long fixed cameras (Shibuya 40 min to 2 h, Woodford London 1.5 h, Toronto bike lane 50 min) | Long and continuous | CC BY on the watch page | Not downloadable within YouTube's terms; ask the uploader for the original file. The 2 h Shibuya uploads may be re-streams (licence doubtful) |
| Bellevue Traffic Video Dataset | 101 h, 5 intersections, 1280×720, 30 fps | "For research purposes", no licence named | Best footage; licence risk for a prize entry |
| Belt Parkway bridge webcam (YouTube) | 8–12 h archives, fixed | CC BY | Negatives (false candidates per hour) |
| AI City Challenge 2021, Track 4 | Iowa DOT highway cameras, 100 training videos of about 15 min (28–98 MB each), 800×410; 18 labelled anomalies in 17 videos (crashes *and* stalled vehicles, split not published); 15 GB zip on Google Drive, single files readable by HTTP range requests. Labels, ReadMe and licence files fetched to `data/aicity21/` (git-ignored). | **Not cleared.** The zip's `license.txt` says CC BY 4.0, but its Data License Agreement allows only challenge use, then "non-commercial, academic purposes only", no redistribution "in whole or in part", no unredacted faces or plates | **The only long footage with a real crash we found.** Reviewed by eye (2026-10-20, `data/aicity21/review.md`): 2 crashes happen on screen (video 91 at about 602 s, clear; video 95 at about 40 s, night, likely), 1 possible, 4 aftermath only, 10 stalled vehicles, 1 not found. Video 91 plays as camera `test_11` (port 116, since 2026-10-21) for internal tests only. Do not use in the entry until AI City (aicitychallenges@gmail.com) or the organizers clear it. |
| ACCIDENT (CVPRW 2026) | 2,027 real roadside and CCTV crash clips, 1–114 s (median 27 s), impact frame labelled | Annotations CC BY 4.0; clips kept only where source licences allow redistribution | Crash-layer recall on dozens of clips instead of 5 |
| dnepronet (YouTube), Kamianske | Fixed street webcam, 9:10 with a crash; many 1-min crash clips from the same cameras | CC BY (uploader's claim) | Closest openly licensed long crash clip |

Caveats: a YouTube CC licence is whatever the uploader claims, and downloading with tools such as yt-dlp breaks
YouTube's terms even when reuse is licensed. Non-commercial terms (AI City's agreement, TSBOW, TUM A9, Bellevue's research
clause) are a risk for a cash-prize entry: ask the organizers. The sources and licences of our current clips in `data/` are still TODO.

## Gates

| Gate | Test | Requests | Pass | If it fails |
|---|---|---|---|---|
| G0 Lens works | `lens_1` records a rendered clip of `test_11`'s crash; Hafnia answers on it | 2–3 | clip recorded at the logged span; a completed answer | **Passed 2026-10-21** (`run/lens-test_11-20261021T144445Z`): plain NONE twice, crop and crop in slow motion ACCIDENT twice each, on the same crash |
| G1 Footage | At least 20–30 min of intersection video with frequent vehicle–pedestrian or vehicle–cyclist interactions, licence we can cite | 0 | footage plays as a camera | **Partly passed 2026-10-21:** about 11 min of dense CC0 footage on 3 cameras (Mumbai 02, 03, Düsseldorf), no long continuous dense source; Street Scene (3.75 h, quiet) for false-candidate rates. Next: ask YouTube CC uploaders for originals, confirm the Intersection Safety Challenge licence |
| G2 Hafnia judges near misses | About 15 near-miss and 15 normal-interaction windows from G1, both prompt variants, plain and through the lens; reference labels by Opus from 2 fps frames | 40–60 | ≥ ~75% agreement with the reference (NYU's SeeUnsafe reached 76.7% on normal / near miss / collision) | Fall back to `docs/PLAN.md` with the improvements from this plan's crash layer and the lens |
| G3 Enough candidates | Tier 0 conflict candidates offline on G1 | 0 | ≥ ~20 candidates per camera-hour, so sampling is meaningful | Loosen thresholds or pick busier footage |

## Evaluation (validity)

- **E1 Hafnia vs reference.** About 60 candidates: Hafnia's label against Opus labels from 2 fps frames (the method of
  `run/bench-20261015`). Confusion matrix, agreement with a 95% interval.
- **E2 Does the estimate hold?** Label *every* candidate in one span with Hafnia (up to about 300 requests over two
  days) and take that as the population. Resample audits at 5, 10 and 20% (free, offline): bias, 95% interval
  coverage, interval width vs audit rate.
- **E3 Why audit at all.** Tier 0's raw count vs the audited estimate vs the full labels: how far raw detector counts
  are off.
- **E4 Cost.** Requests per camera-day for a target interval width; cameras one 500-a-day allowance covers.
- **E5 Crash layer.** Recall on ACCIDENT clips (40 clips ≈ 40–80 requests) and false candidates per camera-hour on
  long normal footage, each with a 95% interval. Today's 5 looped clips cannot separate tiered from polling.
- **E6 Lens.** The same candidate windows plain and through each lens transformation (crop, slow motion, marks,
  low-light), scored against the reference labels: agreement per variant with 95% intervals, split by day/night and
  by road-user size. About 20 windows × 3 variants ≈ 60 requests.

## Schedule (revised 2026-10-21)

The allowance resets at 00:00 UTC (the machine's clock). Each day stays under the scripts' `--stop-at` cap. Oct 20 went
to the footage search and the AI City review instead of G1, so everything moves one day and the dashboard shrinks.

| Day | Date | Work | Hafnia requests |
|---|---|---|---|
| 2 | Oct 21 | Plan revision. Lens camera: MediaMTX, publisher, `lens_1`, recording (G0 on `test_11`). | 3 |
| 3 | Oct 22 | G1: near-miss footage, licence check, convert. Conflict measures in `tier0/`, run offline (G3). | 0 |
| 4 | Oct 23 | Inject the footage (Recording Server restart: ask first). G2 pilot, plain and lens. **Decide: plan B or plan A.** | 60 |
| 5 | Oct 24 | Candidate store, auditor, estimator. E2 labelling, part 1. | 200 |
| 6 | Oct 25 | E2 labelling, part 2. Opus reference labels (E1). | 150 |
| 7 | Oct 26 | E2–E4 offline. E6 lens comparison. Crash-layer prompt A/B. | 90 |
| 8 | Oct 27 | Dashboard; bookmarks for confirmed near misses; shared budget pacing with the crash layer. | 30 |
| 9 | Oct 28 | Live run: both layers on several cameras for some hours. E5. | 300 |
| 10 | Oct 29 | Final report with charts. Best-effort `setup.ps1`, README, optional demo video. | 50 |
| 11 | Oct 30 | Spare; submission. | |

## Risks

| Risk | Fallback |
|---|---|
| Hafnia cannot tell a near miss from a normal interaction (G2) | Back to plan A, keeping the prompt and router improvements and the lens |
| No licensable intersection footage | Ask the organizers about Bellevue or NGSIM terms; worst case report on NGSIM only |
| Image-plane PET too noisy (perspective, occlusion) | Homography from 4 clicked points; higher thresholds; let Hafnia's audit absorb it (that is its job) |
| Too few confirmed near misses for tight intervals | Report wider intervals honestly; pool strata; more audit budget |
| Near misses look less dramatic than crashes in a demo | The crash layer stays in the demo, on the same cameras and dashboard |
| Lens stream drops, or `lens_1` records nothing (record-on-motion) | Keep the stream running with idle frames; our own recording rule for `lens_1`; plain clips still work |
| Lens transformations do not help, or hurt (E6) | Report it as measured; keep only what helps |

## What carries over from plan A

Everything built so far: tier 0 (detection, tracking, rules), FrameBridge, the gateway and XProtect clients, the
router, clip injection, the evaluation and report scripts, and every measured finding in `CLAUDE.md`. Dropped: the
"learned trust" claim measured on looped clips, which a loop makes trivially learnable.

## Sources

- Milestone, Hafnia training and output formats: https://www.milestonesys.com/resources/content/articles/smart-city-video-intelligence/
- Milestone, AI Search and alert verification: https://www.milestonesys.com/company/news/press-releases/ai-built-for-security-operations/
- NVIDIA VSS alert verification: https://docs.nvidia.com/vss/3.2.0/alert-verification-service.html
- FHWA SSAM thresholds and conflict definition: https://www.fhwa.dot.gov/publications/research/safety/08051/03a.cfm,
  https://www.fhwa.dot.gov/publications/research/safety/08051/06.cfm
- Kansas DOT study on near-miss tool accuracy: https://rosap.ntl.bts.gov/view/dot/72548/dot_72548_DS1.pdf
- Bellevue: https://bellevuewa.gov/sites/default/files/media/pdf_document/2020/TRB-Accepted-Paper-2021-Video-Surrogate-Safety-Analysis-Bellevue.pdf
- Ann Arbor: https://engage.a2gov.org/safe-streets-all-project
- Fremont: https://www.roadsbridges.com/city-fremont-calif-deploy-intersection-analytics-systems-along-smart-corridor
- SeeUnsafe: https://arxiv.org/abs/2501.10604
- Set-of-Mark visual prompting: https://arxiv.org/abs/2310.11441
- Universal driver settings: https://doc.milestonesys.com/xprotect/universal-drivers/v1.67/en/supported-features
- AI City Challenge dataset access: https://www.aicitychallenge.org/ai-city-challenge-dataset-access/
- ACCIDENT dataset: https://www.kaggle.com/datasets/picekl/accident, https://accidentbench.github.io
- dnepronet crash video: https://www.youtube.com/watch?v=BH9nEpAjrp4
