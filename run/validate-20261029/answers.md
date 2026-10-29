# The second question's answers

## 1. holdout mumbai02-real-002 — first answer OBSTRUCTION, truth NONE, want discard

First answer's summary: A large tree trunk falls across the roadway, blocking the lane and forcing vehicles to stop or maneuver around it.

Decision: **discard** (NONE; Completed, 13.5 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a stationary train at a platform with people standing on the platform and vehicles parked along the curb; no obstruction, damage, collision, or tampering is visible.",
  "evidence_frames": "start, middle, end",
  "object": "stationary train at platform",
  "still_present": true
}
```
```

## 2. holdout duesseldorf-real-001 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A dark station wagon is stopped in the lane with brake lights illuminated, blocking traffic; vehicles behind slow and stop, and pedestrians cross the road around it.

Decision: **confirm** (STALLED_VEHICLE; Completed, 13.5 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A dark station wagon is stopped in the middle of the lane with brake lights illuminated, surrounded by other vehicles and pedestrians crossing nearby, indicating a breakdown or stall rather than a parked or queued vehicle.",
  "evidence_frames": "middle",
  "object": "dark station wagon",
  "still_present": true
}
```
```

## 3. holdout mumbai02-loops-001 — first answer COLLISION, truth NONE, want discard

First answer's summary: A white sedan collides with a parked vehicle at the curb, then stalls in the lane and blocks traffic.

Decision: **discard** (NONE; Completed, 13.4 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a black-and-yellow taxi turning left at an intersection and a white sedan following behind, with no visible collision, damage, obstruction, or right-of-way violation; traffic flows smoothly without impact or disruption.",
  "evidence_frames": "middle",
  "object": "black-and-yellow taxi",
  "still_present": false
}
```
```

## 4. holdout mumbai02-loops-002 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white sedan stalls in the middle of the lane, blocking traffic and forcing vehicles to merge around it.

Decision: **confirm** (STALLED_VEHICLE; Completed, 10.3 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A black-and-yellow taxi is stopped in the middle of the roadway, blocking the lane and causing surrounding vehicles to slow and queue; the vehicle remains stationary throughout the clip with no visible movement or exit.",
  "evidence_frames": "middle",
  "object": "black-and-yellow taxi",
  "still_present": true
}
```
```

## 5. holdout mumbai02-loops-006 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A yellow taxi is stopped in the middle of the lane, blocking traffic, while motorcycles and other vehicles maneuver around it.

Decision: **confirm** (STALLED_VEHICLE; Completed, 10.2 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A yellow-and-black taxi is stationary in the middle of the lane with its brake lights illuminated, surrounded by motorcycles and other vehicles that are stopped or slowing to avoid it, indicating a breakdown or stall blocking the traffic lane.",
  "evidence_frames": "middle",
  "object": "yellow-and-black taxi",
  "still_present": true
}
```
```

## 6. holdout mumbai02-loops-008 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white sedan stalls in the middle of the lane, blocking traffic and forcing vehicles to maneuver around it.

Decision: **confirm** (STALLED_VEHICLE; Completed, 10.2 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A white sedan is stopped in the middle of the intersection, blocking the lane and causing surrounding vehicles and pedestrians to stop and reroute around it.",
  "evidence_frames": "middle",
  "object": "white sedan",
  "still_present": true
}
```
```

## 7. holdout mumbai02-loops-010 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it.

Decision: **discard** (NONE; Completed, 9.8 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a clear intersection with vehicles moving through the junction and pedestrians crossing at marked crossings; no vehicle is stopped or broken down in a traffic lane, no collision or obstruction is visible, and traffic flows normally.",
  "evidence_frames": "middle",
  "object": "intersection with moving vehicles and crossing pedestrians",
  "still_present": false
}
```
```

## 8. holdout mumbai02-loops-012 — first answer OBSTRUCTION, truth NONE, want discard

First answer's summary: A white SUV is parked on the pavement, blocking the lane and forcing passing vehicles to slow and maneuver around it.

Decision: **confirm** (OBSTRUCTION; Completed, 9.7 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A white SUV is parked across the roadway, blocking the lane and forcing passing vehicles to slow and maneuver around it, which clearly obstructs the right-of-way.",
  "evidence_frames": "middle",
  "object": "white SUV parked across lane",
  "still_present": true
}
```
```

