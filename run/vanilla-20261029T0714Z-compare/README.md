# The plain way against Clearway on the same minutes (2026-10-29)

`scripts/vanilla_poll.py`, 07:14-07:20 UTC, 66 requests, 66 completed (today's count 88 before, 168 after, Clearway's
live run asking beside it). The plain way to use Hafnia on a set of cameras: the organizers' example question
("Describe what happens in this video.", a 30 s clip ending 5 s ago, as the kit's `ask_hafnia.py`) asked about every
camera once a minute, which is what a recurring XProtect rule with a Hafnia webhook does. Eleven cameras, six polls
each. Clearway ran beside it on the same eleven cameras for ten minutes
(`run/clearway-live-20261029T071314Z-compare`: started 07:13, models loaded and cameras streaming by 07:15:45, so
the two overlap in the poller's last four minutes; the loops repeat every 8-17 s, so every minute holds the same
scenes). The comparison is the last section; the plain way's answers are read one by one first.

## The plain way's 66 answers, read one by one (`answers.md`)

- **The staged incidents, 36 answers on six cameras: the incident is in the description 24 times.** The stalled
  pickup with smoke 6 of 6, the graffiti 6 of 6, the person at the gate with a tool 6 of 6 (once with the gate
  "swinging open", which does not happen), the bin tipped over 5 of 6 (the sixth: "the bin remains upright,
  unsuccessful attempt"). **The person on the tracks: 0 of 6.** Six times the same words: "sits on the edge of the
  platform facing the tracks, stands up and walks away from the tracks, calm, orderly movement with no signs of
  distress or danger". In the clip the person steps down and walks along the rails; at 832 px wide they are a few
  dozen pixels, and the description never puts them on the track. The scooter left across the pavement: 1 of 6; the
  other five describe the rider mounting and riding away.
- **Every incident is reported again every minute.** The same truck, the same graffiti, six times each in six
  minutes; nothing says it is the same event. Several answers notice the loop themselves ("the scene repeats").
- **The five street cameras, 30 answers: 24 ordinary scenes described as ordinary.** The crowd, the fogged
  highway, the red SUV at a red light (never called stalled: the whole frame, a descriptive question), the
  roadworks in the bus lane ("flows smoothly without incidents"). Nothing invented in 24 answers.
- **The `vandalism` camera, 6 of 6: "throws a small object toward a window, the glass shatters".** That is DAMAGE by
  Clearway's own definition (glass broken), and Clearway has never asked about it: a thrown object and a crack are
  not a change that stays, so the detector at the real-camera setting reports nothing there
  (`docs/INVESTIGATION-2026-10-27.md`, the camera table). The plain way reports it every minute. This is the one
  thing in the comparison the plain way finds and Clearway does not.
- **Answers are paragraphs**, 359 characters on average, 6-21 s each; an operator reads 66 of them for six minutes
  of eleven cameras, with no category, no verdict, no link between them.

## The arithmetic of asking on a timer

Once a minute with 30 s clips: 60 requests per camera-hour, half of each camera's time looked at, the day's 500
requests gone in 45 minutes for eleven cameras. Every five minutes: 12 per camera-hour, a tenth of the time looked
at, the allowance gone in 3.8 hours; an incident shorter than four and a half minutes can fall between two clips.
Every fifteen minutes: 4 per camera-hour, a thirtieth of the time, 11 hours of allowance, and anything under
fourteen and a half minutes can be missed outright. The interval trades requests against blindness, and no interval
removes the reading.

## The comparison

Clearway's reference on these cameras is the 20-minute run of 2026-10-27 (`run/clearway-live-20261027T124112Z-clean`,
the same eleven loops, nothing else running) and the three-hour shift of 2026-10-26 for the rate; today's run beside
the poller is the third column and is degraded, see below.

| | The plain way, once a minute (this run, 6 min) | Clearway, 2026-10-27 (20 min) | Clearway today, beside the poller (10 min) |
|---|---|---|---|
| Requests | 66 | 14 | 15 (the cap; 5 of 20 questions went unasked) |
| Requests per camera-hour | 60 | 3.8 in a 20-minute run dominated by the start-up burst; **1 over the three-hour shift of 10-26** (33 requests) | 8.2 |
| Share of each camera's time looked at | 50 % (30 s of every 60) | 100 % by the detector; the model sees only what stayed changed | the same, where frames arrived |
| What the operator gets | 66 paragraphs, 359 characters each, no category, each incident reported six times | 7 incidents with category, owner, alarm and the clip judged; 331 recurrences merged at no request | 6 incident cards |
| Staged incidents found | truck, graffiti, gate 6 of 6; bin 5 of 6; **scooter 1 of 6; person on the tracks 0 of 6** | 6 of 6 cameras, the tracks and the scooter through the magnified clip; 12 of 14 categories as expected | 4 of 6 (truck, bin, gate, graffiti); the tracks camera delivered no frames |
| Invented incidents on the four ordinary street cameras | 0 of 24 | 0 | 0 |
| The smashed window (`vandalism`) | reported 6 of 6 | never asked: not a change that stays | never asked |
| The day's 500 requests last | 45 minutes | the whole day with room to spare | |

**Today's Clearway run is not the reference.** Running the two side by side on one machine was a design mistake:
the machine sat at 100 % CPU with the poller's 66 clip exports and the board recorder beside eleven live streams,
the service got 4-47 % of the CPU against 54 % in the 10-27 run, frames arrived at 0-2.5 per second per camera
against 7.5-8.1, three cameras delivered none or almost none (the tracks 0.0, the condensation street 0.0, the
vandalism alley 0.2), and the board recorder managed 23 frames in ten minutes (a 6 s video, unusable). What it did
produce was right as far as it went: 6 cards on the four cameras it saw, 12 of 15 answers as the stand-in
expected, 6 of 6 alarms in XProtect in the expected state. The loops being identical minute to minute, the plain
way's six minutes and Clearway's twenty of 10-27 are the same scenes, which is what the video compares.

**What the comparison says, in order of weight:** (1) the plain way's cost grows with the interval and the camera
count, Clearway's with incidents: 60 against 1 request per camera-hour here, and no interval removes the reading of
a paragraph per request; (2) the plain way looks at half the time at best, the detector at all of it; (3) a full
frame described in words never put the person on the tracks, six times out of six, and the scooter once in six,
while the magnified clip names both; (4) the plain way's descriptive question invented nothing on the ordinary
street scenes, and it reports the smashed window that Clearway's change detector never sees because nothing stays
changed: a thrown object is an event, not a change, and Clearway is built for changes.

<!-- tables: written by vanilla_poll.py score; the text above is kept -->

66 requests sent (66 completed, 0 failed): 11 cameras x 6 polls every 60 s for 6 min, 30 s clips, the prompt 'Describe what happens in this video.'. Answers took 6.2-20.8 s (mean 12.2), 359 characters on average.

**At this interval:** 60 requests per camera-hour; the clips cover 50 % of each camera's time; the day's 500 requests last 45.5 minutes for 11 cameras.

## Per camera

| Camera | Sent | Completed | Answers naming an incident | Words found |
|---|---|---|---|---|
| vehicle_breakdown_traffic_queue | 6 | 6 | 5 | collision 1, stalled vehicle 5 |
| bin_pushed_over_onto_sidewalk | 6 | 6 | 1 | obstruction 1 |
| escooter_left_across_sidewalk | 6 | 6 | 1 | obstruction 1 |
| school_gate_break_in_night | 6 | 6 | 5 | tampering 5 |
| person_on_railway_tracks | 6 | 6 | 0 | - |
| graffiti_on_standing_train | 6 | 6 | 6 | damage 6 |
| busy_street | 6 | 6 | 0 | - |
| highway_traffic_overcast_weather | 6 | 6 | 0 | - |
| city_street_7_condensation_inside_housing | 6 | 6 | 0 | - |
| vandalism | 6 | 6 | 3 | collision 3, damage 2 |
| traffic_flows_in_the_open_lanes | 6 | 6 | 0 | - |

## Every answer

| Poll | Camera | Span (UTC) | s | Words | Answer |
|---|---|---|---|---|---|
| 1 | vehicle_breakdown_traffic_queue | 07:13:26-07:13:56 | 14.9 | stalled vehicle | A silver pickup truck is stopped in the middle of the intersection with its brake lights illuminated. A person exits the driver's side and stands on the pavement, while another person remains inside the vehicle. The truck's exhaust emits a visible plume of whi |
| 1 | bin_pushed_over_onto_sidewalk | 07:13:26-07:13:56 | 14.8 | - | A person in a dark hoodie and black pants attempts to tip a large green wheeled trash bin on the sidewalk. The bin tips over and rolls onto the pavement, where the person walks around it. The scene repeats: the bin is uprighted, then tipped again and rolls ove |
| 1 | escooter_left_across_sidewalk | 07:13:28-07:13:58 | 12.6 | - | A person in dark clothing approaches a white electric scooter parked on the sidewalk, steps onto it, and rides away. The rider briefly stops, dismounts, and walks a few steps before mounting again and riding off. The scene takes place on a clear, dry day with  |
| 1 | school_gate_break_in_night | 07:13:41-07:14:11 | 13.2 | tampering | A person in dark clothing approaches a locked metal gate at night, crouches to inspect the lock, and uses a tool to pick or manipulate it. After a brief pause, the gate swings open, and the individual walks through and away from the camera. The scene is illumi |
| 1 | person_on_railway_tracks | 07:13:41-07:14:11 | 13.1 | - | A person in a red jacket and black pants sits on the edge of the platform near the yellow tactile paving, then stands and walks along the platform. The individual pauses briefly, sits again, and resumes walking. The scene shows a quiet station with clear dayli |
| 1 | graffiti_on_standing_train | 07:13:43-07:14:13 | 11.1 | damage | A person in dark clothing is spray-painting graffiti on the side of a stationary red train at a platform. The individual moves along the train's length, applying paint to the exterior while the train remains stopped. The platform is clear of other passengers,  |
| 1 | busy_street | 07:13:54-07:14:24 | 20.8 | - | The scene shows a busy urban street at night with a dense crowd of pedestrians filling the sidewalks and roadway. People are walking in both directions, some pausing or looking around, while vehicles move slowly through the congested traffic. Streetlights and  |
| 1 | highway_traffic_overcast_weather | 07:13:54-07:14:24 | 20.7 | - | A single vehicle travels steadily along a wet, multi-lane highway under overcast, rainy conditions. The pavement is visibly wet and reflective, with lane markings faintly visible through the rain. The vehicle maintains a consistent speed and lane position, wit |
| 1 | city_street_7_condensation_inside_housing | 07:13:55-07:14:25 | 19.6 | - | The scene shows a clear, dry urban intersection with vehicles stopped at a red light. A red SUV is positioned in the rightmost lane, waiting at the signal. Lane markings are visible, and the pavement appears smooth and well maintained. No pedestrians or cyclis |
| 1 | vandalism | 07:14:15-07:14:45 | 10.0 | collision | A man in black clothing walks along a paved alleyway beside a brick building, then throws a small object toward a window. The projectile strikes the glass, causing it to shatter into visible fragments. The man watches the impact and then walks away. |
| 1 | traffic_flows_in_the_open_lanes | 07:14:15-07:14:45 | 9.9 | - | The scene shows a multi-lane urban roadway with a closed leftmost lane due to construction. A red-and-white mini excavator is parked on the left side of the closed lane, surrounded by orange traffic cones and temporary barriers. Workers in high-visibility vest |
| 2 | vehicle_breakdown_traffic_queue | 07:14:26-07:14:56 | 18.3 | stalled vehicle | A silver pickup truck is stopped in the middle of the roadway with its driver-side door open and a person standing outside. The vehicle emits visible exhaust smoke and remains stationary despite active traffic flow. Pedestrians cross the street at the marked c |
| 2 | bin_pushed_over_onto_sidewalk | 07:14:30-07:15:00 | 14.0 | obstruction | A person in dark clothing attempts to lift a large green wheeled trash bin on a city sidewalk. The bin tips over and falls onto its side, blocking the walkway. The individual steps back, walks away, and later returns to try lifting it again, but the bin remain |
| 2 | escooter_left_across_sidewalk | 07:14:31-07:15:01 | 12.8 | obstruction | A person in dark clothing walks along a paved sidewalk toward a parked electric scooter, then rides it briefly before stopping and dismounting. The scooter is left lying on its side on the pavement. Traffic flows steadily in the adjacent roadway, with parked c |
| 2 | school_gate_break_in_night | 07:14:44-07:15:14 | 12.1 | - | A person in dark clothing crouches at a locked metal gate at night, using a tool to pry or manipulate the latch. After a brief pause, they stand, turn toward the camera, and walk away, leaving the gate still locked. The scene is illuminated by a streetlamp, ca |
| 2 | person_on_railway_tracks | 07:14:44-07:15:14 | 11.9 | - | A person in a red jacket and black pants walks along a train platform, then crouches and sits on the edge of the platform near the tracks. The individual remains seated for several seconds, then stands up and walks away. The platform is empty otherwise, with n |
| 2 | graffiti_on_standing_train | 07:14:46-07:15:16 | 10.5 | damage | A person in dark clothing stands on the platform beside a red train, repeatedly spraying colorful graffiti onto the train's side. The individual pauses, steps back, and resumes spraying, while another person remains visible on the opposite platform. The train  |
| 2 | busy_street | 07:14:56-07:15:26 | 19.9 | - | A dense crowd of pedestrians fills the street at night, moving slowly in both directions. People are dressed in winter coats and hats, and some hold phones or bags. Vehicles, including a red double-decker bus, navigate cautiously through the narrow gaps betwee |
| 2 | highway_traffic_overcast_weather | 07:14:57-07:15:27 | 19.6 | - | The scene shows a multi-lane highway under clear daytime conditions with no visible precipitation. The pavement appears dry and well maintained, with crisp lane markings and no puddles or wet reflections. Traffic is sparse, with vehicles moving steadily in bot |
| 2 | city_street_7_condensation_inside_housing | 07:14:58-07:15:28 | 17.8 | - | The scene shows a clear, sunny day at a city intersection with dry pavement and no visible weather-related hazards. Traffic is orderly: vehicles in the left lane move straight through the intersection, while a red SUV in the right lane waits at a red light. La |
| 2 | vandalism | 07:15:16-07:15:46 | 8.8 | collision, damage | A man in black clothing walks along a paved alleyway beside a brick building, repeatedly throwing a small object toward a window with a visible cracked pane. The object strikes the glass, causing additional cracks and a noticeable impact. The man pauses after  |
| 2 | traffic_flows_in_the_open_lanes | 07:15:16-07:15:46 | 8.7 | - | The scene shows a multi-lane urban roadway with a marked bus lane on the left and a construction zone on the far left. A red-and-white mini excavator is parked in the bus lane, surrounded by orange traffic cones and temporary barriers, with workers in high-vis |
| 3 | vehicle_breakdown_traffic_queue | 07:15:26-07:15:56 | 9.1 | - | A silver pickup truck is stopped in the middle of the intersection with its brake lights illuminated. A person exits the driver's side and stands on the pavement, while another person exits the passenger side and walks toward the curb. The truck remains statio |
| 3 | bin_pushed_over_onto_sidewalk | 07:15:26-07:15:56 | 9.0 | - | A person in dark clothing and white sneakers attempts to tip a large green wheeled trash bin on a tiled sidewalk. The bin tips over and rolls onto the pavement, where the person walks away. The scene repeats: the bin is upright, the person tips it again, it fa |
| 3 | escooter_left_across_sidewalk | 07:15:26-07:15:56 | 8.9 | - | A person in dark clothing and white sneakers is seen on a sidewalk next to a parked electric scooter. The rider dismounts, walks a few steps, then returns to the scooter, mounts it, and rides away down the bike lane. The pavement is wet, and a silver car passe |
| 3 | school_gate_break_in_night | 07:15:35-07:16:05 | 9.9 | tampering | A person in dark clothing approaches a locked metal gate at night, crouches to inspect the padlock, and attempts to pick or manipulate it with a tool. The individual pauses, looks around cautiously, and resumes working on the lock before the clip ends. |
| 3 | person_on_railway_tracks | 07:15:35-07:16:05 | 9.9 | - | A person in a red jacket and black pants walks along a train platform, stops at the yellow tactile paving, and sits on the edge of the platform facing the tracks. After a brief pause, they stand up and walk away from the tracks, continuing along the platform.  |
| 3 | graffiti_on_standing_train | 07:15:35-07:16:05 | 9.8 | damage | A person in dark clothing walks along the platform, stops near the train, and begins spray-painting graffiti on the side of the stationary red train. The individual applies colorful markings to the train's surface while standing close to the tracks, then steps |
| 3 | busy_street | 07:15:45-07:16:15 | 19.2 | - | The scene shows a busy urban street at night with a dense crowd of pedestrians filling the roadway. People are walking in both directions, some pausing or looking around, while vehicles move slowly through the congestion. Streetlights and illuminated storefron |
| 3 | highway_traffic_overcast_weather | 07:15:45-07:16:15 | 19.1 | - | The scene shows a multi-lane highway under clear daytime conditions with a wet, reflective pavement. A black sedan travels steadily in the rightmost lane, maintaining its lane and speed. A white SUV enters from the right, merges into the middle lane, and conti |
| 3 | city_street_7_condensation_inside_housing | 07:15:45-07:16:15 | 19.0 | - | The scene shows a clear, dry urban intersection with vehicles stopped at a red light. A red SUV is positioned in the rightmost lane, waiting at the signal. Lane markings are visible, and the pavement appears smooth and well maintained. No pedestrians or cyclis |
| 3 | vandalism | 07:16:04-07:16:34 | 6.3 | - | A man in black clothing walks along a paved alleyway beside a brick building, repeatedly throwing small objects toward a window with a visible cracked pane. The pavement is wet, and the alley is otherwise empty with no other people or vehicles present. |
| 3 | traffic_flows_in_the_open_lanes | 07:16:04-07:16:34 | 6.2 | - | The scene shows a multi-lane urban roadway with a marked bus lane on the left and a construction zone on the far left. A red-and-white mini excavator is parked in the bus lane, surrounded by orange traffic cones and temporary barriers, with workers in high-vis |
| 4 | vehicle_breakdown_traffic_queue | 07:16:26-07:16:56 | 8.1 | stalled vehicle, collision | A silver pickup truck is stopped in the middle of the intersection with its driver-side door open and a person standing outside. Smoke is visibly rising from the vehicle, indicating a mechanical issue or fire. Traffic is halted in the adjacent lanes, and pedes |
| 4 | bin_pushed_over_onto_sidewalk | 07:16:26-07:16:56 | 8.1 | - | A person in dark clothing and white sneakers attempts to tip a large green wheeled trash bin on a tiled sidewalk. The bin tips over and rolls onto the pavement, where the person walks away. The scene repeats: the bin is upright, the person tips it again, it fa |
| 4 | escooter_left_across_sidewalk | 07:16:26-07:16:56 | 8.0 | - | A person in dark clothing and white sneakers is seen on a sidewalk next to a parked electric scooter. The rider dismounts, walks a few steps, then returns to the scooter, mounts it, and rides away down the bike lane. The pavement is wet, and a silver car passe |
| 4 | school_gate_break_in_night | 07:16:34-07:17:04 | 9.1 | tampering | A person in dark clothing approaches a locked metal gate at night, crouches to inspect the lock, and attempts to pick or manipulate it with a tool. After a brief pause, they stand, look around cautiously, and crouch again to continue working on the lock. The s |
| 4 | person_on_railway_tracks | 07:16:34-07:17:04 | 9.0 | - | A person in a red jacket and black pants walks along a train platform, stops at the yellow tactile paving, and sits on the edge of the platform facing the tracks. After a brief pause, they stand up and walk away from the tracks, continuing along the platform.  |
| 4 | graffiti_on_standing_train | 07:16:34-07:17:04 | 8.9 | damage | A person in dark clothing walks along the platform toward a stationary red train, stops at the yellow safety line, and begins spray-painting graffiti on the train's side. The individual pauses briefly, then resumes painting before stepping back and walking awa |
| 4 | busy_street | 07:16:43-07:17:13 | 16.2 | - | The scene shows a busy urban street at night with a dense crowd of pedestrians filling the roadway and sidewalks. People are walking in both directions, some pausing or looking around, while vehicles move slowly through the congested lanes. Streetlights and il |
| 4 | highway_traffic_overcast_weather | 07:16:43-07:17:13 | 16.1 | - | The scene shows a wet, multi-lane highway under overcast, rainy conditions with reduced visibility. Vehicles travel steadily in both directions, maintaining lanes and consistent speeds despite the slick pavement. No abrupt maneuvers, collisions, or traffic dis |
| 4 | city_street_7_condensation_inside_housing | 07:16:43-07:17:13 | 16.0 | - | The scene shows a clear, dry urban intersection with vehicles stopped at a red light. A red SUV is positioned in the rightmost lane, waiting at the signal. Lane markings are visible, and the pavement appears smooth and well maintained. No pedestrians or cyclis |
| 4 | vandalism | 07:16:59-07:17:29 | 8.3 | - | A man in black clothing repeatedly throws a small object toward a building's windows, causing visible cracks and shattering in the glass. The pavement is wet, and the man walks back and forth along the curb, pausing to aim and throw. |
| 4 | traffic_flows_in_the_open_lanes | 07:16:59-07:17:29 | 8.2 | - | The scene shows a multi-lane urban roadway with a marked bus lane on the left and a construction zone on the far left. A small white excavator is parked in the bus lane, surrounded by orange traffic cones and temporary barriers, with workers in high-visibility |
| 5 | vehicle_breakdown_traffic_queue | 07:17:26-07:17:56 | 8.8 | stalled vehicle | A silver pickup truck is stopped in the middle of the intersection with its driver-side door open and a person standing outside. Smoke is visibly emanating from the vehicle's engine area. Traffic is halted in the adjacent lanes, and pedestrians are crossing th |
| 5 | bin_pushed_over_onto_sidewalk | 07:17:26-07:17:56 | 8.7 | - | A person in dark clothing and white sneakers attempts to tip a large green wheeled trash bin on a city sidewalk. The bin tips over and rolls onto the pavement, where the person walks away. The scene repeats: the bin is upright, the person tips it again, it fal |
| 5 | escooter_left_across_sidewalk | 07:17:26-07:17:56 | 8.7 | - | A person in dark clothing and white sneakers is seen on a sidewalk next to a parked electric scooter. The rider dismounts, walks a few steps, then returns to the scooter, mounts it, and rides away down the bike lane. The pavement is wet, and a passing car brie |
| 5 | school_gate_break_in_night | 07:17:35-07:18:05 | 9.9 | tampering | A person in dark clothing approaches a locked metal gate at night, carrying a tool. They pause, look around cautiously, and crouch to work on the lock, attempting to pick or manipulate it. The scene is lit by a nearby streetlamp, casting long shadows and highl |
| 5 | person_on_railway_tracks | 07:17:35-07:18:05 | 9.8 | - | A person in a red jacket and black pants walks along a train platform, stops at the yellow tactile paving, and sits on the edge of the platform facing the tracks. After a brief pause, they stand up and walk away from the tracks, continuing along the platform.  |
| 5 | graffiti_on_standing_train | 07:17:35-07:18:05 | 9.8 | damage | A person in dark clothing approaches the platform edge, pauses, and begins spray-painting graffiti on the side of a stationary red train. The individual applies multiple colors in a deliberate, continuous motion, stepping back and forth to cover a section of t |
| 5 | busy_street | 07:17:45-07:18:15 | 16.2 | - | The scene shows a busy urban street at night with a dense crowd of pedestrians filling the roadway. People are walking in both directions, some pausing or looking around, while vehicles move slowly through the congestion. Streetlights and illuminated storefron |
| 5 | highway_traffic_overcast_weather | 07:17:45-07:18:15 | 16.2 | - | A black sedan travels along a wet, multi-lane highway in rainy conditions, maintaining a steady speed and lane position. The pavement is visibly wet and reflective, with lane markings appearing slightly muted. The vehicle proceeds smoothly without abrupt maneu |
| 5 | city_street_7_condensation_inside_housing | 07:17:45-07:18:15 | 16.1 | - | The scene shows a clear, dry urban intersection with vehicles stopped at a red light. A red SUV is positioned in the rightmost lane, waiting at the signal. Lane markings are visible, and the pavement appears well maintained. No pedestrians or cyclists are pres |
| 5 | vandalism | 07:18:01-07:18:31 | 7.5 | collision, damage | A man in black clothing walks along a paved alleyway beside a brick building, then throws a small object toward a window. The projectile strikes the glass, causing it to shatter into multiple fragments. The man watches the impact, then walks away as the broken |
| 5 | traffic_flows_in_the_open_lanes | 07:18:01-07:18:31 | 7.5 | - | The scene shows a multi-lane urban roadway with a closed leftmost lane marked "BUS LANE" and a construction zone on the left. A red-and-white mini excavator is parked in the closed lane, surrounded by orange traffic cones and barriers, with workers in high-vis |
| 6 | vehicle_breakdown_traffic_queue | 07:18:26-07:18:56 | 7.6 | stalled vehicle | A silver pickup truck is stopped in the middle of the roadway with its driver-side door open and a person standing outside. Smoke is visibly emanating from the vehicle, indicating a mechanical issue or fire. Traffic is halted behind the truck, and pedestrians  |
| 6 | bin_pushed_over_onto_sidewalk | 07:18:26-07:18:56 | 7.5 | - | A person in a dark hoodie and black pants attempts to tip a large green wheeled trash bin on the sidewalk, but the bin remains upright and rolls slightly forward. The individual steps back, walks away, and later returns to try again, repeating the same unsucce |
| 6 | escooter_left_across_sidewalk | 07:18:26-07:18:56 | 7.5 | - | A person in dark clothing and white sneakers is seen on a sidewalk next to a parked electric scooter. The rider dismounts, walks a few steps, then returns to the scooter, mounts it, and rides away down the bike lane. The pavement is wet, and a passing car brie |
| 6 | school_gate_break_in_night | 07:18:34-07:19:04 | 12.8 | tampering | A person in dark clothing approaches a locked metal gate at night, crouches to inspect the lock, and attempts to pick or manipulate it with a tool. After a brief pause, they stand, look around cautiously, and crouch again to continue working on the lock. The s |
| 6 | person_on_railway_tracks | 07:18:34-07:19:04 | 12.7 | - | A person in a red jacket and black pants walks along a train platform, stops at the yellow tactile paving, and sits on the edge of the platform facing the tracks. After a brief pause, they stand up and walk away from the tracks, continuing along the platform.  |
| 6 | graffiti_on_standing_train | 07:18:38-07:19:08 | 8.7 | damage | A person in dark clothing stands on the platform near a red train, holding a spray can and applying colorful graffiti to the train's side. The individual moves along the train, pausing to spray in sections, while another person remains on the opposite platform |
| 6 | busy_street | 07:18:46-07:19:16 | 17.4 | - | The scene shows a busy urban street at night with a dense crowd of pedestrians filling the roadway and sidewalks. People are walking in both directions, some in groups and others alone, with many wearing winter coats and hats. Vehicles, including a red double- |
| 6 | highway_traffic_overcast_weather | 07:18:46-07:19:16 | 17.3 | - | A single silver SUV enters from the right and travels straight in the middle lane of a multi-lane highway, maintaining a steady speed and consistent lane position. The road surface is dry with clear lane markings, and visibility is reduced by dense fog that ob |
| 6 | city_street_7_condensation_inside_housing | 07:18:46-07:19:16 | 17.2 | - | The scene shows a clear, dry urban intersection with vehicles stopped at a red light. A red SUV is stationary in the rightmost lane, while a white sedan and a dark sedan are stopped in the leftmost lane. Lane markings are visible, and the pavement appears smoo |
| 6 | vandalism | 07:19:04-07:19:34 | 8.6 | - | A man in black clothing walks along a paved alleyway beside a brick building, then repeatedly throws a small object toward a window on the building's facade. Each throw results in the window glass shattering, producing visible cracks and broken fragments. The  |
| 6 | traffic_flows_in_the_open_lanes | 07:19:04-07:19:34 | 8.6 | - | The scene shows a multi-lane urban roadway with a marked bus lane on the left and a construction zone on the far left. A red-and-white mini excavator is parked in the bus lane, surrounded by orange traffic cones and temporary barriers, with workers in high-vis |
