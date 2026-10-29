# Every answer

## 1. mumbai02-real-001 (real, lens x5.82, at 42.7 s)

Truth: NONE. a yellow-black taxi waiting in the foreground queue at the junction for 18 s, motorbikes beside it

Answer: **UNPARSED**

```
Transfer Assets: An error was returned from Hafnia VLM: HTTP 403 Forbidden
```

## 2. mumbai02-real-002 (real, lens x6.71, at 43.4 s)

Truth: NONE. people standing at the far pavement corner under the building for 16 s (x6.7 crop)

Answer: **OBSTRUCTION**

```
{"category": "OBSTRUCTION", "object": "fallen tree trunk", "where": "lane", "still_present": true, "summary": "A large tree trunk falls across the roadway, blocking the lane and forcing vehicles to stop or maneuver around it."}
```

## 3. duesseldorf-real-001 (real, lens x4.73, at 29.9 s)

Truth: NONE. a black estate car waiting at the crossing for 18 s while pedestrians cross in front of it

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "dark station wagon",
  "where": "lane",
  "still_present": true,
  "summary": "A dark station wagon is stopped in the lane with brake lights illuminated, blocking traffic; vehicles behind slow and stop, and pedestrians cross the road around it."
}
```
```

## 4. mumbai02-loops-001 (loops, lens x2.76, at 13.4 s)

Truth: NONE. the far pavement corner: a stall, a parked van, people

Answer: **COLLISION**

```
```json
{
  "category": "COLLISION",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan collides with a parked vehicle at the curb, then stalls in the lane and blocks traffic."
}
```
```

## 5. mumbai02-loops-002 (loops, lens x3.34, at 14.0 s)

Truth: NONE. the far corner, parked vehicles and people on the pavement

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan stalls in the middle of the lane, blocking traffic and forcing vehicles to merge around it."
}
```
```

## 6. mumbai02-loops-004 (loops, lens x2.91, at 16.3 s)

Truth: NONE. motorbike riders paused in the middle of the junction

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "motorcyclists and cars",
  "where": "lane",
  "still_present": true,
  "summary": "Motorcyclists and cars move through the intersection in an orderly flow, with no collisions, obstructions, or damage observed."
}
```
```

## 7. mumbai02-loops-006 (loops, lens x4.1, at 17.6 s)

Truth: NONE. the rear of the queued taxi

Answer: **STALLED_VEHICLE**

```
{"category": "STALLED_VEHICLE", "object": "yellow taxi", "where": "lane", "still_present": true, "summary": "A yellow taxi is stopped in the middle of the lane, blocking traffic, while motorcycles and other vehicles maneuver around it."}
```

## 8. mumbai02-loops-008 (loops, lens x2.54, at 27.3 s)

Truth: NONE. the far pavement: pedestrians crossing, a parked white car, a lorry

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan stalls in the middle of the lane, blocking traffic and forcing vehicles to maneuver around it."
}
```
```

## 9. mumbai02-loops-010 (loops, direct x1.0, at 27.8 s)

Truth: NONE. the far corner with stalls and pedestrians, the whole frame shown

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white van",
  "where": "lane",
  "still_present": true,
  "summary": "A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it."
}
```
```

## 10. mumbai02-loops-012 (loops, lens x2.82, at 28.2 s)

Truth: NONE. a white car at the far right kerb by a building

Answer: **OBSTRUCTION**

```
```json
{
  "category": "OBSTRUCTION",
  "object": "white SUV parked on pavement",
  "where": "pavement",
  "still_present": true,
  "summary": "A white SUV is parked on the pavement, blocking the lane and forcing passing vehicles to slow and maneuver around it."
}
```
```

## 11. mumbai02-loops-014 (loops, direct x2.22, at 29.4 s)

Truth: NONE. a black car and a motorbike moving through the junction by the taxi queue

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white van",
  "where": "lane",
  "still_present": true,
  "summary": "A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it."
}
```
```

## 12. mumbai02-loops-016 (loops, direct x2.37, at 29.5 s)

Truth: NONE. a queued taxi, the whole frame shown

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "motorcyclist",
  "where": "pavement",
  "still_present": true,
  "summary": "A motorcyclist rides along the pavement at the intersection, weaving between parked cars and pedestrians while traffic moves through the junction."
}
```
```

## 13. mumbai02-loops-018 (loops, lens x3.34, at 30.1 s)

Truth: NONE. a blue cart or cover at the bottom right by the railing, static street furniture

Answer: **OBSTRUCTION**

```
{"category": "OBSTRUCTION", "object": "blue tarpaulin on pavement", "where": "pavement", "still_present": true, "summary": "A blue tarpaulin lies across the pavement, partially blocking the pedestrian path and remaining in place throughout the video."}
```

## 14. mumbai02-loops-020 (loops, direct x1.13, at 30.3 s)

Truth: NONE. the right half of the junction, vehicles passing the traffic light

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white van",
  "where": "lane",
  "still_present": true,
  "summary": "A white van stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it."
}
```
```