## 9. holdout mumbai02-loops-014 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it.

Decision: **discard** (NONE; Completed, 9.6 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a clear intersection with vehicles moving through the junction and pedestrians crossing at the zebra crossing; no vehicle is stalled in a traffic lane, no collision or obstruction is visible, and traffic flows normally.",
  "evidence_frames": "middle",
  "object": "intersection with moving vehicles and crossing pedestrians",
  "still_present": false
}
```
```

## 10. holdout mumbai02-loops-018 — first answer OBSTRUCTION, truth NONE, want discard

First answer's summary: A blue tarpaulin lies across the pavement, partially blocking the pedestrian path and remaining in place throughout the video.

Decision: **confirm** (OBSTRUCTION; Completed, 9.4 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A blue object lies across the pavement near the staircase, visibly blocking the path and preventing normal passage.",
  "evidence_frames": "middle",
  "object": "blue object on pavement",
  "still_present": true
}
```
```

## 11. holdout mumbai02-loops-020 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it.

Decision: **discard** (NONE; Completed, 9.4 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a clear intersection with vehicles moving through the junction and pedestrians crossing at marked crossings; no vehicle is stopped or broken down in a traffic lane, no collision or obstruction is visible, and traffic flows normally.",
  "evidence_frames": "middle",
  "object": "intersection with moving vehicles and crossing pedestrians",
  "still_present": false
}
```
```

## 12. holdout mumbai02-loops-022 — first answer OBSTRUCTION, truth NONE, want discard

First answer's summary: A white sedan is stopped in the middle of the lane, blocking traffic and forcing vehicles and pedestrians to detour around it.

Decision: **confirm** (OBSTRUCTION; Completed, 9.3 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A white sedan is stopped across the roadway, blocking the lane and forcing vehicles and pedestrians to detour around it, which clearly obstructs the right-of-way.",
  "evidence_frames": "middle",
  "object": "white sedan stopped across roadway",
  "still_present": true
}
```
```

## 13. holdout mumbai02-loops-024 — first answer COLLISION, truth NONE, want discard

First answer's summary: A white sedan collides with a black SUV at the intersection, then stalls in the lane and remains there as traffic around it slows and stops.

Decision: **discard** (NONE; Completed, 10.3 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a steady flow of vehicles and pedestrians with no visible collision, damage, obstruction, or stalled vehicle; traffic moves smoothly without abrupt stops or impacts.",
  "evidence_frames": "middle",
  "object": "vehicles and pedestrians",
  "still_present": false
}
```
```

## 14. holdout mumbai02-loops-025 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A yellow taxi is stopped in the middle of the lane, blocking traffic, while other vehicles and motorcycles maneuver around it.

Decision: **discard** (NONE; Completed, 10.2 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a yellow taxi parked at the kerb with motorcycles and other vehicles moving around it, but no vehicle is stopped or broken down in a traffic lane; traffic flows normally without obstruction.",
  "evidence_frames": "middle",
  "object": "yellow taxi parked at kerb",
  "still_present": false
}
```
```

## 15. holdout mumbai02-loops-027 — first answer COLLISION, truth NONE, want discard

First answer's summary: A white sedan collides with a black hatchback in the middle of the intersection, then stalls and blocks the lane.

Decision: **discard** (NONE; Completed, 10.1 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a clear intersection with vehicles moving smoothly through the junction, no collisions, obstructions, or damage visible, and no person on tracks.",
  "evidence_frames": "middle",
  "object": "intersection traffic",
  "still_present": false
}
```
```

## 16. holdout mumbai02-loops-029 — first answer COLLISION, truth NONE, want discard

First answer's summary: A white hatchback enters the intersection and collides with a black sedan, causing the hatchback to spin and stall in the lane.

Decision: **discard** (NONE; Completed, 11.1 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a busy intersection with vehicles and motorcycles moving through the junction, no collision, damage, obstruction, or stalled vehicle is visible, and traffic flows smoothly without any right-of-way incident.",
  "evidence_frames": "middle",
  "object": "vehicles and motorcycles",
  "still_present": false
}
```
```

