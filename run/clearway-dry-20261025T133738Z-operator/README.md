# Operator verdicts (F7) on a live dry run (2026-10-25)

`scripts/run_clearway.py --minutes 5 --alarms --close-alarms-at-end` (the stand-in answering: no Hafnia requests;
alarms named "[dry run]", closed at the end) with the board following it. A test script posted to the board's
`/api/operator` as its page does: it confirmed the e-scooter card and rejected the bin card. This is the same test as
`run/clearway-dry-20261025T132833Z-operator-inflight`, with the ledger fixed.

- 6 cards, one per incident; 19 questions (16 in the start-up burst); 9.8 fps on every camera, none dropped.
- The board refused what it should: a form post (415), another origin (403), an unknown verdict (400), an unknown
  card (409), a second click before the service had the first (409), confirming a rejected card (409).
- The verdicts were applied 0.1 and 0.3 s after the post.
- **E-scooter, confirmed** (`cw-0003`): the XProtect alarm went to In progress with "Confirmed by the operator on the
  Clearway board."; 7 later occurrences joined the card.
- **Bin, rejected** (`cw-0007`): the alarm closed with "Rejected by the operator on the Clearway board: not an
  incident." The four pieces of its first occurrence still in the lens queue were answered OBSTRUCTION and joined the
  rejected card. 26 later changes looked like it and were skipped; 24 of them were never asked about. Two that stayed
  30 s were asked about after all (the provisional skip's safety net) and joined the card when the answer was
  OBSTRUCTION again. No bin card came back.
- XProtect: 6 alarms raised, 1 set to In progress, 6 closed (the bin's by the rejection, the rest by the test harness
  at the end), 12 bookmarks, 0 errors. Read back: 6 of 6 in the expected state (`report_clearway.py --xprotect`).
- The board, checked in headless Edge screenshots, shows Confirm and Reject on each card; Reject asks for a second
  click. A confirmed card says "Confirmed by the operator"; a rejected one is dimmed with "look-alikes here are
  skipped". The screenshots also showed a card with the previous run's snapshot in its inset. The media URLs were the
  same in every run (`/snaps/cw-0003.jpg`) and cached for an hour, so they now carry the run's name (`?run=`).

Cost to watch on live runs: each escalated look-alike of a rejected card is one request. Here 2 came in the 3 minutes
after the verdict, and they only matter when Hafnia names another category. The verdicts are kept in the run's
ledger: a new run starts without them.