## 15. mumbai02-loops-022 (loops, lens x3.41, at 33.5 s)

Truth: NONE. the far corner: a parked goods vehicle and pedestrians

Answer: **OBSTRUCTION**

```
```json
{
  "category": "OBSTRUCTION",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan is stopped in the middle of the lane, blocking traffic and forcing vehicles and pedestrians to detour around it."
}
```
```

## 16. mumbai02-loops-024 (loops, direct x2.17, at 33.7 s)

Truth: NONE. the road by the queue, cars passing, the whole frame shown

Answer: **COLLISION**

```
```json
{
  "category": "COLLISION",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan collides with a black SUV at the intersection, then stalls in the lane and remains there as traffic around it slows and stops."
}
```
```

## 17. mumbai02-loops-025 (loops, lens x2.65, at 33.7 s)

Truth: NONE. a queued taxi waiting

Answer: **STALLED_VEHICLE**

```
{"category": "STALLED_VEHICLE", "object": "yellow taxi", "where": "lane", "still_present": true, "summary": "A yellow taxi is stopped in the middle of the lane, blocking traffic, while other vehicles and motorcycles maneuver around it."}
```

## 18. mumbai02-loops-027 (loops, direct x1.26, at 38.1 s)

Truth: NONE. the queue moving off, taxis, motorbikes and a white car

Answer: **COLLISION**

```
```json
{
  "category": "COLLISION",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan collides with a black hatchback in the middle of the intersection, then stalls and blocks the lane."
}
```
```

## 19. mumbai02-loops-029 (loops, direct x2.1, at 46.5 s)

Truth: NONE. the pavement corner with a lorry and people, the whole frame shown

Answer: **COLLISION**

```
```json
{
  "category": "COLLISION",
  "object": "white hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A white hatchback enters the intersection and collides with a black sedan, causing the hatchback to spin and stall in the lane."
}
```
```

## 20. mumbai02-loops-031 (loops, lens x4.87, at 47.3 s)

Truth: NONE. a dark car at the far right kerb, a white car passing close beside it

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan is stopped in the middle of the lane, blocking traffic and causing vehicles behind to slow and stop."
}
```
```

## 21. mumbai02-loops-033 (loops, direct x2.29, at 50.9 s)

Truth: NONE. motorbike riders waiting in the junction, a black car passing

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white hatchback",
  "where": "lane",
  "still_present": true,
  "summary": "A white hatchback stalls in the middle of the intersection, blocking the lane and forcing other vehicles to maneuver around it."
}
```
```

## 22. mumbai02-loops-035 (loops, direct x1.0, at 134.7 s)

Truth: NONE. the far side of the junction: two red buses and taxis crossing, the whole frame

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan is stopped in the middle of the intersection, blocking the lane and forcing surrounding vehicles and motorcycles to maneuver around it."
}
```
```

## 23. mumbai02-loops-037 (loops, lens x3.47, at 135.4 s)

Truth: NONE. a motorbike with riders stopped at the bottom edge of the frame for 19 s, cut off

Answer: **COLLISION**

```
{"category": "COLLISION", "object": "motorcycle", "where": "lane", "still_present": false, "summary": "A motorcycle collides with a parked vehicle in the lane, producing visible sparks and smoke, and the rider is thrown from the bike."}
```

## 24. duesseldorf-loops-001 (loops, lens x3.73, at 12.0 s)

Truth: NONE. the rear of a car waiting at the junction, people on the pavement behind

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "dark blue station wagon",
  "where": "lane",
  "still_present": true,
  "summary": "A dark blue station wagon is stopped in the lane with brake lights illuminated, blocking traffic; a blue sedan pulls up behind it and stops, while pedestrians wait on the pavement."
}
```
```

## 25. duesseldorf-loops-003 (loops, direct x1.42, at 15.0 s)

Truth: NONE. the far building's roofline after an exposure change, the whole frame shown

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "blue sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A blue sedan is stopped in the middle of the intersection, blocking the lane and causing other vehicles to queue behind it."
}
```
```

## 26. duesseldorf-loops-005 (loops, lens x3.28, at 15.0 s)

Truth: NONE. the far building's facade, nothing happening

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "white sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A white sedan is stopped in the middle of the lane, blocking traffic, while other vehicles slow and maneuver around it."
}
```
```

## 27. duesseldorf-loops-007 (loops, direct x1.23, at 18.3 s)

Truth: NONE. cars queued at the junction on the far side, the whole frame shown

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "blue sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A blue sedan stalls in the middle of the intersection, blocking the lane and forcing other vehicles to stop and wait."
}
```
```

## 28. duesseldorf-loops-009 (loops, lens x3.47, at 18.4 s)

Truth: NONE. a traffic light and the building corner

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "pedestrians and vehicles",
  "where": "lane",
  "still_present": true,
  "summary": "Pedestrians cross the street while vehicles wait at a red light, with no collisions or obstructions visible."
}
```
```