## 17. holdout mumbai02-loops-031 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white sedan is stopped in the middle of the lane, blocking traffic and causing vehicles behind to slow and stop.

Decision: **confirm** (STALLED_VEHICLE; Completed, 11.0 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A white sedan is stopped in the middle of the lane, blocking traffic flow and causing vehicles behind to slow and queue; the car remains stationary throughout the clip with no visible movement or damage.",
  "evidence_frames": "middle",
  "object": "white sedan",
  "still_present": true
}
```
```

## 18. holdout mumbai02-loops-033 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white hatchback stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it.

Decision: **discard** (NONE; Completed, 10.8 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a busy intersection with vehicles moving through the junction and parked cars along the kerbs; no vehicle is stopped or broken down in a traffic lane, and no obstruction, collision, or damage is visible.",
  "evidence_frames": "middle",
  "object": "intersection traffic",
  "still_present": false
}
```
```

## 19. holdout mumbai02-loops-035 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white sedan is stopped in the middle of the intersection, blocking the lane and forcing surrounding vehicles and motorcycles to maneuver around it.

Decision: **confirm** (STALLED_VEHICLE; Completed, 11.2 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A white sedan is stopped in the middle of the intersection, blocking the lane and causing surrounding vehicles to slow and queue, consistent with a stalled vehicle.",
  "evidence_frames": "middle",
  "object": "white sedan",
  "still_present": true
}
```
```

## 20. holdout mumbai02-loops-037 — first answer COLLISION, truth NONE, want discard

First answer's summary: A motorcycle collides with a parked vehicle in the lane, producing visible sparks and smoke, and the rider is thrown from the bike.

Decision: **discard** (NONE; Completed, 11.1 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a red vehicle parked at the kerb with a motorcycle passing behind it and other vehicles moving normally; no collision, damage, obstruction, or right-of-way violation is visible.",
  "evidence_frames": "start, middle, end",
  "object": "parked red vehicle",
  "still_present": false
}
```
```

## 21. holdout duesseldorf-loops-001 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A dark blue station wagon is stopped in the lane with brake lights illuminated, blocking traffic; a blue sedan pulls up behind it and stops, while pedestrians wait on the pavement.

Decision: **confirm** (STALLED_VEHICLE; Completed, 10.9 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A dark station wagon is stopped in the middle of the traffic lane with brake lights illuminated, surrounded by other vehicles and pedestrians, indicating a breakdown or stall rather than a parked or queued vehicle.",
  "evidence_frames": "middle",
  "object": "dark station wagon",
  "still_present": true
}
```
```

## 22. holdout duesseldorf-loops-003 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A blue sedan is stopped in the middle of the intersection, blocking the lane and causing other vehicles to queue behind it.

Decision: **discard** (NONE; Completed, 10.2 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a blue sedan smoothly entering the intersection and turning left without stopping, with no stalled vehicle, collision, obstruction, damage, or tampering visible.",
  "evidence_frames": "start, middle, end",
  "object": "blue sedan",
  "still_present": false
}
```
```

## 23. holdout duesseldorf-loops-005 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A white sedan is stopped in the middle of the lane, blocking traffic, while other vehicles slow and maneuver around it.

Decision: **discard** (NONE; Completed, 10.2 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a dark sedan stopped at a red light with other vehicles moving around it, indicating normal traffic flow rather than a stalled vehicle or incident.",
  "evidence_frames": "start, middle, end",
  "object": "dark sedan at red light",
  "still_present": false
}
```
```

## 24. holdout duesseldorf-loops-007 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A blue sedan stalls in the middle of the intersection, blocking the lane and forcing other vehicles to stop and wait.

Decision: **discard** (NONE; Completed, 10.1 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a blue sedan completing a right turn and merging into the lane, with no vehicle stopped or broken down in the traffic lane; traffic flows smoothly and no obstruction or damage is visible.",
  "evidence_frames": "start, middle, end",
  "object": "blue sedan",
  "still_present": false
}
```
```

## 25. holdout duesseldorf-loops-010 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A dark blue sedan is stopped in the lane with brake lights illuminated, blocking traffic; pedestrians wait on the pavement as the vehicle remains stationary.

