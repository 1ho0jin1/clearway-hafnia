# Submission text

For the portal (closes 2 November 2026, 12:00 CET). The portal asks for a working solution, a solution description,
a demonstration video and the source code. The description below is about 430 words; shorten from the bottom if the
form has a lower limit. Paste the repository link and the video link where the form asks for them.

## Title

Clearway

## One line

Clearway keeps public ways clear: it watches a city's XProtect cameras for what blocks or endangers a way, asks
Hafnia VLM once about each incident, and turns the answer into an XProtect alarm, a card for the owner and a push to
their phone.

## Description

Clearway watches a city's XProtect cameras for things that block or endanger a public way: a vehicle stalled in a
lane, a person on the tracks, an e-scooter dropped across a pavement, a bin tipped over, damage to transit. It asks
the Hafnia VLM about each incident once, and turns the answer into one XProtect alarm with bookmarks, one card on an
owner board (rail control, traffic operations, street services, asset owners, security), and one push to the owner's
phone with Confirm and Reject.

Noticing an obstruction with a vision-language model is table stakes. Clearway's contribution is the optimization
around the model.

Every request is earned. Nothing asks Hafnia on a timer or a motion event. A change detector on the live frames
notices what arrived and stayed; a memory of past verdicts skips what Hafnia or an operator already judged; the
pieces and recurrences of one incident are merged. Three hours on eleven cameras cost 33 requests, one per
camera-hour. The plain way, the organizers' example question asked of every camera once a minute, costs 60 per
camera-hour and spends the day's 500 in 45 minutes.

Hafnia is shown the right thing. A small spot is cropped and enlarged on a magnifier camera of our own, so the model
sees a 30-pixel crash large: the full frame called it NONE twice, the magnified clip named it. The magnifier
camera's frames carry a code that the service reads back from the recording, so each question covers the seconds
the recording really holds. Six times out of six, the plain full frame left a person on the platform; the magnified
clip put them on the tracks.

The answer is checked, not trusted. Live answers are scored against the expected category and audited against the
frames; the wrong ones are traced to causes and the causes removed. The three-hour shift produced four false alarms,
all traced to one defect in the magnifier camera's time base. The next run, 14 requests over twenty minutes, produced
seven alarms and none false, 20 to 42 seconds after the change.

One alarm per incident, kept right over time: raised once, reopened on a recurrence, closed by itself when the spot
clears. Confirm and Reject, on the board or the phone, teach the memory, so the system adapts to a site without
retraining.

Everything is measured and reproducible. Every run folder in the repository carries its numbers and a README,
decisions replay offline from the logs, and one script sets up a fresh machine. The limit is stated too: on three
real streets it had never seen, the same prompt turned 31 of 39 hard negatives, mostly cars waiting at a light, into
incidents. The fix lies upstream of the model and is not built; a second confirming question and a size floor in
square metres were both measured and not adopted.

Built with XProtect 2026 R1 (MIP SDK frames, the REST API for alarms and bookmarks, an RTSP camera of our own
through MediaMTX), the Hafnia gateway API, Python, YOLO11 for people and SigLIP 2 for the look of a spot.

## Links

- Repository: `https://github.com/1ho0jin1/hafnia-hackathon-2026` (private today: make it public, grant the judges
  access, or upload an archive, whichever the form takes)
- Video: `docs/video/clearway.mp4` once the final cut is built; upload or link as the form asks
- Where to start reading: `README.md`, then `docs/walkthrough/index.html` (the pipeline step by step with figures)
