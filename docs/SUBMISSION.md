# Submission text

For the portal (closes 2 November 2026, 12:00 CET). The form, read 2026-11-01, has these fields; the answers are
one or two sentences each, as it asks. The video must be public or unlisted and **under 3 minutes**. Paste the
repository link and the video link where the form asks for them.

## Short Project Description (1-3 sentences)

Clearway keeps public ways clear: it watches a city's XProtect cameras for what blocks or endangers a way, such as a
stalled vehicle, a person on the tracks or an object across a pavement, asks Hafnia VLM once about each incident,
and turns the answer into an XProtect alarm, a card for the responsible owner and a push to their phone.

## What problem does your solution solve, and for whom?

City and transit operators have many cameras and few eyes, so an obstruction sits unseen until someone complains,
and a model asked on a timer burns the allowance and floods people with text. Clearway tells rail control, traffic
operations and street services what is blocking a way right now, whose job it is and how long it has been there, at
one request per incident.

## How does your solution use XProtect?

Live frames come from the cameras through the MIP SDK, and each verified incident becomes an XProtect alarm with a
snapshot and bookmarks through the REST API, closed by itself when the spot clears and reopened when it recurs. A
magnifier camera of our own is registered in XProtect so that Hafnia, which reads only XProtect recordings, can be
asked about an enlarged clip of a small spot.

## How does your solution use Hafnia VLM?

Hafnia is asked through the gateway API only when a change detector sees something arrive and stay and no earlier
verdict covers it, and it is shown a clip centred on the moment and cropped to the spot. It answers in JSON with a
category, a summary and the evidence, which names the owner and the priority; every answer is scored and audited
against the frames.

## What value does your solution add?

Three hours on eleven cameras cost 33 requests, one per camera-hour, against 60 per camera-hour for asking every
camera once a minute, and the operator gets one alarm per incident instead of a paragraph per request. Owners get a
card and a push with Confirm and Reject that teach the system, and every claim is measured and reproducible from the
repository, including the known limit on real streets.

## Demonstration Video (public or unlisted, under 3 minutes)

The video in the README (2:57, GitHub's upload). The storyboard is in `VIDEO.md`.

## What did you build during the hackathon, and what existed before? (max 100 words)

Everything in the repository was written during the hackathon, from the first benchmark on 15 October: the change
detector, the incident ledger, the service, the magnifier camera, the XProtect alarms, the owner board, the phone
pushes, the setup script and every measurement. It builds on the organizers' XProtect 2026 R1 and Hafnia gateway,
Milestone's MIP SDK, and open-source libraries: Ultralytics YOLO11 (people), SigLIP 2 (the look of a spot), OpenCV,
MediaMTX and ffmpeg (the magnifier camera), ntfy (pushes). No earlier code of our own was used.

(86 words. Real-ESRGAN is in the repository but not in the product: it was measured and left out of the lens.)

## Links

- Repository: `https://github.com/1ho0jin1/hafnia-hackathon-2026` (private today: make it public, grant the judges
  access, or upload an archive, whichever the form takes)
- Where to start reading: `README.md`, then `docs/walkthrough/index.html` (the pipeline step by step with figures)

## Longer description (if a field allows it; about 430 words)

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
