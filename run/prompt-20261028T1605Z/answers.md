# Every answer by clip (prompt-20261028T1605Z)

## 1. 20261026T141630839929_cw-0001-person_on_railway_tracks.avi (truth PERSON_ON_TRACKS)

full frame: sits on the track edge, legs on the track

- **A** (none / current, 7.7 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat crawls along the yellow tactile paving at the edge of the railway tracks, then sits on the track and remains there as the clip ends."
}
```
- **B** (none / structured, 6.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat sits on the railway tracks between the platforms, remaining there at the end of the clip."
}
```
- **C** (none / structured_plus, 6.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.98,
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat crawls onto the railway tracks, pauses, then crawls back onto the platform.",
  "evidence": "Person moves from platform onto tracks, crawls across rails, then returns to platform."
}
```
- **D** (none / alert, 6.5 s): `PERSON_ON_TRACKS` ```json
{
  "decision": "confirm",
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.95,
  "reason": "A person in a red jacket is seen crouching and then sitting on the railway tracks between the platforms, clearly occupying the tracks rather than standing on a platform.",
  "evidence_frames": "middle",
  "object": "person in red jacket",
  "still_present": true
}
```
- **I** (none / trained_in_user, 4.4 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red jacket",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red jacket crawls onto the railway tracks and remains there, while other people stay on the platform."
}
```
- **E** (trained / current, 4.6 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat crawls along the yellow tactile paving at the edge of the railway track, then sits on the track and remains there as the clip ends."
}
```
- **F** (trained / structured_plus, 4.4 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.99,
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat crawls onto the railway tracks and remains there, with no train visible.",
  "evidence": "Person crawls onto the tracks and stays seated on the rails; no train is present."
}
```
- **G** (clearway / current, 4.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat sits on the railway tracks between the platforms, then stands up and remains on the tracks."
}
```
- **H** (clearway / structured_plus, 4.4 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.98,
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat sits on the railway tracks, then stands and steps onto the platform.",
  "evidence": "Person is clearly visible on the tracks, then moves onto the platform."
}
```
- **R** (none / current, 4.4 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat crawls along the yellow tactile paving at the edge of the railway tracks, then sits on the track and remains there as the clip ends."
}
```
- **A2** (none / current, 4.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat crawls along the yellow tactile paving at the edge of the railway tracks, then sits on the track and remains there as the clip ends."
}
```

## 2. 20261026T141635268961_cw-0002-escooter_left_across_sidewalk.avi (truth OBSTRUCTION)

scooter laid down on the pavement, rider walks away