Decision: **confirm** (STALLED_VEHICLE; Completed, 9.1 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A dark station wagon is stopped in the middle of the lane with brake lights illuminated, blocking the lane and causing nearby vehicles to slow and queue; pedestrians are visible on the sidewalk, consistent with a vehicle stalled in traffic.",
  "evidence_frames": "middle",
  "object": "station wagon",
  "still_present": true
}
```
```

## 26. holdout duesseldorf-loops-012 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A blue sedan stalls in the middle of the lane, blocking traffic and forcing other vehicles to stop and wait.

Decision: **confirm** (STALLED_VEHICLE; Completed, 9.1 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A dark sedan is stopped in the middle of the intersection, blocking the lane and causing other vehicles to queue behind it; the vehicle remains stationary throughout the clip with no visible movement or clearance.",
  "evidence_frames": "middle",
  "object": "dark sedan stopped in lane",
  "still_present": true
}
```
```

## 27. holdout duesseldorf-loops-014 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A blue sedan stalls in the middle of the lane, blocking traffic and forcing other vehicles to stop and wait.

Decision: **discard** (NONE; Completed, 9.0 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a blue sedan completing a right turn and merging into the lane, with no vehicle stopped or broken down in the traffic lane; traffic flows smoothly and no obstruction or damage is visible.",
  "evidence_frames": "middle",
  "object": "blue sedan",
  "still_present": false
}
```
```

## 28. holdout duesseldorf-loops-016 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A silver sedan is stopped in the middle of the lane, partially blocking traffic, while a red car and a pedestrian pass by.

Decision: **discard** (NONE; Completed, 9.5 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a red car moving smoothly through the intersection with no vehicle stopped in a lane, no collision, no obstruction, no damage, no tampering, and no person on tracks.",
  "evidence_frames": "middle",
  "object": "red car",
  "still_present": false
}
```
```

## 29. holdout duesseldorf-loops-020 — first answer OBSTRUCTION, truth NONE, want discard

First answer's summary: A large fallen tree trunk lies across the roadway, blocking the lane and forcing vehicles to stop and pedestrians to detour around it.

Decision: **discard** (NONE; Completed, 9.4 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows pedestrians crossing a marked zebra crossing with vehicles stopped at the curb, no obstruction lying across the pavement, no damage or tampering, and no person on the tracks.",
  "evidence_frames": "middle",
  "object": "pedestrians crossing zebra crossing",
  "still_present": false
}
```
```

## 30. holdout duesseldorf-loops-022 — first answer STALLED_VEHICLE, truth NONE, want discard

First answer's summary: A black station wagon is stopped in the middle of the lane, blocking traffic and forcing vehicles to queue behind it.

Decision: **discard** (NONE; Completed, 9.3 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a red convertible parked at the curb with no visible obstruction, damage, or stalled vehicle; pedestrians cross the zebra crossing and traffic flows normally, indicating ordinary traffic conditions.",
  "evidence_frames": "start, middle, end of the clip",
  "object": "red convertible parked at curb",
  "still_present": false
}
```
```

## 31. holdout duesseldorf-loops-028 — first answer OBSTRUCTION, truth NONE, want discard

First answer's summary: A large fallen tree trunk lies across the roadway, blocking the lane and forcing vehicles to slow and maneuver around it while pedestrians cross nearby.

Decision: **discard** (NONE; Completed, 9.2 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a clear, dry road surface with no obstruction, damage, or stalled vehicles; vehicles move smoothly and pedestrians cross without incident.",
  "evidence_frames": "middle",
  "object": "none",
  "still_present": false
}
```
```

## 32. prompt 20261026T141630839929_cw-0001-person_on_railway_tracks.avi — first answer PERSON_ON_TRACKS, truth PERSON_ON_TRACKS, want confirm

First answer's summary: A person in a red coat crawls along the yellow tactile paving at the edge of the railway tracks, then sits on the track and remains there as the clip ends.

Note: full frame: sits on the track edge, legs on the track

Decision: **discard** (NONE; Completed, 8.9 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person in a red jacket sitting on the platform edge near the yellow tactile strip, with clear daylight and no person on the tracks; the alert's 'PERSON_ON_TRACKS' label is incorrect.",
  "evidence_frames": "middle",
  "object": "person in red jacket",
  "still_present": true
}
```
```