## 29. duesseldorf-loops-010 (loops, lens x2.54, at 18.4 s)

Truth: NONE. the crossing by the kerb, queued cars behind, a pedestrian

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "dark blue sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A dark blue sedan is stopped in the lane with brake lights illuminated, blocking traffic; pedestrians wait on the pavement as the vehicle remains stationary."
}
```
```

## 30. duesseldorf-loops-012 (loops, direct x2.13, at 19.2 s)

Truth: NONE. the building's first-floor windows and the traffic light, the whole frame shown

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "blue sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A blue sedan stalls in the middle of the lane, blocking traffic and forcing other vehicles to stop and wait."
}
```
```

## 31. duesseldorf-loops-014 (loops, direct x2.29, at 20.3 s)

Truth: NONE. cars queued on the far side by the shop fronts, the whole frame shown

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "blue sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A blue sedan stalls in the middle of the lane, blocking traffic and forcing other vehicles to stop and wait."
}
```
```

## 32. duesseldorf-loops-016 (loops, lens x3.82, at 26.1 s)

Truth: NONE. the red cabriolet's front wheel while it waits at the crossing

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "silver sedan",
  "where": "lane",
  "still_present": true,
  "summary": "A silver sedan is stopped in the middle of the lane, partially blocking traffic, while a red car and a pedestrian pass by."
}
```
```

## 33. duesseldorf-loops-018 (loops, lens x3.08, at 26.5 s)

Truth: NONE. the far facade, queued cars below

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "pedestrians and vehicles",
  "where": "pavement",
  "still_present": true,
  "summary": "Pedestrians cross the pavement while vehicles remain stopped or move slowly in the adjacent lane, with no collision or obstruction observed."
}
```
```

## 34. duesseldorf-loops-020 (loops, lens x2.67, at 26.6 s)

Truth: NONE. the crossing in front of the kerb, pedestrians' legs passing over the tram rails

Answer: **OBSTRUCTION**

```
```json
{
  "category": "OBSTRUCTION",
  "object": "fallen tree trunk",
  "where": "lane",
  "still_present": true,
  "summary": "A large fallen tree trunk lies across the roadway, blocking the lane and forcing vehicles to stop and pedestrians to detour around it."
}
```
```

## 35. duesseldorf-loops-022 (loops, direct x1.14, at 26.7 s)

Truth: NONE. the far building's roof, the whole frame shown

Answer: **STALLED_VEHICLE**

```
```json
{
  "category": "STALLED_VEHICLE",
  "object": "black station wagon",
  "where": "lane",
  "still_present": true,
  "summary": "A black station wagon is stopped in the middle of the lane, blocking traffic and forcing vehicles to queue behind it."
}
```
```

## 36. duesseldorf-loops-024 (loops, lens x2.76, at 26.7 s)

Truth: NONE. the far shop fronts, pedestrians passing

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "pedestrians and vehicles",
  "where": "pavement",
  "still_present": true,
  "summary": "Pedestrians cross the street at the marked crosswalk while vehicles remain stopped at the red light, maintaining orderly traffic flow."
}
```
```

## 37. duesseldorf-loops-026 (loops, direct x1.0, at 26.7 s)

Truth: NONE. the red cabriolet waiting while people cross the tram rails in front, the whole frame

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "Pedestrians and vehicles",
  "where": "pavement",
  "still_present": true,
  "summary": "Pedestrians cross the zebra crossing while vehicles wait at the red light, with no collisions or obstructions observed."
}
```
```

## 38. duesseldorf-loops-028 (loops, lens x3.14, at 27.3 s)

Truth: NONE. the red cabriolet's front and the tram rails, people crossing in front

Answer: **OBSTRUCTION**

```
```json
{
  "category": "OBSTRUCTION",
  "object": "fallen tree trunk",
  "where": "lane",
  "still_present": true,
  "summary": "A large fallen tree trunk lies across the roadway, blocking the lane and forcing vehicles to slow and maneuver around it while pedestrians cross nearby."
}
```
```

## 39. duesseldorf-loops-030 (loops, direct x1.1, at 29.7 s)

Truth: NONE. the left edge: a kiosk, a woman walks past in the foreground, the whole frame shown

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "pedestrians and vehicles",
  "where": "pavement",
  "still_present": true,
  "summary": "Pedestrians cross the zebra crossing while vehicles wait at the red light, with no collisions or obstructions."
}
```
```

## 40. duesseldorf-loops-032 (loops, direct x2.11, at 29.7 s)

Truth: NONE. the building's windows and traffic lights, the whole frame shown

Answer: **NONE**

```
```json
{
  "category": "NONE",
  "object": "Pedestrians and vehicles",
  "where": "pavement",
  "still_present": true,
  "summary": "Pedestrians cross the zebra crossing while vehicles wait at the red light, maintaining orderly traffic flow."
}
```
```