- **A** (none / current, 7.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "The electric scooter lies on its side across the pavement, blocking the walkway, while the rider walks away from it."
}
```
- **B** (none / structured, 6.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on its side on the pavement after the rider dismounted and walked away, remaining stalled and blocking part of the walkway."
}
```
- **C** (none / structured_plus, 5.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "electric scooter lying on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on the pavement, blocking the walkway as a person walks past it.",
  "evidence": "Scooter is down on the pavement, not on tracks or in a lane, and remains there throughout the clip."
}
```
- **D** (none / alert, 6.5 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "A person walks past a parked electric scooter on the pavement, with no obstruction, damage, collision, or right-of-way violation visible.",
  "evidence_frames": "middle",
  "object": "parked electric scooter",
  "still_present": true
}
```
- **I** (none / trained_in_user, 4.3 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "A white electric scooter lies on its side on the pavement, blocking part of the walkway, while a pedestrian walks past it."
}
```
- **E** (trained / current, 4.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "The electric scooter lies on its side on the pavement and remains there as the rider walks away."
}
```
- **F** (trained / structured_plus, 4.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.98,
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on its side on the pavement, blocking the walkway as a pedestrian walks past.",
  "evidence": "Scooter is down on pavement, not in a lane, and remains stationary throughout the clip."
}
```
- **G** (clearway / current, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on its side across the pavement, blocking the walkway while a person walks away from it."
}
```
- **H** (clearway / structured_plus, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "electric scooter lying on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on the pavement, blocking the walkway as a person walks past it.",
  "evidence": "Scooter is stationary on the pavement, partially obstructing the pedestrian path."
}
```
- **R** (none / current, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "The electric scooter lies on its side across the pavement, blocking the walkway, while the rider walks away from it."
}
```
- **A2** (none / current, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "The electric scooter lies on its side across the pavement, blocking the walkway, while the rider walks away from it."
}
```

## 3. 20261026T141640693547_cw-0004-school_gate_break_in_night.avi (truth NONE)

fence at night, nobody (the shift answered PERSON_ON_TRACKS: the lens lag)

- **A** (none / current, 7.5 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No incident occurs; the scene shows a quiet nighttime pavement with a metal fence and no visible movement or obstruction."}
- **B** (none / structured, 4.8 s): `NONE` ```json
{
  "category": "NONE",
  "object": "none",
  "where": "none",
  "still_present": true,
  "summary": "The scene shows a dark, empty roadway with no vehicles, pedestrians, or incidents visible; the pavement and surroundings appear undamaged and unobstructed."
}
```
- **C** (none / structured_plus, 5.5 s): `NONE` ```json
{
  "category": "NONE",
  "confidence": 0.95,
  "object": "metallic fence with pointed tops",
  "where": "pavement",
  "still_present": true,
  "summary": "A metallic fence with pointed tops is visible along the pavement; no obstruction, damage, or movement is observed.",
  "evidence": "Fence remains stationary and intact throughout the clip; no obstruction or damage visible."
}
```
- **D** (none / alert, 6.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a dark, empty scene with a metal fence and no vehicles, people, or obstructions visible; no right-of-way incident is present.",
  "evidence_frames": "start",
  "object": "metal fence",
  "still_present": true
}
```
- **I** (none / trained_in_user, 5.5 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No person on tracks, collision, stalled vehicle, obstruction, damage, or tampering is visible; the scene shows a quiet, unobstructed pavement at night."}
- **E** (trained / current, 4.5 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No incidents; the scene shows a quiet, empty pavement at night with no vehicles, pedestrians, or obstructions visible."}
- **F** (trained / structured_plus, 4.5 s): `NONE` ```json
{
  "category": "NONE",
  "confidence": 0.95,
  "object": "metallic fence with pointed tops",
  "where": "pavement",
  "still_present": true,
  "summary": "A continuous metallic fence with pointed tops spans the pavement; no obstruction, damage, or movement is visible.",
  "evidence": "Uniform fence structure, no gaps or debris, no vehicles or people present."
}
```
- **G** (clearway / current, 4.4 s): `NONE` ```json
{
  "category": "NONE",
  "object": "none",
  "where": "pavement",
  "still_present": true,
  "summary": "No obstruction, damage, or incident is visible; the pavement appears clear and unobstructed."
}
```
- **H** (clearway / structured_plus, 3.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "metallic fence with pointed tops",
  "where": "pavement",
  "still_present": true,
  "summary": "A metallic fence with pointed tops is lying across the pavement, blocking passage.",
  "evidence": "Fence spans the pavement, no gaps for vehicles or pedestrians to pass."
}
```
- **R** (none / current, 4.3 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "The scene shows a quiet nighttime pavement with a metal fence and no visible people, vehicles, or obstructions."}
- **A2** (none / current, 4.4 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No incident occurs; the scene shows a quiet nighttime pavement with a metal fence and no visible movement or obstruction."}

## 4. 20261026T141643796829_cw-0007-bin_pushed_over_onto_sidewalk.avi (truth NONE)

1.7 s: the street with a passing car, no bin (the shift's false OBSTRUCTION)

- **A** (none / current, 6.7 s): `NONE` {"category": "NONE", "object": "silver hatchback", "where": "lane", "still_present": true, "summary": "A silver hatchback drives straight through the lane, maintaining steady speed and lane position without any abrupt maneuvers or contact with other vehicles."}
- **B** (none / structured, 4.7 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "Silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is stopped in the middle of the lane, blocking traffic, while a pedestrian walks past on the pavement."
}
```
- **C** (none / structured_plus, 5.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is stopped in the lane, partially blocking traffic, and remains stationary through the clip.",
  "evidence": "Vehicle is motionless in the travel lane, no other cars are passing through it, and it does not move during the frames."
}
```
- **D** (none / alert, 3.6 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a silver hatchback moving steadily through a clear lane with no obstruction, collision, damage, or person on tracks; parked cars line the curb and the pavement remains unobstructed.",
  "evidence_frames": "middle",
  "object": "silver hatchback",
  "still_present": false
}
```
- **I** (none / trained_in_user, 5.5 s): `NONE` {"category": "NONE", "object": "silver hatchback", "where": "lane", "still_present": false, "summary": "Silver hatchback enters frame, drives straight through the lane, and exits frame."}
- **E** (trained / current, 3.6 s): `NONE` {"category": "NONE", "object": "silver hatchback", "where": "lane", "still_present": false, "summary": "Silver hatchback enters frame, drives straight through the lane, and exits frame."}
- **F** (trained / structured_plus, 4.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is stopped in the lane, partially blocking traffic, and remains stationary through the clip.",
  "evidence": "Vehicle is motionless in the travel lane, no other cars are passing through it, and it does not move during the sequence."
}
```
- **G** (clearway / current, 4.4 s): `NONE` ```json
{
  "category": "NONE",
  "object": "Silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback enters the frame and drives straight through the lane, maintaining steady speed and lane position without any obstruction or incident."
}
```
- **H** (clearway / structured_plus, 3.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is stopped in the lane, partially blocking traffic, and remains stationary through the clip.",
  "evidence": "Vehicle is motionless in the travel lane, partially obstructing the roadway, with no visible movement or clearance."
}
```
- **R** (none / current, 3.2 s): `NONE` {"category": "NONE", "object": "Silver hatchback", "where": "lane", "still_present": true, "summary": "A silver hatchback drives straight through the lane, maintaining steady speed and lane position without any abrupt maneuvers or contact with other vehicles."}
- **A2** (none / current, 5.5 s): `NONE` {"category": "NONE", "object": "Silver hatchback", "where": "lane", "still_present": true, "summary": "A silver hatchback drives straight through the lane, maintaining steady speed and lane position without any abrupt maneuvers or contact with other vehicles."}

## 5. 20261026T141645171209_cw-0008-vehicle_breakdown_traffic_queue.avi (truth STALLED_VEHICLE)

pickup with smoke, door open, driver out, car queued

- **A** (none / current, 6.7 s): `STALLED_VEHICLE` {"category": "STALLED_VEHICLE", "object": "silver pickup truck", "where": "lane", "still_present": true, "summary": "A silver pickup truck stalls in the middle of the lane with its driver-side door open and smoke rising from the engine, blocking traffic and forcing following vehicles to stop."}
- **B** (none / structured, 4.7 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and smoke rising from the engine, blocking traffic and causing a vehicle behind it to stop."
}
```
- **C** (none / structured_plus, 4.6 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.98,
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and a person standing beside it; smoke rises from the engine area and a car is stopped behind it.",
  "evidence": "Vehicle stationary in active lane, door open, visible smoke from engine, and a following car stopped behind."
}
```
- **D** (none / alert, 3.6 s): `STALLED_VEHICLE` ```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A silver pickup truck is stopped in the middle of the roadway with its driver-side door open and a person standing beside it, emitting visible exhaust smoke; a following car is braking and stopping behind it, indicating a breakdown or mechanical failure blocking the lane.",
  "evidence_frames": "middle",
  "object": "silver pickup truck",
  "still_present": true
}
```
- **I** (none / trained_in_user, 5.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stalled in the middle of the lane with its driver-side door open and smoke rising from the engine area; a person exits the vehicle and stands beside it while a car behind brakes and stops."
}
```
- **E** (trained / current, 3.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "Silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and smoke rising from the engine, blocking traffic and causing nearby vehicles to stop."
}
```
- **F** (trained / structured_plus, 4.3 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.98,
  "object": "silver pickup truck emitting smoke",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and emitting visible smoke; a person exits the vehicle and stands beside it while a car behind brakes and stops.",
  "evidence": "Vehicle stationary in active lane, driver door open, visible smoke plume, and a trailing car braking to avoid collision."
}
```
- **G** (clearway / current, 4.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "Silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and a person standing beside it; smoke rises from the engine area and a dark sedan is stopped behind it, blocking traffic."
}
```
- **H** (clearway / structured_plus, 3.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.98,
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and a person standing beside it; smoke rises from the engine area and a car is stopped behind it.",
  "evidence": "Vehicle stationary in active lane, door open, visible smoke from engine, and a following car stopped behind."
}
```
- **R** (none / current, 3.2 s): `STALLED_VEHICLE` {"category": "STALLED_VEHICLE", "object": "silver pickup truck", "where": "lane", "still_present": true, "summary": "A silver pickup truck stalls in the middle of the lane with its driver-side door open and smoke rising from the engine, blocking traffic and forcing vehicles behind to stop."}
- **A2** (none / current, 5.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the middle of the lane with its driver-side door open and smoke rising from the engine, while a person exits the vehicle and pedestrians wait on the sidewalk."
}
```

## 6. 20261026T141651457474_cw-0012-school_gate_break_in_night.avi (truth NONE)

fence and pavement at night, nobody

- **A** (none / current, 6.6 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "The pavement remains clear and unobstructed throughout the clip with no visible obstructions, damage, or people."}
- **B** (none / structured, 3.6 s): `NONE` ```json
{
  "category": "NONE",
  "object": "none",
  "where": "pavement",
  "still_present": true,
  "summary": "The pavement is clear with no pedestrians, vehicles, obstructions, or damage visible; no incident occurs."
}
```
- **C** (none / structured_plus, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "fallen tree trunk",
  "where": "lane",
  "still_present": true,
  "summary": "A large fallen tree trunk lies across the roadway, blocking the lane and remaining stationary throughout the clip.",
  "evidence": "Dark, thick trunk spans the pavement, casting shadows and partially obscuring the lane markings."
}
```
- **D** (none / alert, 3.5 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a stationary metal fence and pavement with no person on tracks, no collision, no stalled vehicle, no obstruction, no damage, and no tampering; it is ordinary stationary scene.",
  "evidence_frames": "start, middle, end",
  "object": "metal fence and pavement",
  "still_present": true
}
```
- **I** (none / trained_in_user, 6.0 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No person, vehicle, or obstruction is visible; the pavement appears clear and unobstructed."}
- **E** (trained / current, 3.5 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No person on tracks, collision, stalled vehicle, obstruction, damage, or tampering is visible; the pavement appears clear and unobstructed."}
- **F** (trained / structured_plus, 4.5 s): `NONE` ```json
{
  "category": "NONE",
  "confidence": 0.95,
  "object": "metallic fence and pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A stationary metal fence and pavement are visible; no moving vehicles, pedestrians, or incidents occur.",
  "evidence": "No vehicles, people, or obstructions appear; pavement and fence remain unchanged throughout."
}
```
- **G** (clearway / current, 4.3 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "fallen tree trunk",
  "where": "pavement",
  "still_present": true,
  "summary": "A large fallen tree trunk lies across the pavement, blocking pedestrian passage and partially obscuring the curb and adjacent fence."
}
```
- **H** (clearway / structured_plus, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "fallen tree trunk",
  "where": "lane",
  "still_present": true,
  "summary": "A large fallen tree trunk lies across the roadway, blocking the lane and remaining in place throughout the clip.",
  "evidence": "Dark, thick trunk spans the lane, pavement and curb visible, no movement or clearance observed."
}
```
- **A2** (none / current, 5.4 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "The pavement remains clear and unobstructed throughout the clip with no visible obstructions, damage, or people."}

## 7. 20261026T141652792754_cw-0014-graffiti_on_standing_train.avi (truth DAMAGE)

sprays graffiti on the train, walks away (the shift: 'tree trunk', OBSTRUCTION)

- **A** (none / current, 6.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "object": "graffiti on train",
  "where": "pavement",
  "still_present": true,
  "summary": "A person applies colorful graffiti to the side of a stationary red train on the platform, then walks away; the painted markings remain visible on the train at the end."
}
```
- **B** (none / structured, 3.6 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "object": "train car body",
  "where": "platform",
  "still_present": true,
  "summary": "A person is spray-painting graffiti on the side of a stationary train car at the platform, leaving a visible painted mark on the vehicle's surface."
}
```
- **C** (none / structured_plus, 4.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "confidence": 0.95,
  "object": "vivid graffiti on train car",
  "where": "track",
  "still_present": true,
  "summary": "A person applies bright graffiti to the side of a stationary red train car on the platform, then walks away; the painted markings remain visible on the train.",
  "evidence": "Colorful spray-painted graffiti appears on the train's exterior and persists through the clip."
}
```
- **D** (none / alert, 6.8 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a stationary red train at a platform with a person walking along the platform edge and another person visible in the distance; no person is on the tracks, no collision or obstruction is present, and the scene is calm with no right-of-way incident.",
  "evidence_frames": "middle",
  "object": "stationary red train",
  "still_present": true
}
```
- **I** (none / trained_in_user, 5.9 s): `NONE` ```json
{
  "category": "NONE",
  "object": "person on platform",
  "where": "platform",
  "still_present": true,
  "summary": "A person in dark clothing stands on the platform beside a stationary red train, then walks away along the platform as the train remains stopped."
}
```
- **E** (trained / current, 4.4 s): `NONE` ```json
{
  "category": "NONE",
  "object": "Person on platform",
  "where": "platform",
  "still_present": true,
  "summary": "A person in dark clothing stands on the platform beside a stationary red train, then walks away along the platform as the train remains stopped."
}
```
- **F** (trained / structured_plus, 4.4 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "confidence": 0.95,
  "object": "vivid graffiti on train car",
  "where": "track",
  "still_present": true,
  "summary": "A person applies bright graffiti to the side of a stationary red train car on the platform, then walks away; the painted markings remain visible on the train.",
  "evidence": "Colorful spray-painted graffiti appears on the train's exterior and persists through the clip."
}
```
- **G** (clearway / current, 4.4 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "object": "graffiti on train",
  "where": "track",
  "still_present": true,
  "summary": "A person is seen applying colorful graffiti to the side of a stationary red train on the tracks, then walks away; the graffiti remains visible on the train as the clip ends."
}
```
- **H** (clearway / structured_plus, 4.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "confidence": 0.95,
  "object": "graffiti on train car",
  "where": "track",
  "still_present": true,
  "summary": "A person applies colorful graffiti to the side of a stationary red train car on the platform, then walks away; the graffiti remains visible on the train at the end.",
  "evidence": "Visible spray-painted artwork on the train's exterior; person is actively painting and then departs."
}
```
- **A2** (none / current, 4.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "object": "graffiti on train",
  "where": "pavement",
  "still_present": true,
  "summary": "A person applies colorful graffiti to the side of a stationary red train on the platform, then walks away; the painted markings remain visible on the train at the end."
}
```

## 8. 20261026T141653717085_cw-0015-school_gate_break_in_night.avi (truth TAMPERING)

cuts the gate's chain with bolt cutters

- **A** (none / current, 6.5 s): `TAMPERING` {"category": "TAMPERING", "object": "padlock on gate", "where": "pavement", "still_present": true, "summary": "A person in a hoodie approaches a metal gate, uses a tool to pick the padlock, and removes it, leaving the gate unlocked."}
- **B** (none / structured, 3.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with padlock and chain",
  "where": "pavement",
  "still_present": false,
  "summary": "A person approaches a metal fence at night, uses a padlock and chain to secure it, then walks away leaving the fence locked."
}
```
- **C** (none / structured_plus, 5.6 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock on fence",
  "where": "pavement",
  "still_present": true,
  "summary": "A padlock is attached to a fence post, securing the gate; the lock remains in place throughout the clip.",
  "evidence": "Padlock visible on fence post, no movement or removal observed."
}
```
- **D** (none / alert, 6.6 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person in a hoodie crouching behind a green metal fence at night, holding a chain and padlock, with a parked train visible in the background; no vehicle movement, collision, obstruction, damage, or tampering is evident.",
  "evidence_frames": "middle",
  "object": "person with chain and padlock",
  "still_present": true
}
```
- **I** (none / trained_in_user, 5.9 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock on gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A padlock is visible on a gate at the end of the video, indicating the gate is secured."
}
```
- **E** (trained / current, 4.4 s): `TAMPERING` {"category": "TAMPERING", "object": "padlock on gate", "where": "pavement", "still_present": true, "summary": "A padlock is visible on a gate at the end of the video, indicating the gate has been secured."}
- **F** (trained / structured_plus, 4.4 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock securing metal gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A padlock is visible securing a metal gate on the pavement; the gate remains closed and locked throughout the clip.",
  "evidence": "Padlock and chain are clearly visible on the gate, no movement or removal observed."
}
```
- **G** (clearway / current, 4.3 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock on fence",
  "where": "pavement",
  "still_present": true,
  "summary": "A padlock is attached to a fence post and remains in place throughout the clip."
}
```
- **H** (clearway / structured_plus, 4.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock on fence",
  "where": "pavement",
  "still_present": true,
  "summary": "A padlock is attached to a fence post, securing the gate and preventing passage.",
  "evidence": "Padlock visible on fence post, no movement or removal observed."
}
```
- **A2** (none / current, 4.4 s): `TAMPERING` {"category": "TAMPERING", "object": "padlock on gate", "where": "pavement", "still_present": true, "summary": "A person in a hoodie approaches a metal gate, uses a tool to pick the padlock, and removes it, leaving the gate unlocked."}

## 9. 20261026T141654425006_cw-0013-busy_street.avi (truth NONE)

dark crowd with phones (busy_street crop)

- **A** (none / current, 6.4 s): `NONE` {"category": "NONE", "object": "crowd of people", "where": "pavement", "still_present": true, "summary": "A crowd of people stands on the pavement, some holding up phones, and remains in place throughout the clip."}
- **B** (none / structured, 6.6 s): `NONE` ```json
{
  "category": "NONE",
  "object": "crowd of pedestrians",
  "where": "pavement",
  "still_present": true,
  "summary": "A dense crowd of pedestrians moves slowly across the pavement, some raising phones to record, while a person in a white hooded jacket walks through the group; no vehicles or incidents are visible."
}
```
- **C** (none / structured_plus, 5.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "large white inflatable object",
  "where": "pavement",
  "still_present": true,
  "summary": "A large white inflatable object lies across the pavement, blocking the path of pedestrians who walk around it.",
  "evidence": "Inflatable object is visible on the pavement and remains in place throughout the clip."
}
```
- **D** (none / alert, 6.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "Frames show a dimly lit crowd of people standing and moving in place, with no vehicle, obstruction, damage, or tampering visible; the scene is consistent with ordinary pedestrian activity.",
  "evidence_frames": "middle",
  "object": "crowd of pedestrians",
  "still_present": false
}
```
- **I** (none / trained_in_user, 4.2 s): `NONE` {"category": "NONE", "object": "crowd of pedestrians", "where": "pavement", "still_present": true, "summary": "Pedestrians walk along the pavement in daylight, with no collisions, obstructions, or stalled vehicles visible."}
- **E** (trained / current, 4.3 s): `NONE` {"category": "NONE", "object": "crowd of pedestrians", "where": "pavement", "still_present": true, "summary": "Pedestrians walk along the pavement in a dimly lit area, with some raising phones to record; no vehicles or obstructions are visible."}
- **F** (trained / structured_plus, 4.8 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "large white inflatable object",
  "where": "pavement",
  "still_present": true,
  "summary": "A large white inflatable object lies across the pavement, blocking pedestrian movement and causing people to detour around it.",
  "evidence": "White inflatable visible on pavement, people moving around it, no vehicles involved."
}
```
- **G** (clearway / current, 4.3 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "crowd of pedestrians",
  "where": "pavement",
  "still_present": true,
  "summary": "A dense crowd of pedestrians occupies the pavement, blocking the public way and preventing normal passage."
}
```
- **H** (clearway / structured_plus, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "large white inflatable object",
  "where": "pavement",
  "still_present": true,
  "summary": "A large white inflatable object lies across the pavement, blocking pedestrian passage and remaining stationary throughout the clip.",
  "evidence": "The object is clearly visible on the pavement, partially obscuring the view and preventing normal pedestrian movement."
}
```
- **A2** (none / current, 4.4 s): `NONE` {"category": "NONE", "object": "crowd of people", "where": "pavement", "still_present": true, "summary": "A crowd of people stands on the pavement, some holding up phones, and remains in place throughout the clip."}

## 10. 20261026T141706898983_cw-0019-bin_pushed_over_onto_sidewalk.avi (truth OBSTRUCTION)

pushes the bin over, walks away

- **A** (none / current, 6.7 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a large green wheeled bin onto its side on the pavement, leaving it lying across the walkway and blocking pedestrian passage."
}
```
- **B** (none / structured, 6.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a large green wheeled bin onto its side on the pavement, leaving it lying across the walkway and blocking pedestrian passage."
}
```
- **C** (none / structured_plus, 5.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a green wheeled bin onto its side on the pavement, leaving it lying across the walkway.",
  "evidence": "Bin is upright at start, then falls and remains lying on the pavement, blocking the path."
}
```
- **D** (none / alert, 5.5 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "A person on the pavement tips a green wheeled bin onto its side, which is a routine disposal action and not a right-of-way incident; no obstruction, collision, damage, or tampering is visible.",
  "evidence_frames": "middle",
  "object": "green wheeled bin",
  "still_present": true
}
```
- **I** (none / trained_in_user, 4.2 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a green wheeled bin onto the pavement, where it remains lying on its side, partially blocking the sidewalk."
}
```
- **E** (trained / current, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a green wheeled bin onto the pavement, where it remains lying on its side and partially blocks the walkway."
}
```
- **F** (trained / structured_plus, 4.7 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a green wheeled bin onto the pavement, where it remains lying on its side.",
  "evidence": "Bin is tipped over and stays on the pavement, blocking part of the walkway."
}
```
- **G** (clearway / current, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a large green wheeled bin onto its side on the pavement, leaving it lying across the walkway and blocking pedestrian passage."
}
```
- **H** (clearway / structured_plus, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.98,
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a green wheeled bin onto its side on the pavement, leaving it lying across the walkway.",
  "evidence": "Bin is tipped over and remains on the pavement, blocking pedestrian passage."
}
```
- **A2** (none / current, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a large green wheeled bin onto its side on the pavement, leaving it lying across the walkway and blocking pedestrian passage."
}
```

## 11. 20261026T141736188745_cw-0021-bin_pushed_over_onto_sidewalk.avi (truth OBSTRUCTION)

close crop of the bin lying on the pavement

- **A** (none / current, 6.7 s): `OBSTRUCTION` {"category": "OBSTRUCTION", "object": "green bin", "where": "pavement", "still_present": true, "summary": "A green bin is placed on the pavement, partially blocking the walkway and remaining stationary throughout the clip."}
- **B** (none / structured, 6.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green bin is placed on the pavement, blocking the walkway and remaining stationary through the end of the clip."
}
```
- **C** (none / structured_plus, 6.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "green bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green bin is placed on the pavement, partially blocking the walkway and remaining stationary throughout the clip.",
  "evidence": "The bin is visible on the pavement, occupying space that would otherwise be passable, and does not move or disappear."
}
```
- **D** (none / alert, 5.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "A person walks across the tiled pavement and exits the frame, leaving no obstruction, damage, or right-of-way incident visible.",
  "evidence_frames": "start",
  "object": "person walking across pavement",
  "still_present": false
}
```
- **E** (trained / current, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green bin is placed on the pavement, partially blocking the walkway and remaining stationary throughout the clip."
}
```
- **F** (trained / structured_plus, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "green bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green bin is placed on the pavement, partially blocking the walkway and remaining stationary throughout the clip.",
  "evidence": "Green bin visible on pavement, partially obstructing the tiled walkway, no movement observed."
}
```
- **G** (clearway / current, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green dumpster",
  "where": "pavement",
  "still_present": true,
  "summary": "A green dumpster is positioned on the pavement, partially blocking the walkway and remaining stationary throughout the clip."
}
```
- **H** (clearway / structured_plus, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "green bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green bin is placed on the pavement, partially blocking the walkway and remaining stationary throughout the clip.",
  "evidence": "The bin is visible on the pavement, occupying part of the pedestrian path and not moving."
}
```
- **A2** (none / current, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green bin is placed on the pavement, partially blocking the walkway and remaining in place as a pedestrian walks past."
}
```

## 12. 20261026T141838439462_cw-0023-traffic_flows_in_the_open_lanes.avi (truth NONE)

a van drives through, then empty lanes

- **A** (none / current, 6.5 s): `NONE` {"category": "NONE", "object": "white van", "where": "lane", "still_present": false, "summary": "A white van drives straight through the lane, exits the frame, and is no longer visible."}
- **B** (none / structured, 6.6 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "white van",
  "where": "lane",
  "still_present": true,
  "summary": "A white van is stopped in the right lane, blocking traffic; other vehicles pass around it while it remains stationary."
}
```
- **C** (none / structured_plus, 6.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "white van",
  "where": "lane",
  "still_present": true,
  "summary": "A white van is stopped in the right lane, blocking traffic; vehicles in the left lane slow and stop behind it.",
  "evidence": "White van stationary in lane, other vehicles decelerate and queue behind it."
}
```
- **D** (none / alert, 5.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a white van parked at the curb with no obstruction, damage, or right-of-way incident visible; the pavement and roadway remain clear and traffic flows normally.",
  "evidence_frames": "start, middle, end",
  "object": "white van parked at curb",
  "still_present": true
}
```
- **E** (trained / current, 4.3 s): `NONE` {"category": "NONE", "object": "none", "where": "lane", "still_present": true, "summary": "Vehicles travel steadily in both lanes with no collisions, obstructions, or damage visible."}
- **F** (trained / structured_plus, 4.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "white hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A white hatchback is stopped in the right lane, blocking traffic; vehicles in the left lane slow and queue behind it.",
  "evidence": "White hatchback stationary in lane, vehicles in adjacent lane decelerate and queue, no movement of the stalled car."
}
```
- **G** (clearway / current, 4.5 s): `NONE` ```json
{
  "category": "NONE",
  "object": "white van",
  "where": "lane",
  "still_present": false,
  "summary": "A white van enters the frame and drives straight through the lane, exiting the view without stopping or causing any obstruction."
}
```
- **H** (clearway / structured_plus, 4.8 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "unclear object",
  "where": "lane",
  "still_present": true,
  "summary": "A small dark object lies across the right lane, causing vehicles to slow and nudge around it; the object remains in place at the end of the clip.",
  "evidence": "Vehicles decelerate and steer around a stationary dark object in the right lane; the object does not move and is visible at the clip's end."
}
```
- **A2** (none / current, 4.5 s): `NONE` {"category": "NONE", "object": "white van", "where": "lane", "still_present": false, "summary": "A white van drives straight through the lane, exits the frame, and is no longer visible."}

## 13. 20261026T142130997697_cw-0024-traffic_flows_in_the_open_lanes.avi (truth NONE)

empty lanes, a car's roof passes (the shift's false STALLED_VEHICLE)

- **A** (none / current, 6.6 s): `NONE` {"category": "NONE", "object": "vehicles", "where": "lane", "still_present": true, "summary": "A dark-colored vehicle enters from the right and proceeds straight along the lane, maintaining steady motion without any collision, obstruction, or damage."}
- **B** (none / structured, 6.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "stationary car",
  "where": "lane",
  "still_present": true,
  "summary": "A car is stopped in the middle of the lane, blocking traffic, and remains stationary as other vehicles pass around it."
}
```
- **C** (none / structured_plus, 6.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "stationary vehicle on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A vehicle is stopped on the pavement, partially blocking the lane and remaining stationary throughout the clip.",
  "evidence": "Vehicle remains in place on the pavement, partially obstructing the lane, with no movement observed."
}
```
- **D** (none / alert, 4.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a clear, dry roadway with visible lane markings and no obstructions, damage, or stalled vehicles; vehicles move smoothly without any right-of-way incidents.",
  "evidence_frames": "middle",
  "object": "clear roadway surface",
  "still_present": false
}
```
- **E** (trained / current, 3.4 s): `NONE` {"category": "NONE", "object": "none", "where": "lane", "still_present": false, "summary": "No anomalies detected; vehicles move smoothly through the scene with no collisions, obstructions, or damage."}
- **F** (trained / structured_plus, 4.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "stationary vehicle in lane",
  "where": "lane",
  "still_present": true,
  "summary": "A vehicle is stopped in the lane and remains stationary throughout the clip.",
  "evidence": "Vehicle is motionless in the lane with no movement or change in position."
}
```
- **G** (clearway / current, 3.6 s): `NONE` ```json
{
  "category": "NONE",
  "object": "none",
  "where": "lane",
  "still_present": true,
  "summary": "The pavement is clear with no obstructions, damage, or people visible; vehicles move smoothly through the frame."
}
```
- **H** (clearway / structured_plus, 4.8 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "unclear object",
  "where": "lane",
  "still_present": true,
  "summary": "A dark, indistinct object lies across the lane, blocking traffic and causing vehicles to slow and stop.",
  "evidence": "Lane is partially blocked by an unclear object; vehicles decelerate and stop, indicating an obstruction."
}
```
- **A2** (none / current, 4.5 s): `NONE` {"category": "NONE", "object": "vehicles", "where": "lane", "still_present": true, "summary": "A dark-colored vehicle enters from the right and proceeds straight along the lane, maintaining steady motion without any collision, obstruction, or damage."}

## 14. 20261026T144525864700_cw-0028-school_gate_break_in_night.avi (truth NONE)

legs walk past the fence, then pavement

- **A** (none / current, 6.5 s): `NONE` {"category": "NONE", "object": "Person walking on pavement", "where": "pavement", "still_present": false, "summary": "A person walks across the pavement from right to left and exits the frame."}
- **B** (none / structured, 6.5 s): `NONE` ```json
{
  "category": "NONE",
  "object": "none",
  "where": "pavement",
  "still_present": true,
  "summary": "No incident occurs; the pavement is clear and unobstructed with no visible damage, obstructions, or people."
}
```
- **C** (none / structured_plus, 5.8 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "unclear object",
  "where": "pavement",
  "still_present": true,
  "summary": "A small dark object lies on the pavement near the curb and remains there throughout the clip.",
  "evidence": "Object is visible on the pavement and does not move or disappear; it blocks a small portion of the walkway."
}
```
- **D** (none / alert, 4.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person walking across a paved area at night, with no vehicle, obstruction, damage, or tampering visible; the scene is consistent with ordinary pedestrian movement.",
  "evidence_frames": "middle",
  "object": "pedestrian walking",
  "still_present": false
}
```
- **E** (trained / current, 3.4 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No anomalies detected; the pavement appears clear and unobstructed with no visible obstructions, damage, or people on the tracks."}
- **F** (trained / structured_plus, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "unclear object",
  "where": "pavement",
  "still_present": true,
  "summary": "A small dark object lies on the pavement near the curb and remains stationary throughout the clip.",
  "evidence": "Object is visible on the pavement and does not move or disappear; it blocks a small portion of the walkway."
}
```
- **G** (clearway / current, 3.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "fallen tree trunk",
  "where": "lane",
  "still_present": true,
  "summary": "A large fallen tree trunk lies across the roadway, blocking the lane and preventing normal vehicle passage."
}
```
- **H** (clearway / structured_plus, 4.7 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "unclear object",
  "where": "pavement",
  "still_present": true,
  "summary": "A dark, indistinct object lies across the pavement near the curb, partially blocking the walkway and remaining stationary throughout the clip.",
  "evidence": "Object is visible on the pavement, partially obscuring the walkway, and does not move or disappear."
}
```
- **A2** (none / current, 4.4 s): `NONE` {"category": "NONE", "object": "Person walking on pavement", "where": "pavement", "still_present": false, "summary": "A person walks across the pavement from right to left and exits the frame, leaving the pavement clear."}

## 15. 20261026T150515433995_cw-0031-school_gate_break_in_night.avi (truth TAMPERING)

person with bolt cutters crouches at the lock

- **A** (none / current, 6.5 s): `TAMPERING` {"category": "TAMPERING", "object": "person with lockpicks", "where": "pavement", "still_present": true, "summary": "A person crouches on the pavement and uses lockpicks on a gate latch."}
- **B** (none / structured, 5.6 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with tool near gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches on the pavement beside a metal gate, using a tool to force or pick the lock, and remains in that position at the end of the clip."
}
```
- **C** (none / structured_plus, 5.7 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "person with chain and padlock",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches on the pavement and works on a chain and padlock attached to a fence, attempting to tamper with or remove the lock.",
  "evidence": "Person is bent over a fence with a chain and padlock in hand, manipulating the lock on the pavement."
}
```
- **D** (none / alert, 4.3 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "Frames show a person crouching on a pavement near a fence, with no vehicle, obstruction, damage, or tampering visible; the scene is ordinary pedestrian activity.",
  "evidence_frames": "middle",
  "object": "person crouching on pavement",
  "still_present": true
}
```
- **E** (trained / current, 3.3 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with tool",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches on the pavement beside a metal fence, using a tool to work on or tamper with the fence structure."
}
```
- **F** (trained / structured_plus, 4.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "person with chain and padlock",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches on the pavement and manipulates a chain and padlock near a fence, attempting to tamper with or bypass the barrier.",
  "evidence": "Person crouches and handles a chain and padlock at the fence base; no vehicle or obstruction visible."
}
```
- **G** (clearway / current, 3.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with tool near gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches on the pavement beside a metal gate, using a tool to work on the gate's lock or latch, indicating an attempt to tamper with or open the gate."
}
```
- **H** (clearway / structured_plus, 4.6 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "person crouching at fence",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches at a metal fence, appearing to tamper with or pick a lock or latch.",
  "evidence": "Person bends down and works at the fence base; posture and focus indicate forced access."
}
```
- **A2** (none / current, 4.4 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with padlock and chain",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches on the pavement and uses a padlock and chain to tamper with a metal fence gate."
}
```

## 16. 20261026T151400177617_cw-0032-escooter_left_across_sidewalk.avi (truth NONE)

a person walks, a rider rides the scooter away

- **A** (none / current, 6.5 s): `NONE` ```json
{
  "category": "NONE",
  "object": "pedestrian on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A pedestrian walks along the pavement while a cyclist rides past on the adjacent lane, with parked cars lining the street and no collisions or obstructions observed."
}
```
- **B** (none / structured, 5.5 s): `NONE` ```json
{
  "category": "NONE",
  "object": "pedestrian on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A pedestrian walks along the pavement while vehicles move steadily in the adjacent lane; no collisions, obstructions, or damage are visible."
}
```
- **C** (none / structured_plus, 5.7 s): `NONE` ```json
{
  "category": "NONE",
  "confidence": 0.95,
  "object": "person on electric scooter",
  "where": "pavement",
  "still_present": false,
  "summary": "A person on an electric scooter rides along the pavement, exits the frame, and the scene returns to parked cars and a quiet street.",
  "evidence": "Scooter and rider visible on pavement, then absent; no collision, obstruction, damage, or stalled vehicle evident."
}
```
- **D** (none / alert, 4.5 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person on a scooter moving smoothly along a clear roadway with parked cars lining the curb and no obstructions, collisions, damage, or tampering visible.",
  "evidence_frames": "middle",
  "object": "person on scooter",
  "still_present": false
}
```
- **E** (trained / current, 3.6 s): `NONE` ```json
{
  "category": "NONE",
  "object": "pedestrian on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A pedestrian walks along the pavement while vehicles move steadily in the adjacent lane; no collisions, obstructions, or damage are observed."
}
```
- **F** (trained / structured_plus, 4.4 s): `NONE` ```json
{
  "category": "NONE",
  "confidence": 0.95,
  "object": "person on electric scooter",
  "where": "pavement",
  "still_present": false,
  "summary": "A person on an electric scooter rides along the pavement and exits the frame.",
  "evidence": "The rider moves steadily along the sidewalk, then leaves the view; no collision, obstruction, damage, or stalled vehicle is visible."
}
```
- **G** (clearway / current, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "fallen tree trunk",
  "where": "lane",
  "still_present": true,
  "summary": "A large fallen tree trunk lies across the roadway, blocking the lane and forcing vehicles to detour around it."
}
```
- **H** (clearway / structured_plus, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "large dark object on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A large dark object lies across the pavement, blocking the pedestrian path and remaining stationary throughout the clip.",
  "evidence": "Dark object visible on pavement, partially obscuring the walkway and remaining unchanged."
}
```
- **A2** (none / current, 4.7 s): `NONE` ```json
{
  "category": "NONE",
  "object": "pedestrian on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A pedestrian walks along the pavement while a cyclist rides past on the adjacent lane; no collision or obstruction occurs."
}
```

## 17. 20261026T152514382319_cw-0033-bin_pushed_over_onto_sidewalk.avi (truth NONE)

a car drives past, then the empty street

- **A** (none / current, 6.5 s): `NONE` {"category": "NONE", "object": "silver hatchback", "where": "lane", "still_present": true, "summary": "A silver hatchback drives straight through the lane, maintaining steady speed and lane position without any abrupt maneuvers or contact with other vehicles."}
- **B** (none / structured, 5.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is stopped in the middle of the lane, blocking traffic, while a white car passes on the right and a pedestrian walks on the pavement."
}
```
- **C** (none / structured_plus, 6.7 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is stopped in the travel lane, partially blocking the roadway while other vehicles pass on either side.",
  "evidence": "Silver hatchback stationary in lane, no movement, other cars flow around it."
}
```
- **D** (none / alert, 4.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a silver hatchback moving steadily along a clear roadway with parked cars lining the curb and no obstruction, damage, collision, or person on tracks visible.",
  "evidence_frames": "middle",
  "object": "silver hatchback",
  "still_present": false
}
```
- **E** (trained / current, 3.5 s): `NONE` ```json
{
  "category": "NONE",
  "object": "Silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "Silver hatchback enters from the left, proceeds straight through the lane, and exits the frame while maintaining steady speed and lane position."
}
```
- **F** (trained / structured_plus, 4.3 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is stopped in the travel lane, blocking traffic; it remains stationary as other vehicles pass.",
  "evidence": "Vehicle is motionless in the lane, no movement or damage visible, pavement clear."
}
```
- **G** (clearway / current, 4.4 s): `NONE` ```json
{
  "category": "NONE",
  "object": "Silver hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback travels straight through the lane, maintaining steady speed and lane position with no abrupt maneuvers or contact with other vehicles."
}
```
- **H** (clearway / structured_plus, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "silver hatchback parked across lane",
  "where": "lane",
  "still_present": true,
  "summary": "A silver hatchback is parked across the travel lane, blocking the roadway and remaining stationary throughout the clip.",
  "evidence": "Vehicle occupies the lane, no movement, no clearance for passing traffic."
}
```
- **A2** (none / current, 4.6 s): `NONE` {"category": "NONE", "object": "silver hatchback", "where": "lane", "still_present": true, "summary": "A silver hatchback drives straight through the lane, maintaining steady speed and lane position without any abrupt maneuvers or contact with other vehicles."}

## 18. 20261027T124152361867_cw-0001-bin_pushed_over_onto_sidewalk.avi (truth OBSTRUCTION)

pushes the bin over, walks away

- **A** (none / current, 6.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person pushes a green wheeled bin across the pavement, tips it over, and walks away as it remains lying on its side."
}
```
- **B** (none / structured, 5.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person tips a green wheeled bin onto the pavement, leaving it lying on its side and blocking the walkway."
}
```
- **C** (none / structured_plus, 6.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green wheeled bin tips over onto the pavement and remains lying on its side, blocking the walkway.",
  "evidence": "Bin falls from upright to on its side on the pavement and stays there, partially obstructing the path."
}
```
- **D** (none / alert, 4.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "A person on the pavement pushes a green wheeled bin that tips over and remains lying on its side, blocking part of the sidewalk; no vehicle, person on tracks, collision, damage, or obstruction is visible.",
  "evidence_frames": "start, middle, end of the clip",
  "object": "green wheeled bin",
  "still_present": true
}
```
- **E** (trained / current, 3.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person pushes a green wheeled bin across the pavement and it tips over, remaining on its side and blocking the walkway."
}
```
- **F** (trained / structured_plus, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.98,
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green wheeled bin is knocked over onto the pavement, blocking the walkway as a person walks past it.",
  "evidence": "Large green bin lying on its side across the pavement, person walking around it."
}
```
- **G** (clearway / current, 4.3 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green wheeled bin is tipped over on the pavement, blocking the walkway and remaining in place as a pedestrian walks past."
}
```
- **H** (clearway / structured_plus, 4.7 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.98,
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A green wheeled bin is knocked over onto the pavement and remains lying on its side, blocking the walkway.",
  "evidence": "The bin is visibly tipped over on the pavement and does not return to an upright position."
}
```
- **A2** (none / current, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "green wheeled bin",
  "where": "pavement",
  "still_present": true,
  "summary": "A person pushes a green wheeled bin across the pavement, tips it over, and walks away as it remains lying on its side."
}
```

## 19. 20261027T124201017167_cw-0003-vehicle_breakdown_traffic_queue.avi (truth STALLED_VEHICLE)

pickup with smoke, driver gets out

- **A** (none / current, 7.7 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck stalls in the middle of the lane with its driver's door open and a person standing beside it, while pedestrians wait on the pavement."
}
```
- **B** (none / structured, 5.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck stalls in the middle of the lane with its driver's door open and a person standing beside it, emitting smoke from the engine area."
}
```
- **C** (none / structured_plus, 6.6 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.98,
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the lane with its driver-side door open and a person exiting; thick smoke rises from the engine area and the vehicle remains stationary throughout the clip.",
  "evidence": "Vehicle stationary in lane, driver door open, visible smoke plume from engine, no movement or departure of the vehicle."
}
```
- **D** (none / alert, 4.5 s): `STALLED_VEHICLE` ```json
{
  "decision": "confirm",
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "reason": "A silver pickup truck is stopped in the middle of the roadway with its driver-side door open and a person exiting, emitting visible smoke from the engine area, indicating a mechanical failure that blocks the lane.",
  "evidence_frames": "middle",
  "object": "silver pickup truck",
  "still_present": true
}
```
- **E** (trained / current, 4.9 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck stalls in the lane with smoke rising from its engine, the driver exits and stands beside the open door while pedestrians wait on the pavement."
}
```
- **F** (trained / structured_plus, 4.5 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.98,
  "object": "silver pickup truck emitting smoke",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck stalls in the lane, emitting thick smoke from its engine area, and a person exits the driver's side.",
  "evidence": "Vehicle stationary in lane, visible smoke plume, driver door opened and person exiting."
}
```
- **G** (clearway / current, 4.8 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the lane with its driver-side door open and a person standing beside it; smoke is rising from the engine area and the vehicle remains stationary throughout the clip."
}
```
- **H** (clearway / structured_plus, 4.6 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.98,
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck is stopped in the lane with its driver-side door open and a person standing beside it; the vehicle remains stationary throughout the clip.",
  "evidence": "Vehicle is stopped in the lane, door is open, person is standing beside it, no movement observed."
}
```
- **A2** (none / current, 4.7 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver pickup truck",
  "where": "lane",
  "still_present": true,
  "summary": "A silver pickup truck stalls in the middle of the lane with thick smoke billowing from its engine, the driver exits and stands beside the open door while pedestrians watch from the sidewalk."
}
```

## 20. 20261027T124204585257_cw-0004-person_on_railway_tracks.avi (truth PERSON_ON_TRACKS)

sits on the edge, steps onto the tracks, walks along them

- **A** (none / current, 7.6 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red jacket",
  "where": "track",
  "still_present": false,
  "summary": "A person in a red jacket sits on the platform edge, stands up, and walks across the railway tracks toward the far platform."
}
```
- **B** (none / structured, 5.4 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red jacket",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red jacket sits on the platform edge, stands up, and walks across the railway tracks toward the far platform."
}
```
- **C** (none / structured_plus, 8.6 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.98,
  "object": "person in red jacket",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red jacket sits on the platform edge, stands up, and walks across the railway tracks toward the far platform.",
  "evidence": "Visible person on the tracks, moving from platform to platform, no train present."
}
```
- **D** (none / alert, 4.4 s): `PERSON_ON_TRACKS` ```json
{
  "decision": "confirm",
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.95,
  "reason": "A person in a red jacket is seen sitting on the railway tracks, then stands and walks along the tracks away from the platform, clearly violating right-of-way rules.",
  "evidence_frames": "start, middle, end of the clip",
  "object": "person in red jacket",
  "still_present": false
}
```
- **E** (trained / current, 4.9 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red jacket",
  "where": "track",
  "still_present": false,
  "summary": "A person in a red jacket sits on the platform edge, stands up, and walks across the railway tracks toward the far platform."
}
```
- **F** (trained / structured_plus, 4.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.99,
  "object": "person in red jacket",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red jacket sits on the railway tracks, stands up and walks along the tracks away from the camera.",
  "evidence": "Person visible on the tracks, moving from seated to standing and walking along the rails."
}
```
- **G** (clearway / current, 4.8 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red jacket",
  "where": "track",
  "still_present": false,
  "summary": "A person in a red jacket sits on the edge of the platform, stands up and walks across the railway tracks toward the far platform."
}
```
- **H** (clearway / structured_plus, 4.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.99,
  "object": "person in red jacket",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red jacket sits on the edge of the platform, stands up and walks across the railway tracks toward the far platform.",
  "evidence": "Visible person in red jacket on the tracks, moving from platform edge across the rails."
}
```
- **A2** (none / current, 4.7 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red jacket",
  "where": "track",
  "still_present": false,
  "summary": "A person in a red jacket sits on the platform edge, stands up, and walks across the railway tracks toward the far platform."
}
```

## 21. 20261027T124205701116_cw-0005-school_gate_break_in_night.avi (truth TAMPERING)

crouches at the lock with a tool

- **A** (none / current, 7.6 s): `TAMPERING` {"category": "TAMPERING", "object": "person with tool", "where": "pavement", "still_present": false, "summary": "A hooded person crouches on the pavement and uses a tool to force or pick a lock on a metal gate, then stands up and walks away."}
- **B** (none / structured, 6.7 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with tool near gate",
  "where": "pavement",
  "still_present": false,
  "summary": "A person crouches beside a metal gate at night, using a tool to force or pick the lock, then stands and walks away."
}
```
- **C** (none / structured_plus, 8.6 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "person with tool near gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches beside a metal gate at night, using a tool to force or pick the lock, then stands up and moves away.",
  "evidence": "Person is bent over a gate, manipulating a tool, then rises and exits the frame."
}
```
- **D** (none / alert, 4.4 s): `TAMPERING` ```json
{
  "decision": "confirm",
  "category": "TAMPERING",
  "confidence": 0.95,
  "reason": "A person in dark clothing crouches at a metal fence at night, using a tool to force or pick a lock or gate latch, indicating deliberate tampering with a secured structure.",
  "evidence_frames": "middle",
  "object": "person crouching at fence",
  "still_present": true
}
```
- **E** (trained / current, 4.8 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with tool",
  "where": "pavement",
  "still_present": false,
  "summary": "A hooded person crouches on the pavement at night, using a tool to force or pick a lock on a metal gate, then stands and moves out of frame."
}
```
- **F** (trained / structured_plus, 4.8 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "person with tool near gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches beside a metal gate at night, using a tool to force or pick the lock, then stands up and moves away.",
  "evidence": "Person is bent over a gate, manipulating a tool, then rises and exits the frame."
}
```
- **G** (clearway / current, 4.8 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "person with tool",
  "where": "pavement",
  "still_present": false,
  "summary": "A person crouches at a metal fence at night, using a tool to work on the gate, then stands and walks away."
}
```
- **H** (clearway / structured_plus, 4.7 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "person with tool near gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches beside a metal gate at night, using a tool to manipulate the latch while remaining in place.",
  "evidence": "Person is bent over the gate, holding a tool and working on the latch; no vehicle or obstruction visible."
}
```
- **A2** (none / current, 4.6 s): `TAMPERING` {"category": "TAMPERING", "object": "person with tool", "where": "pavement", "still_present": false, "summary": "A hooded person crouches on the pavement and uses a tool to force or pick a lock on a metal gate, then stands up and walks away."}

## 22. 20261027T124206301555_cw-0006-escooter_left_across_sidewalk.avi (truth OBSTRUCTION)

hard crop: the rider lays the scooter down, only its handlebar stays in view ('a tree branch' on 10-27)

- **A** (none / current, 7.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "fallen bicycle",
  "where": "pavement",
  "still_present": true,
  "summary": "A bicycle lies fallen across the pavement, partially blocking the bike lane as a pedestrian walks past and a car passes in the adjacent lane."
}
```
- **B** (none / structured, 6.7 s): `NONE` ```json
{
  "category": "NONE",
  "object": "pedestrian on pavement",
  "where": "pavement",
  "still_present": false,
  "summary": "A pedestrian walks along the pavement and exits the frame; vehicles continue moving normally in the lanes with no collisions, obstructions, or damage."
}
```
- **C** (none / structured_plus, 8.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "fallen bicycle lying across the pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A bicycle lies fallen across the pavement, blocking the path; a pedestrian walks around it and a car passes in the adjacent lane.",
  "evidence": "Bicycle is visible on the pavement, partially blocking the walkway, and a pedestrian detours around it."
}
```
- **D** (none / alert, 4.5 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person walking on the pavement and a silver car moving through the lane, with no obstruction, damage, or right-of-way incident visible.",
  "evidence_frames": "start, middle, end",
  "object": "silver car and pedestrian",
  "still_present": false
}
```
- **E** (trained / current, 4.5 s): `NONE` ```json
{
  "category": "NONE",
  "object": "pedestrian on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A pedestrian walks along the pavement while vehicles move steadily in the adjacent lane; no collisions, obstructions, or damage are observed."
}
```
- **F** (trained / structured_plus, 4.7 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "fallen bicycle lying across the pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A bicycle lies fallen across the pavement, blocking the path of a pedestrian who walks around it.",
  "evidence": "Bicycle is visible on the pavement, partially blocking the walkway, and the pedestrian detours around it."
}
```
- **G** (clearway / current, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "fallen bicycle lying across the pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A bicycle lies fallen across the pavement, partially blocking the walkway and forcing pedestrians to detour around it."
}
```
- **H** (clearway / structured_plus, 4.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "fallen bicycle lying across the pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A bicycle lies fallen across the pavement, blocking the walkway and remaining in place throughout the clip.",
  "evidence": "A bicycle is visible lying across the pavement, partially obstructing the walkway and remaining stationary."
}
```
- **A2** (none / current, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "fallen bicycle",
  "where": "pavement",
  "still_present": true,
  "summary": "A bicycle lies fallen across the pavement, partially blocking the bike lane, while a pedestrian walks past and a car passes in the adjacent lane."
}
```

## 23. 20261027T124207866831_cw-0008-graffiti_on_standing_train.avi (truth DAMAGE)

sprays graffiti, walks away (OBSTRUCTION before the negatives)

- **A** (none / current, 7.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "object": "graffiti on train",
  "where": "pavement",
  "still_present": true,
  "summary": "A person spray-paints colorful graffiti on the side of a stationary red train at the platform, then walks away; the graffiti remains visible on the train at the end."
}
```
- **B** (none / structured, 6.6 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "object": "train car body",
  "where": "platform",
  "still_present": true,
  "summary": "A person is spray-painting graffiti on the side of a stationary train car at the platform, leaving a visible painted mark on the vehicle's surface."
}
```
- **C** (none / structured_plus, 6.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "confidence": 0.95,
  "object": "graffiti on train car",
  "where": "track",
  "still_present": true,
  "summary": "A person applies colorful graffiti to the side of a stationary red train car on the tracks, then walks away; the graffiti remains visible on the train.",
  "evidence": "Visible spray-painted graffiti on the train's exterior; person is actively painting it."
}
```
- **D** (none / alert, 4.5 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a person on the platform near a parked train with no obstruction, damage, or right-of-way incident visible; the scene is calm with no vehicle movement or emergency activity.",
  "evidence_frames": "middle",
  "object": "person on platform",
  "still_present": true
}
```
- **E** (trained / current, 4.4 s): `NONE` ```json
{
  "category": "NONE",
  "object": "Person on platform",
  "where": "platform",
  "still_present": true,
  "summary": "A person in dark clothing walks along the platform past a stationary red train, then pauses and looks toward the tracks."
}
```
- **F** (trained / structured_plus, 4.7 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "confidence": 0.95,
  "object": "vivid graffiti on train body",
  "where": "track",
  "still_present": true,
  "summary": "A person applies bright graffiti to the side of a stationary red train on the platform, then walks away; the painted markings remain visible on the train.",
  "evidence": "Colorful spray-painted lettering on the train's exterior persists through the clip."
}
```
- **G** (clearway / current, 4.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "Graffiti on train car",
  "where": "pavement",
  "still_present": true,
  "summary": "A person applies colorful graffiti to the side of a stationary red train car on the platform, then steps back and walks away; the graffiti remains visible on the train."
}
```
- **H** (clearway / structured_plus, 4.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "confidence": 0.95,
  "object": "graffiti on train car",
  "where": "track",
  "still_present": true,
  "summary": "A person applies colorful graffiti to the side of a stationary red train car on the platform, then walks away; the graffiti remains visible on the train at the end.",
  "evidence": "Visible spray-painted graffiti on the train's exterior; person is actively painting it."
}
```
- **A2** (none / current, 4.5 s): `DAMAGE` ```json
{
  "category": "DAMAGE",
  "object": "graffiti on train",
  "where": "pavement",
  "still_present": true,
  "summary": "A person spray-paints colorful graffiti on the side of a stationary red train at the platform, then walks away; the graffiti remains visible on the train at the end."
}
```

## 24. 20261027T124210265311_cw-0009-school_gate_break_in_night.avi (truth NONE)

the fence's top at night, nobody (the 'wrong seconds' clip)

- **A** (none / current, 7.5 s): `NONE` {"category": "NONE", "object": "metallic fence", "where": "pavement", "still_present": true, "summary": "A metallic fence with pointed tops stands along the pavement at night, remaining stationary and unobstructed throughout the clip."}
- **B** (none / structured, 6.6 s): `NONE` ```json
{
  "category": "NONE",
  "object": "none",
  "where": "none",
  "still_present": true,
  "summary": "The scene shows a dark, empty pavement with a metal fence and no pedestrians, vehicles, or incidents visible."
}
```
- **C** (none / structured_plus, 6.5 s): `NONE` ```json
{
  "category": "NONE",
  "confidence": 0.95,
  "object": "metallic fence with pointed tops",
  "where": "pavement",
  "still_present": true,
  "summary": "A metallic fence with pointed tops remains stationary across the pavement throughout the clip.",
  "evidence": "Fence is visible and unchanged from start to end; no movement, damage, or obstruction is observed."
}
```
- **D** (none / alert, 4.4 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "The clip shows a static green metal fence with no vehicles, people, or obstructions visible; no right-of-way incident is present.",
  "evidence_frames": "middle",
  "object": "green metal fence",
  "still_present": true
}
```
- **E** (trained / current, 4.4 s): `NONE` {"category": "NONE", "object": "none", "where": "pavement", "still_present": true, "summary": "No anomalies detected; the scene shows a quiet, well-lit pavement with no pedestrians, vehicles, or obstructions visible."}
- **F** (trained / structured_plus, 5.5 s): `NONE` ```json
{
  "category": "NONE",
  "confidence": 0.95,
  "object": "metallic fence with pointed tops",
  "where": "pavement",
  "still_present": true,
  "summary": "A continuous metallic fence with pointed tops spans the pavement; no obstruction, damage, or movement is visible.",
  "evidence": "Uniform fence structure, no gaps or debris, no vehicles or people present."
}
```
- **G** (clearway / current, 4.4 s): `NONE` ```json
{
  "category": "NONE",
  "object": "none",
  "where": "pavement",
  "still_present": true,
  "summary": "No obstruction, damage, or incident is visible; the pavement appears clear and unobstructed."
}
```
- **H** (clearway / structured_plus, 5.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "metallic fence with pointed tops",
  "where": "pavement",
  "still_present": true,
  "summary": "A metallic fence with pointed tops is lying across the pavement, blocking passage.",
  "evidence": "Fence spans the pavement, no gaps for vehicles or pedestrians to pass."
}
```
- **A2** (none / current, 4.4 s): `NONE` {"category": "NONE", "object": "metallic fence with pointed tops", "where": "pavement", "still_present": true, "summary": "A metallic fence with pointed tops remains stationary on the pavement throughout the video."}

## 25. 20261027T124211337185_cw-0010-school_gate_break_in_night.avi (truth TAMPERING)

crop: crouched at the lock with cutters, the lock, legs leave

- **A** (none / current, 9.0 s): `TAMPERING` {"category": "TAMPERING", "object": "padlock and chain", "where": "pavement", "still_present": true, "summary": "A person crouches and uses a tool to force open a padlock and chain securing a metal gate, then stands up and walks away."}
- **B** (none / structured, 6.6 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock on gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches beside a metal gate, removes a padlock from the gate's chain, and walks away with the lock."
}
```
- **C** (none / structured_plus, 6.4 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock and chain on gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches and removes a padlock and chain from a metal gate, then stands up and walks away.",
  "evidence": "Padlock and chain are visible on the gate, then absent as the person removes them."
}
```
- **D** (none / alert, 5.7 s): `NONE` ```json
{
  "decision": "discard",
  "category": "NONE",
  "confidence": 0.95,
  "reason": "Frames show a person crouching and standing near a locked metal gate with a chain and padlock, then walking away; no vehicle, person on tracks, obstruction, damage, or tampering is visible.",
  "evidence_frames": "start, middle, end of the clip",
  "object": "person near locked gate",
  "still_present": false
}
```
- **E** (trained / current, 4.9 s): `TAMPERING` {"category": "TAMPERING", "object": "padlock and chain", "where": "pavement", "still_present": true, "summary": "A person crouches and removes a padlock and chain from a metal fence, then stands up and walks away."}
- **F** (trained / structured_plus, 5.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock and chain on gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches and removes a padlock and chain from a metal gate, then stands up and walks away.",
  "evidence": "Padlock and chain are visible on the gate, then absent as the person removes them."
}
```
- **G** (clearway / current, 5.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock and chain",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches and removes a padlock and chain from a metal fence, leaving the lock and chain lying on the pavement."
}
```
- **H** (clearway / structured_plus, 5.4 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock and chain on gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches beside a metal gate, removes a padlock and chain, and walks away leaving the gate unlocked.",
  "evidence": "Padlock and chain are visible on the gate, then removed and carried away by the person."
}
```
- **A2** (none / current, 5.5 s): `TAMPERING` {"category": "TAMPERING", "object": "padlock and chain", "where": "pavement", "still_present": true, "summary": "A person crouches and uses a tool to force open a padlock and chain securing a metal gate, then stands up and walks away."}

## 26. 20261027T124212362072_cw-0011-person_on_railway_tracks.avi (truth PERSON_ON_TRACKS)

crop: red jacket at the edge, tracks, sitting with legs on the track

- **A** (none / current, 8.9 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat walks onto the railway tracks, pauses, then sits down on the rails."
}
```
- **B** (none / structured, 6.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": false,
  "summary": "A person in a red coat walks onto the railway tracks, then stumbles and falls onto the rails before disappearing from view."
}
```
- **C** (none / structured_plus, 5.6 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.98,
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat walks onto the railway tracks, then sits down on the edge of the platform.",
  "evidence": "Person enters frame, steps onto the tracks, and remains seated on the platform edge."
}
```
- **D** (none / alert, 5.6 s): `PERSON_ON_TRACKS` ```json
{
  "decision": "confirm",
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.95,
  "reason": "A person in a red coat is seen walking onto the railway tracks and then sitting on the edge of the platform, clearly occupying the tracks rather than remaining on the platform.",
  "evidence_frames": "middle",
  "object": "person in red coat",
  "still_present": true
}
```
- **E** (trained / current, 4.8 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat walks onto the railway tracks, pauses, then sits down on the rails."
}
```
- **F** (trained / structured_plus, 5.4 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.98,
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat walks onto the railway tracks, pauses, then sits down on the rails.",
  "evidence": "Person crosses the yellow tactile strip and sits on the rails; no train is visible."
}
```
- **G** (clearway / current, 5.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat walks onto the railway tracks, pauses, then sits down on the rails."
}
```
- **H** (clearway / structured_plus, 5.4 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "confidence": 0.98,
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat walks onto the railway tracks, pauses, then sits on the edge of the platform.",
  "evidence": "Person crosses the yellow tactile strip and sits on the platform edge adjacent to the tracks."
}
```
- **A2** (none / current, 5.5 s): `PERSON_ON_TRACKS` ```json
{
  "category": "PERSON_ON_TRACKS",
  "object": "person in red coat",
  "where": "track",
  "still_present": true,
  "summary": "A person in a red coat walks onto the railway tracks, pauses, then sits down on the rails."
}
```

## 27. 20261027T124213501036_cw-0012-escooter_left_across_sidewalk.avi (truth OBSTRUCTION)

crop: scooter lying, pavement empty, rider rides off

- **A** (none / current, 8.9 s): `OBSTRUCTION` {"category": "OBSTRUCTION", "object": "electric scooter", "where": "pavement", "still_present": false, "summary": "An electric scooter lies on its side across the pavement, blocking the walkway, before a person rides another scooter past it and the obstruction is no longer visible."}
- **B** (none / structured, 6.6 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on its side on the pavement, blocking the walkway, while a rider walks away and another rider later approaches and stops nearby."
}
```
- **C** (none / structured_plus, 5.6 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "electric scooter lying on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on the pavement, blocking the walkway and remaining stationary throughout the clip.",
  "evidence": "Scooter is down on the pavement, not on a track or lane, and does not move or disappear."
}
```
- **D** (none / alert, 5.6 s): `OBSTRUCTION` ```json
{
  "decision": "confirm",
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "reason": "A white electric scooter lies on its side across the tiled pavement, blocking the pedestrian path and remaining stationary throughout the clip.",
  "evidence_frames": "middle",
  "object": "white electric scooter",
  "still_present": true
}
```
- **E** (trained / current, 4.8 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on its side across the pavement, blocking the walkway, while a rider walks past and another scooter passes in the adjacent lane."
}
```
- **F** (trained / structured_plus, 4.4 s): `STALLED_VEHICLE` ```json
{
  "category": "STALLED_VEHICLE",
  "confidence": 0.95,
  "object": "electric scooter",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on its side on the pavement and remains there throughout the clip.",
  "evidence": "The scooter is clearly visible on the pavement, stationary and not moving, with no signs of being towed or repaired."
}
```
- **G** (clearway / current, 5.4 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "object": "electric scooter",
  "where": "pavement",
  "still_present": false,
  "summary": "An electric scooter lies on its side across the pavement, blocking the walkway, then is pushed upright and ridden away."
}
```
- **H** (clearway / structured_plus, 4.5 s): `OBSTRUCTION` ```json
{
  "category": "OBSTRUCTION",
  "confidence": 0.95,
  "object": "electric scooter lying on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "An electric scooter lies on the pavement, blocking the walkway and remaining stationary throughout the clip.",
  "evidence": "Scooter is visible on the pavement, not on the roadway, and does not move or disappear."
}
```
- **A2** (none / current, 5.4 s): `OBSTRUCTION` {"category": "OBSTRUCTION", "object": "electric scooter", "where": "pavement", "still_present": false, "summary": "An electric scooter lies on its side across the pavement, blocking the walkway, before a rider returns and parks it upright."}

## 28. 20261027T124225065659_cw-0013-school_gate_break_in_night.avi (truth TAMPERING)

crouched at the gate with the tool, lock and chain hang, leaves

- **A** (none / current, 6.6 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock and chain",
  "where": "pavement",
  "still_present": false,
  "summary": "A person uses a tool to break the padlock and chain securing the gate, then removes the lock and chain from the gate."
}
```
- **B** (none / structured, 6.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock on gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person uses a tool to force open a padlocked metal gate at night, then walks away with the tool while the padlock remains attached."
}
```
- **C** (none / structured_plus, 5.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock and chain on gate",
  "where": "pavement",
  "still_present": true,
  "summary": "A person crouches and removes a padlock and chain from a metal gate, leaving the gate unlocked.",
  "evidence": "Padlock and chain are visible on the gate, then absent as the person removes them."
}
```
- **D** (none / alert, 4.5 s): `TAMPERING` ```json
{
  "decision": "confirm",
  "category": "TAMPERING",
  "confidence": 0.95,
  "reason": "A person in dark clothing crouches at the gate, uses a tool to force the padlock and chain, and then stands up holding the tool as the lock is compromised.",
  "evidence_frames": "middle",
  "object": "person forcing padlock",
  "still_present": true
}
```
- **E** (trained / current, 4.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock and chain",
  "where": "gate",
  "still_present": false,
  "summary": "A person removes a padlock and chain from a metal gate, leaving the gate unlocked."
}
```
- **F** (trained / structured_plus, 4.4 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock and chain on gate",
  "where": "gate",
  "still_present": true,
  "summary": "A person crouches beside a metal gate at night, removes a padlock and chain, and leaves the gate unlocked.",
  "evidence": "Padlock and chain are visible on the gate, then removed by a person, leaving the gate unlocked."
}
```
- **G** (clearway / current, 4.5 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock and chain",
  "where": "pavement",
  "still_present": true,
  "summary": "A person removes a padlock and chain from a metal gate, leaving the lock and chain still attached to the gate at the end of the clip."
}
```
- **H** (clearway / structured_plus, 4.4 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "confidence": 0.95,
  "object": "padlock and chain on gate",
  "where": "gate",
  "still_present": true,
  "summary": "A person crouches beside a metal gate at night, removes a padlock and chain, and leaves the gate unlocked.",
  "evidence": "Padlock and chain are visible on the gate, then removed by a person, leaving the gate unlocked."
}
```
- **A2** (none / current, 3.1 s): `TAMPERING` ```json
{
  "category": "TAMPERING",
  "object": "padlock and chain",
  "where": "pavement",
  "still_present": false,
  "summary": "A person uses a tool to break the padlock and chain securing the gate, then removes the lock and chain from the gate."
}
```