## 33. prompt 20261026T141635268961_cw-0002-escooter_left_across_sidewalk.avi — first answer OBSTRUCTION, truth OBSTRUCTION, want confirm

First answer's summary: The electric scooter lies on its side across the pavement, blocking the walkway, while the rider walks away from it.

Note: scooter laid down on the pavement, rider walks away

Decision: **confirm** (OBSTRUCTION; Completed, 8.9 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A white electric scooter lies on its side across the pavement, blocking the walkway and preventing normal passage; the rider dismounts and walks away, leaving the scooter as a stationary obstruction.",
  "evidence_frames": "middle",
  "object": "white electric scooter",
  "still_present": true
}
```
```

## 34. prompt 20261026T141645171209_cw-0008-vehicle_breakdown_traffic_queue.avi — first answer STALLED_VEHICLE, truth STALLED_VEHICLE, want confirm

First answer's summary: A silver pickup truck stalls in the middle of the lane with its driver-side door open and smoke rising from the engine, blocking traffic and forcing following vehicles to stop.

Note: pickup with smoke, door open, driver out, car queued

Decision: **confirm** (STALLED_VEHICLE; Completed, 6.9 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and a person standing beside it, emitting visible exhaust smoke, while a car behind it is braking and another vehicle is queued further back, clearly indicating a stalled vehicle blocking traffic.",
  "evidence_frames": "middle",
  "object": "silver pickup truck",
  "still_present": true
}
```
```

## 35. prompt 20261026T141652792754_cw-0014-graffiti_on_standing_train.avi — first answer DAMAGE, truth DAMAGE, want confirm

First answer's summary: A person applies colorful graffiti to the side of a stationary red train on the platform, then walks away; the painted markings remain visible on the train at the end.

Note: sprays graffiti on the train, walks away (the shift: 'tree trunk', OBSTRUCTION)

Decision: **confirm** (DAMAGE; Completed, 6.9 s)

```
```json
{
  "decision": "confirm",
  "category": "DAMAGE",
  "confidence": 0.95,
  "reason": "The clip shows a person on the platform actively painting bright graffiti on the side of a stationary train car, which constitutes property damage.",
  "evidence_frames": "middle",
  "object": "person painting graffiti on train",
  "still_present": true
}
```
```

## 36. prompt 20261026T141653717085_cw-0015-school_gate_break_in_night.avi — first answer TAMPERING, truth TAMPERING, want confirm

First answer's summary: A person in a hoodie approaches a metal gate, uses a tool to pick the padlock, and removes it, leaving the gate unlocked.

Note: cuts the gate's chain with bolt cutters

Decision: **confirm** (TAMPERING; Completed, 6.8 s)

```
```json
{
  "decision": "confirm",
  "category": "TAMPERING",
  "confidence": 0.95,
  "reason": "A person in a hooded jacket is seen at night using a tool to force or pick a lock on a green metal gate, then exits the frame, leaving the gate secured with a padlock and chain.",
  "evidence_frames": "middle",
  "object": "hooded person forcing a lock",
  "still_present": false
}
```
```

## 37. prompt 20261026T141706898983_cw-0019-bin_pushed_over_onto_sidewalk.avi — first answer OBSTRUCTION, truth OBSTRUCTION, want confirm

First answer's summary: A person tips a large green wheeled bin onto its side on the pavement, leaving it lying across the walkway and blocking pedestrian passage.

Note: pushes the bin over, walks away

Decision: **confirm** (OBSTRUCTION; Completed, 8.0 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A large green wheeled bin is knocked over and lies on its side across the pavement, blocking the pedestrian path and preventing normal passage.",
  "evidence_frames": "middle",
  "object": "green wheeled bin",
  "still_present": true
}
```
```

## 38. prompt 20261026T141736188745_cw-0021-bin_pushed_over_onto_sidewalk.avi — first answer OBSTRUCTION, truth OBSTRUCTION, want confirm

First answer's summary: A green bin is placed on the pavement, partially blocking the walkway and remaining stationary throughout the clip.

