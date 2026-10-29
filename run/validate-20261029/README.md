# The AlertValidation shape as a second question: the service's answer put to Hafnia to confirm or discard (2026-10-29)

`scripts/second_question.py`, 06:45-06:55 UTC, 49 requests, 49 completed (today's count 39 before, 88 after). Hafnia
VLM was fine-tuned on an alert-validation task (an upstream alert in, confirm or discard out; Milestone's article;
the trained wording is not published). Asked as a first question with a generic alert (`run/prompt-20261028T1605Z`,
cell D) the shape confirmed nothing false and discarded 10 of 18 incidents: a strict verifier. The candidate use
named before the hold-out was run: a second question before a High-priority alarm, the open question first and,
when its answer names an incident, that category put to the model as the upstream alert on the same span. Both
sides measured here, one shot, the prompt pre-registered (cell D's text with the alert line naming the first
answer's category, `prompt.json`; nothing else differs; the gateway's system prompt empty):

- **31 false cards of the hold-out** (`run/holdout-20261029`: the answers that named an incident on real streets
  where there was none; a discard is right), and
- **18 true incidents of the prompt experiment** (cell A's answers that named the incident the clip shows, on the
  looped scenes; a confirm is right).

## Findings

1. **The second question removes 19 of the 31 false cards and keeps 15 of the 18 true incidents.** As the gate
   before a High-priority alarm: of the 25 High false cards it stops 16 and lets 9 through; of the 5 High true
   incidents it passes 3 and holds 2. Confidence was 0.95 on all 49 answers, right or wrong; "evidence_frames" was
   "middle" 42 times. Valid JSON 49 of 49.
2. **Invented events do not survive a yes-or-no question: 5 of 5 COLLISIONs discarded** ("a steady flow of
   vehicles and pedestrians with no visible collision"). The first question's fluent stories of sparks and thrown
   riders were not defended when the model was asked whether they happened.
3. **Waiting cars survive it when the clip is a crop: 9 of 20 STALLED_VEHICLE confirmed, all but one of them lens
   crops of one stopped car** ("stopped in the middle of the lane with brake lights illuminated", the Düsseldorf
   estate car at the crossing among them, the one real-camera-setting card that reached the question). By view: the
   whole-frame clips were discarded 11 of 13 ("a clear intersection with vehicles moving through"; "a dark sedan
   stopped at a red light"), the lens crops 8 of 18. The hold-out's finding 4 again: the model judges the scene, and
   a crop of a waiting car has no scene. OBSTRUCTION 3 of 6 discarded (a parked SUV and a blue cover on a cart
   confirmed as blocking the way).
4. **What it holds back is the worst thing to hold: 2 of the 3 person-on-the-tracks clips** ("walking along the
   platform edge and stepping onto the tracks", then discard; "sitting on the platform edge near the yellow tactile
   paving"). Yesterday's cell D confirmed all three with a generic alert. With the category named, the verifier
   confirmed far more elsewhere (TAMPERING 5 of 5 against 2 of 5, OBSTRUCTION 5 of 6 against 1 of 6, DAMAGE 2 of 2
   against 0 of 2) and less here; with three clips, form and run-to-run variation cannot be told apart, and either
   way the category cannot be gated on it. The third discard is the hard e-scooter crop (the handlebar only), which
   cell D discarded too.
5. **Reasons are not evidence.** The Mumbai pavement corner was rightly discarded with "a stationary train at a
   platform with people standing on it": there is no train in Mumbai 02; the words are the NONE definition's.

## What this means for Clearway

- **Not a hard gate on High alarms.** It would stop two of every three false High cards on real streets, but on
  the loops it would hold two of three people on the tracks, the category the whole entry exists for. Nothing
  about the result argues for building it as the thing that decides whether an alarm goes out.
- **Usable as a signal, not a verdict:** a discard could lower a card's priority (High to Medium) and say why on the
  card, keeping the alarm and the card; a confirm leaves it. That costs one more request per incident card (about
  one per camera-hour on the loops) and loses nothing an operator would miss. Not built; the design would need its
  own check.
- **The whole frame is the better second look.** The split by view says the second question works where the first
  one does: when the junction is in view. For a STALLED_VEHICLE answer on a crop, the natural second question is
  on the whole frame with the spot marked, which the hold-out already named as candidate fix (4). It has to be
  measured on footage neither run used: the hold-out set is a tuning set, and this result was read from it.
- **The invented-collision habit has a cheap remedy** if COLLISION alarms ever matter on real streets: ask again.

Files: `plan.jsonl` (the 49 questions: source, span, first answer, truth, priority), `prompt.json` (the template
and an example), `results.jsonl` (every answer with timing), `answers.md` (the answers by question with the first
answer's summary), `summary.json`, `ask.log`.

<!-- tables: written by second_question.py score; the text above is kept -->

49 second questions asked (49 answered, 0 failed) with the alert prompt (`prompt.json`) on the spans the first answers were about; the gateway's system prompt empty.

## The verdicts

| Set | Asked | Answered | Right | Confirmed | Discarded | Other | Category kept on confirm | Valid JSON |
|---|---|---|---|---|---|---|---|---|
| hold-out false cards (a discard is right) | 31 | 31 | 19 | 12 | 19 | 0 | 12 | 31 |
| ... of which High priority (the alarm gate) | 25 | 25 | 16 | 9 | 16 | 0 | 9 | 25 |
| true incidents (a confirm is right) | 18 | 18 | 15 | 15 | 3 | 0 | 15 | 18 |
| ... of which High priority | 5 | 5 | 3 | 3 | 2 | 0 | 3 | 5 |
| all | 49 | 49 | 34 | 27 | 22 | 0 | 27 | 49 |

## By the first answer's category

| Set | Asked | Answered | Right | Confirmed | Discarded | Other | Category kept on confirm | Valid JSON |
|---|---|---|---|---|---|---|---|---|
| holdout / COLLISION (High) | 5 | 5 | 5 | 0 | 5 | 0 | 0 | 5 |
| holdout / OBSTRUCTION (Medium) | 6 | 6 | 3 | 3 | 3 | 0 | 3 | 6 |
| holdout / STALLED_VEHICLE (High) | 20 | 20 | 11 | 9 | 11 | 0 | 9 | 20 |
| prompt / DAMAGE (Low) | 2 | 2 | 2 | 2 | 0 | 0 | 2 | 2 |
| prompt / OBSTRUCTION (Medium) | 6 | 6 | 5 | 5 | 1 | 0 | 5 | 6 |
| prompt / PERSON_ON_TRACKS (High) | 3 | 3 | 1 | 1 | 2 | 0 | 1 | 3 |
| prompt / STALLED_VEHICLE (High) | 2 | 2 | 2 | 2 | 0 | 0 | 2 | 2 |
| prompt / TAMPERING (Low) | 5 | 5 | 5 | 5 | 0 | 0 | 5 | 5 |

## The hold-out false cards by view

| Set | Asked | Answered | Right | Confirmed | Discarded | Other | Category kept on confirm | Valid JSON |
|---|---|---|---|---|---|---|---|---|
| direct | 13 | 13 | 11 | 2 | 11 | 0 | 2 | 13 |
| lens | 18 | 18 | 8 | 10 | 8 | 0 | 10 | 18 |

Confidence: {'n': 49, 'min': 0.95, 'max': 0.95, 'mean': 0.95}. Evidence frames: {'start, middle, end': 6, 'middle': 42, 'start, middle, end of the clip': 1}.

## Every second question

| # | Source | Clip | First answer | Truth | Want | Decision | Category | Reason |
|---|---|---|---|---|---|---|---|---|
| 1 | holdout | mumbai02-real-002 | OBSTRUCTION | NONE | discard | discard | NONE | The clip shows a stationary train at a platform with people standing on the platform and vehicles parked along the curb; no obstruction, damage, collision, or tampering is visible. |
| 2 | holdout | duesseldorf-real-001 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A dark station wagon is stopped in the middle of the lane with brake lights illuminated, surrounded by other vehicles and pedestrians crossing nearby, indicating a breakdown or stall rather than a parked or queued vehicl |
| 3 | holdout | mumbai02-loops-001 | COLLISION | NONE | discard | discard | NONE | The clip shows a black-and-yellow taxi turning left at an intersection and a white sedan following behind, with no visible collision, damage, obstruction, or right-of-way violation; traffic flows smoothly without impact  |
| 4 | holdout | mumbai02-loops-002 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A black-and-yellow taxi is stopped in the middle of the roadway, blocking the lane and causing surrounding vehicles to slow and queue; the vehicle remains stationary throughout the clip with no visible movement or exit. |
| 5 | holdout | mumbai02-loops-006 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A yellow-and-black taxi is stationary in the middle of the lane with its brake lights illuminated, surrounded by motorcycles and other vehicles that are stopped or slowing to avoid it, indicating a breakdown or stall blo |
| 6 | holdout | mumbai02-loops-008 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A white sedan is stopped in the middle of the intersection, blocking the lane and causing surrounding vehicles and pedestrians to stop and reroute around it. |
| 7 | holdout | mumbai02-loops-010 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a clear intersection with vehicles moving through the junction and pedestrians crossing at marked crossings; no vehicle is stopped or broken down in a traffic lane, no collision or obstruction is visible,  |
| 8 | holdout | mumbai02-loops-012 | OBSTRUCTION | NONE | discard | confirm **wrong** | OBSTRUCTION | A white SUV is parked across the roadway, blocking the lane and forcing passing vehicles to slow and maneuver around it, which clearly obstructs the right-of-way. |
| 9 | holdout | mumbai02-loops-014 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a clear intersection with vehicles moving through the junction and pedestrians crossing at the zebra crossing; no vehicle is stalled in a traffic lane, no collision or obstruction is visible, and traffic f |
| 10 | holdout | mumbai02-loops-018 | OBSTRUCTION | NONE | discard | confirm **wrong** | OBSTRUCTION | A blue object lies across the pavement near the staircase, visibly blocking the path and preventing normal passage. |
| 11 | holdout | mumbai02-loops-020 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a clear intersection with vehicles moving through the junction and pedestrians crossing at marked crossings; no vehicle is stopped or broken down in a traffic lane, no collision or obstruction is visible,  |
| 12 | holdout | mumbai02-loops-022 | OBSTRUCTION | NONE | discard | confirm **wrong** | OBSTRUCTION | A white sedan is stopped across the roadway, blocking the lane and forcing vehicles and pedestrians to detour around it, which clearly obstructs the right-of-way. |
| 13 | holdout | mumbai02-loops-024 | COLLISION | NONE | discard | discard | NONE | The clip shows a steady flow of vehicles and pedestrians with no visible collision, damage, obstruction, or stalled vehicle; traffic moves smoothly without abrupt stops or impacts. |
| 14 | holdout | mumbai02-loops-025 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a yellow taxi parked at the kerb with motorcycles and other vehicles moving around it, but no vehicle is stopped or broken down in a traffic lane; traffic flows normally without obstruction. |
| 15 | holdout | mumbai02-loops-027 | COLLISION | NONE | discard | discard | NONE | The clip shows a clear intersection with vehicles moving smoothly through the junction, no collisions, obstructions, or damage visible, and no person on tracks. |
| 16 | holdout | mumbai02-loops-029 | COLLISION | NONE | discard | discard | NONE | The clip shows a busy intersection with vehicles and motorcycles moving through the junction, no collision, damage, obstruction, or stalled vehicle is visible, and traffic flows smoothly without any right-of-way incident |
| 17 | holdout | mumbai02-loops-031 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A white sedan is stopped in the middle of the lane, blocking traffic flow and causing vehicles behind to slow and queue; the car remains stationary throughout the clip with no visible movement or damage. |
| 18 | holdout | mumbai02-loops-033 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a busy intersection with vehicles moving through the junction and parked cars along the kerbs; no vehicle is stopped or broken down in a traffic lane, and no obstruction, collision, or damage is visible. |
| 19 | holdout | mumbai02-loops-035 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A white sedan is stopped in the middle of the intersection, blocking the lane and causing surrounding vehicles to slow and queue, consistent with a stalled vehicle. |
| 20 | holdout | mumbai02-loops-037 | COLLISION | NONE | discard | discard | NONE | The clip shows a red vehicle parked at the kerb with a motorcycle passing behind it and other vehicles moving normally; no collision, damage, obstruction, or right-of-way violation is visible. |
| 21 | holdout | duesseldorf-loops-001 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A dark station wagon is stopped in the middle of the traffic lane with brake lights illuminated, surrounded by other vehicles and pedestrians, indicating a breakdown or stall rather than a parked or queued vehicle. |
| 22 | holdout | duesseldorf-loops-003 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a blue sedan smoothly entering the intersection and turning left without stopping, with no stalled vehicle, collision, obstruction, damage, or tampering visible. |
| 23 | holdout | duesseldorf-loops-005 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a dark sedan stopped at a red light with other vehicles moving around it, indicating normal traffic flow rather than a stalled vehicle or incident. |
| 24 | holdout | duesseldorf-loops-007 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a blue sedan completing a right turn and merging into the lane, with no vehicle stopped or broken down in the traffic lane; traffic flows smoothly and no obstruction or damage is visible. |
| 25 | holdout | duesseldorf-loops-010 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A dark station wagon is stopped in the middle of the lane with brake lights illuminated, blocking the lane and causing nearby vehicles to slow and queue; pedestrians are visible on the sidewalk, consistent with a vehicle |
| 26 | holdout | duesseldorf-loops-012 | STALLED_VEHICLE | NONE | discard | confirm **wrong** | STALLED_VEHICLE | A dark sedan is stopped in the middle of the intersection, blocking the lane and causing other vehicles to queue behind it; the vehicle remains stationary throughout the clip with no visible movement or clearance. |
| 27 | holdout | duesseldorf-loops-014 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a blue sedan completing a right turn and merging into the lane, with no vehicle stopped or broken down in the traffic lane; traffic flows smoothly and no obstruction or damage is visible. |
| 28 | holdout | duesseldorf-loops-016 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a red car moving smoothly through the intersection with no vehicle stopped in a lane, no collision, no obstruction, no damage, no tampering, and no person on tracks. |
| 29 | holdout | duesseldorf-loops-020 | OBSTRUCTION | NONE | discard | discard | NONE | The clip shows pedestrians crossing a marked zebra crossing with vehicles stopped at the curb, no obstruction lying across the pavement, no damage or tampering, and no person on the tracks. |
| 30 | holdout | duesseldorf-loops-022 | STALLED_VEHICLE | NONE | discard | discard | NONE | The clip shows a red convertible parked at the curb with no visible obstruction, damage, or stalled vehicle; pedestrians cross the zebra crossing and traffic flows normally, indicating ordinary traffic conditions. |
| 31 | holdout | duesseldorf-loops-028 | OBSTRUCTION | NONE | discard | discard | NONE | The clip shows a clear, dry road surface with no obstruction, damage, or stalled vehicles; vehicles move smoothly and pedestrians cross without incident. |
| 32 | prompt | 20261026T141630839929_cw-0001-person_on_railway_tracks.avi | PERSON_ON_TRACKS | PERSON_ON_TRACKS | confirm | discard **wrong** | NONE | The clip shows a person in a red jacket sitting on the platform edge near the yellow tactile strip, with clear daylight and no person on the tracks; the alert's 'PERSON_ON_TRACKS' label is incorrect. |
| 33 | prompt | 20261026T141635268961_cw-0002-escooter_left_across_sidewalk.avi | OBSTRUCTION | OBSTRUCTION | confirm | confirm | OBSTRUCTION | A white electric scooter lies on its side across the pavement, blocking the walkway and preventing normal passage; the rider dismounts and walks away, leaving the scooter as a stationary obstruction. |
| 34 | prompt | 20261026T141645171209_cw-0008-vehicle_breakdown_traffic_queue.avi | STALLED_VEHICLE | STALLED_VEHICLE | confirm | confirm | STALLED_VEHICLE | A silver pickup truck is stopped in the middle of the lane with its driver-side door open and a person standing beside it, emitting visible exhaust smoke, while a car behind it is braking and another vehicle is queued fu |
| 35 | prompt | 20261026T141652792754_cw-0014-graffiti_on_standing_train.avi | DAMAGE | DAMAGE | confirm | confirm | DAMAGE | The clip shows a person on the platform actively painting bright graffiti on the side of a stationary train car, which constitutes property damage. |
| 36 | prompt | 20261026T141653717085_cw-0015-school_gate_break_in_night.avi | TAMPERING | TAMPERING | confirm | confirm | TAMPERING | A person in a hooded jacket is seen at night using a tool to force or pick a lock on a green metal gate, then exits the frame, leaving the gate secured with a padlock and chain. |
| 37 | prompt | 20261026T141706898983_cw-0019-bin_pushed_over_onto_sidewalk.avi | OBSTRUCTION | OBSTRUCTION | confirm | confirm | OBSTRUCTION | A large green wheeled bin is knocked over and lies on its side across the pavement, blocking the pedestrian path and preventing normal passage. |
| 38 | prompt | 20261026T141736188745_cw-0021-bin_pushed_over_onto_sidewalk.avi | OBSTRUCTION | OBSTRUCTION | confirm | confirm | OBSTRUCTION | A large green bin is positioned across the tiled pavement, blocking the pedestrian path and preventing normal passage. |
| 39 | prompt | 20261026T150515433995_cw-0031-school_gate_break_in_night.avi | TAMPERING | TAMPERING | confirm | confirm | TAMPERING | A person crouches at a metal fence and uses a tool to force or pick a lock, which constitutes tampering with a gate or door. |
| 40 | prompt | 20261027T124152361867_cw-0001-bin_pushed_over_onto_sidewalk.avi | OBSTRUCTION | OBSTRUCTION | confirm | confirm | OBSTRUCTION | A large green wheeled bin lies on its side across the pavement, blocking the walkway and forcing the pedestrian to step around it; the obstruction is clearly visible and stationary. |
| 41 | prompt | 20261027T124201017167_cw-0003-vehicle_breakdown_traffic_queue.avi | STALLED_VEHICLE | STALLED_VEHICLE | confirm | confirm | STALLED_VEHICLE | A silver pickup truck is stopped in the middle of the lane with its driver-side door open and a person exiting, emitting visible smoke from the engine area, indicating a breakdown rather than a parked or queued vehicle. |
| 42 | prompt | 20261027T124204585257_cw-0004-person_on_railway_tracks.avi | PERSON_ON_TRACKS | PERSON_ON_TRACKS | confirm | confirm | PERSON_ON_TRACKS | A person in a red jacket is clearly visible walking across the railway tracks between the platforms, crossing the rails and ballast in the middle of the clip. |
| 43 | prompt | 20261027T124205701116_cw-0005-school_gate_break_in_night.avi | TAMPERING | TAMPERING | confirm | confirm | TAMPERING | A person in dark clothing is crouched beside a metal fence at night, using a tool to force or pick a lock or gate, which constitutes tampering. |
| 44 | prompt | 20261027T124206301555_cw-0006-escooter_left_across_sidewalk.avi | OBSTRUCTION | OBSTRUCTION | confirm | discard **wrong** | NONE | The clip shows a person walking on the pavement and parked cars along the curb with clear lane markings and no obstruction, damage, collision, or stalled vehicle visible. |
| 45 | prompt | 20261027T124207866831_cw-0008-graffiti_on_standing_train.avi | DAMAGE | DAMAGE | confirm | confirm | DAMAGE | The train car displays vivid graffiti on its side, indicating property damage or defacement, which matches the DAMAGE category. |
| 46 | prompt | 20261027T124211337185_cw-0010-school_gate_break_in_night.avi | TAMPERING | TAMPERING | confirm | confirm | TAMPERING | A person crouches beside a metal fence, uses a tool to cut or force the chain and padlock, then stands up and walks away, indicating deliberate tampering with a secured gate. |
| 47 | prompt | 20261027T124212362072_cw-0011-person_on_railway_tracks.avi | PERSON_ON_TRACKS | PERSON_ON_TRACKS | confirm | discard **wrong** | NONE | The clip shows a person walking along the platform edge and stepping onto the tracks, then falling onto the platform; no vehicle collision, obstruction, damage, or tampering is visible. |
| 48 | prompt | 20261027T124213501036_cw-0012-escooter_left_across_sidewalk.avi | OBSTRUCTION | OBSTRUCTION | confirm | confirm | OBSTRUCTION | A white electric scooter lies across the pavement, blocking the walkway and forcing a pedestrian to step around it; the scooter remains stationary and does not move during the clip. |
| 49 | prompt | 20261027T124225065659_cw-0013-school_gate_break_in_night.avi | TAMPERING | TAMPERING | confirm | confirm | TAMPERING | A person in dark clothing crouches at the gate, uses a tool to cut the padlock and chain, and removes the lock, clearly forcing the gate open. |
