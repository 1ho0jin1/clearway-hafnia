# Operator verdicts (F7), first live test: answers still in the lens queue (2026-10-25)

`scripts/run_clearway.py --minutes 5 --alarms --close-alarms-at-end` (the stand-in answering: no Hafnia requests;
alarms named "[dry run]", closed at the end) with the board following it. A test script posted to the board's
`/api/operator` as its page does, once each camera's first card was there.

- The board refused what it should: a form post (415), another origin (403), an unknown verdict (400), an unknown
  card (409), a second click before the service had the first (409), confirming a rejected card (409).
- E-scooter card confirmed: its XProtect alarm went to In progress. Bin card (`cw-0007`) rejected: its alarm closed
  with "Rejected by the operator on the Clearway board: not an incident." Both applied within a second of the post
  (the service reads `operator.jsonl` every second).
- After the rejection, 18 later bin changes looked like the rejected card and were skipped.
- **The bin card came back**, though. The bin's first occurrence had been asked about in five pieces; two of them,
  asked before the verdict and still waiting for the lens (`cw-0011`, `cw-0012`), were answered OBSTRUCTION after it.
  With the rejected card out of reach they became new cards with their own alarms, and a look-alike that stayed 30 s
  was asked about after all and reopened one of them. That is 8 cards for 6 incidents.

Fixed in the ledger (`_same_incident`): an answer about what the operator rejected joins the rejected card when it
names the same category, without a card or an alarm. That covers a question asked before the verdict, and one about a
change held as a look-alike of the card. Replaying this run's own inputs through the fixed ledger (`changes.jsonl`,
each question's recorded answer and delay, the two verdicts at their times) gives 6 cards: the bin card rejected with
23 occurrences, five later answers joined to it, 20 changes skipped. Live again in
`run/clearway-dry-20261025T133738Z-operator`.