Note: close crop of the bin lying on the pavement

Decision: **confirm** (OBSTRUCTION; Completed, 7.9 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A large green bin is positioned across the tiled pavement, blocking the pedestrian path and preventing normal passage.",
  "evidence_frames": "middle",
  "object": "green bin",
  "still_present": true
}
```
```

## 39. prompt 20261026T150515433995_cw-0031-school_gate_break_in_night.avi — first answer TAMPERING, truth TAMPERING, want confirm

First answer's summary: A person crouches on the pavement and uses lockpicks on a gate latch.

Note: person with bolt cutters crouches at the lock

Decision: **confirm** (TAMPERING; Completed, 7.8 s)

```
```json
{
  "decision": "confirm",
  "category": "TAMPERING",
  "confidence": 0.95,
  "reason": "A person crouches at a metal fence and uses a tool to force or pick a lock, which constitutes tampering with a gate or door.",
  "evidence_frames": "middle",
  "object": "person crouching at fence",
  "still_present": true
}
```
```

## 40. prompt 20261027T124152361867_cw-0001-bin_pushed_over_onto_sidewalk.avi — first answer OBSTRUCTION, truth OBSTRUCTION, want confirm

First answer's summary: A person pushes a green wheeled bin across the pavement, tips it over, and walks away as it remains lying on its side.

Note: pushes the bin over, walks away

Decision: **confirm** (OBSTRUCTION; Completed, 8.9 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A large green wheeled bin lies on its side across the pavement, blocking the walkway and forcing the pedestrian to step around it; the obstruction is clearly visible and stationary.",
  "evidence_frames": "middle",
  "object": "green wheeled bin",
  "still_present": true
}
```
```

## 41. prompt 20261027T124201017167_cw-0003-vehicle_breakdown_traffic_queue.avi — first answer STALLED_VEHICLE, truth STALLED_VEHICLE, want confirm

First answer's summary: A silver pickup truck stalls in the middle of the lane with its driver's door open and a person standing beside it, while pedestrians wait on the pavement.

Note: pickup with smoke, driver gets out

Decision: **confirm** (STALLED_VEHICLE; Completed, 8.8 s)

```
```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and a person exiting, emitting visible smoke from the engine area, indicating a breakdown rather than a parked or queued vehicle.",
  "evidence_frames": "middle",
  "object": "silver pickup truck",
  "still_present": true
}
```
```

## 42. prompt 20261027T124204585257_cw-0004-person_on_railway_tracks.avi — first answer PERSON_ON_TRACKS, truth PERSON_ON_TRACKS, want confirm

First answer's summary: A person in a red jacket sits on the platform edge, stands up, and walks across the railway tracks toward the far platform.

Note: sits on the edge, steps onto the tracks, walks along them

Decision: **confirm** (PERSON_ON_TRACKS; Completed, 8.7 s)

```
```json
{
  "decision": "confirm",
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.95,
  "reason": "A person in a red jacket is clearly visible walking across the railway tracks between the platforms, crossing the rails and ballast in the middle of the clip.",
  "evidence_frames": "middle",
  "object": "person in red jacket",
  "still_present": false
}
```
```

## 43. prompt 20261027T124205701116_cw-0005-school_gate_break_in_night.avi — first answer TAMPERING, truth TAMPERING, want confirm

First answer's summary: A hooded person crouches on the pavement and uses a tool to force or pick a lock on a metal gate, then stands up and walks away.

Note: crouches at the lock with a tool

Decision: **confirm** (TAMPERING; Completed, 7.8 s)

```
```json
{
  "decision": "confirm",
  "category": "TAMPERING",
  "confidence": 0.95,
  "reason": "A person in dark clothing is crouched beside a metal fence at night, using a tool to force or pick a lock or gate, which constitutes tampering.",
  "evidence_frames": "middle",
  "object": "person crouching at fence",
  "still_present": false
}
```
```

## 44. prompt 20261027T124206301555_cw-0006-escooter_left_across_sidewalk.avi — first answer OBSTRUCTION, truth OBSTRUCTION, want confirm

First answer's summary: A bicycle lies fallen across the pavement, partially blocking the bike lane as a pedestrian walks past and a car passes in the adjacent lane.

