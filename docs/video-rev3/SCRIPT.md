# Clearway demo video: the script (rev. 3, 2026-11-02)

The source of truth is `script.json` (one entry per line, with what is on screen and the pause after it); this page is
the same text for reading. Spoken like a talk: each scene opens with a short lead-in.

At a calm 2.4 words/s the cut comes to about 2:58; with Kokoro's pace (about 2.8 words/s) about 2:50. The portal's
limit is 3:00.

| # | Scene | On screen | Narration | Words | ≈ Length |
|---|---|---|---|---|---|
| 1 | `title` | Title card | Hello everyone, this is Clearway. It watches cameras managed by XProtect for anything blocking a public way, asks Hafnia VLM once per incident, and turns the answer into one alarm in XProtect, one card on the owner board, and one push to the team that owns it. | 47 | 20 s |
| 2 | `spoiler` | The finished owner board: one column per team. The view moves to each card as you name it. | Here's where we'll end up: one column per responsible team. A person on the tracks goes to rail control, a stalled truck to traffic operations, and a bin on the pavement to street services. | 34 | 15 s |
| 3 | `pipeline` | The pipeline flowchart. The view moves to each stage as you name it. | Now, how does it work? A change detector finds what arrived and stayed. YOLO holds back passing people and watches the tracks. SigLIP 2 fingerprints the spot, and the incident memory skips what was already judged. Only something new reaches Hafnia VLM, small spots magnified first: one request, one answer. | 50 | 22 s |
| 4 | `board` | Smart Client's eleven cameras, then the owner board filling (16 s of footage) | Here it is live, on eleven cameras. Within a minute, every incident has a card in its owner's column, with the clip Hafnia judged, its verdict, and its alarm. | 29 | 16 s |
| 5 | `clip` | The stalled truck's clip | Let's open one card. This is the clip Hafnia saw, and its verdict: a silver pickup stalls in the lane, door open, smoke rising, blocking traffic. | 26 | 12 s |
| 6 | `smartclient` | The XProtect alarms card | In XProtect, the same incident is one alarm, with the category, the owner, Hafnia's summary, and a snapshot. It closes when the spot clears, and reopens if it happens again. | 30 | 13 s |
| 7 | `phone` | Your phone recording: the push, the tap (17 s of footage) | The owner also gets it on their phone, with two buttons: Confirm and Reject. A tap reaches the system in under a second, and either answer teaches the memory. | 29 | 17 s |
| 8 | `verdict` | The Confirm / Reject chart. The view moves through both lanes as you go. | So what does each answer do? Confirm puts the alarm in progress, and look-alikes there are no longer skipped. Reject closes the alarm and marks that look harmless at that spot; a look-alike is asked about again only if it stays thirty seconds. | 43 | 19 s |
| 9 | `numbers` | The Numbers card | So, does it pay off? Three hours on eleven cameras cost thirty-three requests, one per camera-hour, and the next run had no false cards. On real streets it had never seen, waiting cars became false cards; that's our known limit. | 40 | 17 s |
| 10 | `compare` | The plain way against Clearway | Compare the plain way: asking every camera once a minute. That's sixty requests per camera-hour, the day's five hundred gone in forty-five minutes, against Clearway's one. And the full frame never put the person on the tracks; the magnified clip did. | 41 | 18 s |
| 11 | `close` | The closing card | To sum up, Clearway keeps public ways clear, and spends the model's attention only where it earns it. Thank you. | 20 | 9 s |

**Optional, left out by default:** `measured` (Optional: the Measured card (added back only if there is room)): "How do we know it works? We measured every step, and fixed three faults we found: the magnifier camera's clock, a detector that faded, and alarms slowed by our own load."
Built only with `--with-optional`, if the cut leaves about 14 s under 3:00.

## Lines that move the view

In `spoiler`, `pipeline` and `verdict`, each line brings the next view (`on_screen` in `script.json`). In `board`,
the second line cuts from the eleven cameras to the board. The pipeline holds the change detector and YOLO longer
(a 1.4 s pause after each of those lines in the TTS take).

## If the cut runs over 3:00

End `compare` after "against Clearway's one." (−5 s), then drop "small spots magnified first" from `pipeline` (−2 s).