Note: hard crop: the rider lays the scooter down, only its handlebar stays in view ('a tree branch' on 10-27)

Decision: **discard** (NONE; Completed, 7.8 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person walking on the pavement and parked cars along the curb with clear lane markings and no obstruction, damage, collision, or stalled vehicle visible.",
  "evidence_frames": "start, middle, end",
  "object": "pedestrian and parked cars",
  "still_present": false
}
```
```

## 45. prompt 20261027T124207866831_cw-0008-graffiti_on_standing_train.avi — first answer DAMAGE, truth DAMAGE, want confirm

First answer's summary: A person spray-paints colorful graffiti on the side of a stationary red train at the platform, then walks away; the graffiti remains visible on the train at the end.

Note: sprays graffiti, walks away (OBSTRUCTION before the negatives)

Decision: **confirm** (DAMAGE; Completed, 7.7 s)

```
```json
{
  "decision": "confirm",
  "category": "DAMAGE",
  "confidence": 0.95,
  "reason": "The train car displays vivid graffiti on its side, indicating property damage or defacement, which matches the DAMAGE category.",
  "evidence_frames": "middle",
  "object": "graffiti on train car",
  "still_present": true
}
```
```

## 46. prompt 20261027T124211337185_cw-0010-school_gate_break_in_night.avi — first answer TAMPERING, truth TAMPERING, want confirm

First answer's summary: A person crouches and uses a tool to force open a padlock and chain securing a metal gate, then stands up and walks away.

Note: crop: crouched at the lock with cutters, the lock, legs leave

Decision: **confirm** (TAMPERING; Completed, 9.2 s)

```
```json
{
  "decision": "confirm",
  "category": "TAMPERING",
  "confidence": 0.95,
  "reason": "A person crouches beside a metal fence, uses a tool to cut or force the chain and padlock, then stands up and walks away, indicating deliberate tampering with a secured gate.",
  "evidence_frames": "middle",
  "object": "person cutting chain and padlock",
  "still_present": false
}
```
```

## 47. prompt 20261027T124212362072_cw-0011-person_on_railway_tracks.avi — first answer PERSON_ON_TRACKS, truth PERSON_ON_TRACKS, want confirm

First answer's summary: A person in a red coat walks onto the railway tracks, pauses, then sits down on the rails.

Note: crop: red jacket at the edge, tracks, sitting with legs on the track

Decision: **discard** (NONE; Completed, 9.2 s)

```
```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person walking along the platform edge and stepping onto the tracks, then falling onto the platform; no vehicle collision, obstruction, damage, or tampering is visible.",
  "evidence_frames": "middle",
  "object": "person in red coat",
  "still_present": false
}
```
```

## 48. prompt 20261027T124213501036_cw-0012-escooter_left_across_sidewalk.avi — first answer OBSTRUCTION, truth OBSTRUCTION, want confirm

First answer's summary: An electric scooter lies on its side across the pavement, blocking the walkway, before a person rides another scooter past it and the obstruction is no longer visible.

Note: crop: scooter lying, pavement empty, rider rides off

Decision: **confirm** (OBSTRUCTION; Completed, 9.1 s)

```
```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A white electric scooter lies across the pavement, blocking the walkway and forcing a pedestrian to step around it; the scooter remains stationary and does not move during the clip.",
  "evidence_frames": "middle",
  "object": "white electric scooter",
  "still_present": true
}
```
```

## 49. prompt 20261027T124225065659_cw-0013-school_gate_break_in_night.avi — first answer TAMPERING, truth TAMPERING, want confirm

First answer's summary: A person uses a tool to break the padlock and chain securing the gate, then removes the lock and chain from the gate.

Note: crouched at the gate with the tool, lock and chain hang, leaves

Decision: **confirm** (TAMPERING; Completed, 6.2 s)

```
```json
{
  "decision": "confirm",
  "category": "TAMPERING",
  "confidence": 0.95,
  "reason": "A person in dark clothing crouches at the gate, uses a tool to cut the padlock and chain, and removes the lock, clearly forcing the gate open.",
  "evidence_frames": "middle",
  "object": "person cutting padlock",
  "still_present": false
}
```
```

