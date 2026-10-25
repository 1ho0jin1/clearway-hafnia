"""The ledger: one record per incident, the board's and the shift summary's single source (docs/PRODUCT.md, F1).

An *incident* is one problem at one spot (a scooter lying across the pavement there). An *occurrence* is one time it
happens: the change detector reports it, it lasts, the spot clears. A looped clip replays the same incident every
15 s; a real street sees the same kind of thing at the same spot again later. Recognising a known incident again
costs no Hafnia request and gives an instant card, which is what keeps the allowance for new things.

The ledger decides; it does not act. Each call returns actions for the service to carry out (ask Hafnia, raise or
close an XProtect alarm), so the same logic runs live and in offline replays (scripts/eval_ledger.py). Every decision
is appended to an event log (JSONL); `Ledger.replay()` rebuilds the state from it, and the board and the summary read
it.

Matching a new change, in order:
1. *Fragment*: it overlaps a change already active in an incident (the detector often reports a spot in two pieces):
   attached, nothing else happens.
2. *Recurrence*: same camera, same spot (the boxes' overlap covers min_overlap of the smaller one), and it looks like
   the incident (SigLIP 2 similarity
   >= recur_sim to one of its occurrences), more than like anything Hafnia rejected there; the incident is pending or
   open, or cleared within recurrence_window_s. No request; a cleared incident reopens.
3. *Known rejection*: it looks like a change Hafnia (or an operator) rejected at that spot: skipped, no request
   (the verdict memory of run/memory-compare). The skip is provisional: a skipped change still there after
   escalate_s is asked about anyway (`tick`). On a real highway a crashed car and a car that merely stopped at that
   spot looked alike to SigLIP (the road dominates a small crop; run/ledger-F1-real); harmless changes tend to leave,
   a crash stays. An operator's verdict (F7, `on_operator`) goes into the same memory: rejecting a card teaches its
   looks as harmless at its spot; confirming one overrules Hafnia's rejections there that look like it.
4. Otherwise a new pending incident and one Hafnia request. If Hafnia's answer names the category of an open or
   recently cleared incident at the same spot, the new one is merged into it (one card; the request was still spent:
   the look had drifted too far, e.g. the breakdown's smoke, or the change straddled a loop restart). An answer about
   what an operator rejected (asked before the verdict, or about a held look-alike of the card) joins the rejected
   card instead when it names the same category: no card, no alarm.
"""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np


# category -> (owner, XProtect alarm priority); docs/PRODUCT.md, "Who uses it"
OWNERS = {
    "PERSON_ON_TRACKS": ("Rail control", "High"),
    "COLLISION": ("Traffic operations", "High"),
    "STALLED_VEHICLE": ("Traffic operations", "High"),
    "OBSTRUCTION": ("Street services", "Medium"),
    "DAMAGE": ("Asset owner", "Low"),
    "TAMPERING": ("Security", "Low"),
}


@dataclass
class Params:
    recur_sim: float = 0.85             # same look (SigLIP 2 cosine) as before; set before measuring, as the memory's
    min_overlap: float = 0.3            # same spot: the overlap covers this share of the smaller box (containment,
                                        # not IoU: a thin strip inside an incident's grown box is the same spot)
    recurrence_window_s: float = 3600   # a cleared incident can recur (reopen) for this long
    close_after_s: float = 60.0         # an incident's alarm closes once it has stayed cleared this long (tick): a
                                        # recurring incident keeps one open alarm instead of closing and reopening it
                                        # with every occurrence (a loop recurs within 15 s); a closed one reopens
    keep_embs: int = 8                  # occurrences' looks kept per incident (the look can drift), kept diverse:
                                        # when full, the older of the two most alike goes (_remember)
    group_s: float = 5.0                # a change near an incident within this long of its last change is a piece of
    near: float = 0.5                   # it ("near": the boxes overlap once each grows by this share on every side);
                                        # the detector reports a tipped bin as its empty place, the bin and its base
    escalate_s: float = 30.0            # a skipped change still open this long is asked about after all
    clip_after_s: float = 3.0           # the lens clip ends this long after the report (scripts/lens_pilot.py
                                        # AFTER_S): a piece reported later was not in the clip Hafnia judged, so it
                                        # does not join a pending incident


@dataclass
class Incident:
    id: str
    camera: str
    box: tuple[int, int, int, int]
    t_change: float                     # when the first occurrence started changing
    t_report: float                     # when the detector reported it
    state: str = "pending"              # pending -> open | dismissed | merged | failed (no answer will come);
                                        # open -> cleared -> (recurrence) open; rejected
    category: str = ""
    owner: str = ""
    priority: str = ""
    answer: dict = field(default_factory=dict)
    t_answer: float | None = None
    t_alarm: float | None = None        # last alarm raised or reopened
    alarms: int = 0                     # times raised or reopened
    alarm_open: bool = False
    t_cleared: float | None = None
    occurrences: int = 1
    operator: str = ""                  # "confirmed" | "rejected"
    t_verdict: float | None = None      # when the operator gave it
    like: str = ""                      # asked after all about a change held as a look-alike of this rejected card
    merged_into: str = ""               # set when a later answer showed it is the same incident as another
    clip: str = ""
    t_last: float = 0.0                 # last change attached
    t_occurrence: float = 0.0           # when the current occurrence started changing (the board's "open for")
    active: dict[int, int] = field(default_factory=dict)  # tier 0 change ids still open -> box area (pixels)
    embs: list[np.ndarray] = field(default_factory=list, repr=False)

    def public(self) -> dict:
        d = asdict(self)
        d.pop("embs")
        d["active"] = sorted(self.active)
        return d


def _area(b) -> int:
    return max(0, b[2] - b[0]) * max(0, b[3] - b[1])


def _grow(b, share: float) -> tuple[float, float, float, float]:
    w, h = b[2] - b[0], b[3] - b[1]
    return (b[0] - share * w, b[1] - share * h, b[2] + share * w, b[3] + share * h)


def _overlap(a, b) -> float:
    """Share of the smaller box covered by the intersection."""
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    small = min(_area(a), _area(b))
    return ix * iy / small if small else 0.0


def _union(a, b) -> tuple[int, int, int, int]:
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


class Ledger:
    def __init__(self, log: Path | None = None, params: Params | None = None, clock=time.time):
        self.p = params or Params()
        self.log = log
        self.clock = clock
        self.incidents: dict[str, Incident] = {}
        # (camera, box, look, incident, "hafnia" | "operator"): what was rejected where, and by whom
        self.rejections: list[tuple[str, tuple, np.ndarray, str, str]] = []
        self.change_to_incident: dict[tuple[str, int], str] = {}
        self.held: dict[tuple[str, int], dict] = {}   # skipped changes still open: escalated by tick() if they stay
        self.stats = {"changes": 0, "asked": 0, "recurrences": 0, "fragments": 0, "skipped": 0, "escalated": 0,
                      "skipped_operator": 0}    # of the skipped: like a card an operator rejected
        self._n = 0

    # --- event log -------------------------------------------------------------------------------------------------
    def _emit(self, kind: str, **fields) -> None:
        if self.log is None:
            return
        rec = {"kind": kind, "wall": self.clock(), **fields}
        with self.log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=_jsonable) + "\n")

    # --- decisions ---------------------------------------------------------------------------------------------------
    def on_change(self, camera: str, change_id: int, t_change: float, t_report: float, box, emb: np.ndarray) -> dict:
        """A change reported by tier 0. Returns {"action": "fragment" | "recur" | "skip" | "ask", "incident": id, ...}."""
        self.stats["changes"] += 1
        box = tuple(int(v) for v in box)
        emb = np.asarray(emb, np.float32)
        live = [i for i in self.incidents.values()
                if i.camera == camera and _overlap(box, i.box) >= self.p.min_overlap]

        def piece_of(i: Incident) -> bool:
            if not i.active or i.state not in ("pending", "open"):
                return False
            if i.state == "pending" and t_report > i.t_report + self.p.clip_after_s:
                return False
            if _overlap(box, i.box) >= self.p.min_overlap:
                return True
            return (t_report - i.t_last <= self.p.group_s
                    and _overlap(_grow(box, self.p.near), _grow(i.box, self.p.near)) > 0)

        frag = next((i for i in self.incidents.values() if i.camera == camera and piece_of(i)), None)
        if frag is not None:
            frag.active[change_id] = _area(box)
            frag.box, frag.t_last = _union(frag.box, box), t_report
            self.change_to_incident[(camera, change_id)] = frag.id
            self.stats["fragments"] += 1
            self._emit("fragment", incident=frag.id, camera=camera, change=change_id, t=t_report, box=box,
                       area=_area(box), incident_box=frag.box)
            return {"action": "fragment", "incident": frag.id}

        def look(i: Incident) -> float:
            return max((float(emb @ e) for e in i.embs), default=0.0)

        reopenable = [i for i in live if i.state in ("pending", "open")
                      or (i.state == "cleared" and t_report - (i.t_cleared or 0) <= self.p.recurrence_window_s)]
        best = max(reopenable, key=look, default=None)
        s_inc = look(best) if best else 0.0
        s_rej, like, by = max(((float(emb @ e), i, by) for c, b, e, i, by in self.rejections
                               if c == camera and _overlap(box, b) >= self.p.min_overlap), default=(0.0, "", ""))

        if best is not None and s_inc >= self.p.recur_sim and s_inc >= s_rej:
            return self._recur(best, camera, change_id, t_change, t_report, emb, s_inc)
        if s_rej >= self.p.recur_sim and s_rej > s_inc:
            self.stats["skipped"] += 1
            self.stats["skipped_operator"] += by == "operator"
            self.held[(camera, change_id)] = {"t_change": t_change, "t_report": t_report, "box": box, "emb": emb,
                                              "by": by, "like": like}
            self._emit("skip", camera=camera, change=change_id, t=t_report, box=box, similarity=round(s_rej, 3),
                       like=like, by=by)
            return {"action": "skip", "incident": None, "similarity": s_rej, "like": like, "by": by}
        return self._ask(camera, change_id, t_change, t_report, box, emb)

    def _ask(self, camera, change_id, t_change, t_report, box, emb, escalated_at: float | None = None,
             like: str = "") -> dict:
        """like: the operator-rejected card an escalated change was held as a look-alike of."""
        self._n += 1
        t = t_report if escalated_at is None else escalated_at
        # t_last stays the change's own report time: an old change escalated now must not group with a new one
        inc = Incident(f"cw-{self._n:04d}", camera, box, t_change, t, t_last=t_report,
                       active={change_id: _area(box)}, embs=[emb], t_occurrence=t_change, like=like)
        self.incidents[inc.id] = inc
        self.change_to_incident[(camera, change_id)] = inc.id
        self.stats["asked"] += 1
        self._emit("ask", incident=inc.id, camera=camera, change=change_id, t_change=t_change, t=t, box=box,
                   area=_area(box), emb=emb, escalated=escalated_at is not None, like=like)
        return {"action": "ask", "incident": inc.id, "escalated": escalated_at is not None, "change": change_id}

    def tick(self, t: float) -> list[dict]:
        """Call regularly (every second). Asks about skipped changes that have stayed for escalate_s ({"action":
        "ask", ...}) and closes the alarms of incidents that have stayed cleared for close_after_s ({"close_alarm": ...})."""
        out = []
        for key, h in list(self.held.items()):
            if t - h["t_report"] >= self.p.escalate_s:
                del self.held[key]
                self.stats["skipped"] -= 1
                self.stats["skipped_operator"] -= h["by"] == "operator"
                self.stats["escalated"] += 1
                out.append(self._ask(key[0], key[1], h["t_change"], h["t_report"], h["box"], h["emb"], escalated_at=t,
                                     like=h["like"] if h["by"] == "operator" else ""))
        for inc in self.incidents.values():
            if inc.alarm_open and inc.state == "cleared" and t - inc.t_cleared >= self.p.close_after_s:
                out += self._close_alarm(inc, t, "cleared")
        return out

    def _recur(self, inc: Incident, camera, change_id, t_change, t_report, emb, sim) -> dict:
        inc.active[change_id] = _area(tuple(inc.box))
        inc.t_last = t_report
        self._remember(inc, [emb])
        self.change_to_incident[(camera, change_id)] = inc.id
        inc.occurrences += 1
        self.stats["recurrences"] += 1
        actions = []
        if inc.state == "cleared":
            inc.state = "open"
            inc.t_cleared, inc.t_occurrence = None, t_change
            actions = self._alarm(inc, t_report, recurrence=True, t_change=t_change)
        self._emit("recur", incident=inc.id, camera=camera, change=change_id, t_change=t_change, t=t_report,
                   similarity=round(sim, 3), occurrences=inc.occurrences, state=inc.state, emb=emb,
                   area=inc.active[change_id])
        return {"action": "recur", "incident": inc.id, "similarity": sim, "effects": actions}

    def on_answer(self, incident_id: str, category: str, answer: dict, t: float, clip: str = "") -> list[dict]:
        """Hafnia's verdict on a pending incident. Returns effects: [{"alarm": ...}] or []. An incident whose spot has
        already cleared still raises its alarm (a person who left the tracks before the answer came is still news for
        rail control); it closes after close_after_s like any other."""
        inc = self.incidents[incident_id]
        inc.answer, inc.t_answer, inc.clip = answer, t, clip or inc.clip
        if category in OWNERS:
            inc.category = category
            inc.owner, inc.priority = OWNERS[category]
            target = self._same_incident(inc, t)
            if target is not None:
                return self._merge(inc, target, t)
            inc.state = "open" if inc.active else "cleared"
            if not inc.active:
                inc.t_cleared = t
            effects = self._alarm(inc, t, t_change=inc.t_change)
        else:
            inc.state = "dismissed"
            self.rejections += [(inc.camera, inc.box, e, inc.id, "hafnia") for e in inc.embs]
            effects = []
        self._emit("answer", incident=inc.id, t=t, category=category or "NONE", state=inc.state, answer=answer,
                   clip=inc.clip, owner=inc.owner, priority=inc.priority)
        return effects

    def on_failed(self, incident_id: str, t: float, reason: str) -> None:
        """No answer will come for a pending incident (its clip or its request failed). It is dropped, so the next
        change at the spot is asked about anew: live, the gate's first question was lost and its incident stayed
        pending, gathering 39 occurrences that never got a card (2026-10-25)."""
        inc = self.incidents[incident_id]
        if inc.state != "pending":
            return
        for c in inc.active:
            self.change_to_incident.pop((inc.camera, c), None)
        inc.state, inc.active = "failed", {}
        self._emit("failed", incident=inc.id, t=t, reason=reason)

    def _same_incident(self, inc: Incident, t: float) -> Incident | None:
        """The incident with the same category at the same spot that a new answer belongs to, if any: first a card the
        operator rejected, when this question was asked before the verdict (a piece of what the operator judged, still
        in the lens queue) or about a change held as a look-alike of that card; otherwise an open or recently cleared
        one. Live, two pieces of the bin's first occurrence answered after its card was rejected and became new cards,
        and a look-alike that stayed was asked about after all and reopened one (2026-10-25)."""
        same = [o for o in self.incidents.values()
                if o is not inc and o.camera == inc.camera and o.category == inc.category and not o.merged_into
                and _overlap(o.box, inc.box) >= self.p.min_overlap]
        for o in same:
            if o.state == "rejected" and (inc.like == o.id or inc.t_report <= (o.t_verdict or 0)):
                return o
        for o in same:
            if o.state == "open" or (o.state == "cleared" and t - (o.t_cleared or 0) <= self.p.recurrence_window_s):
                return o
        return None

    def _merge(self, inc: Incident, target: Incident, t: float) -> list[dict]:
        for c, area in inc.active.items():
            target.active[c] = area
            self.change_to_incident[(inc.camera, c)] = target.id
        self._remember(target, inc.embs)
        if target.state == "rejected":      # following the operator: these looks are rejected at the spot too
            self.rejections += [(inc.camera, inc.box, e, target.id, "operator") for e in inc.embs]
        target.box = _union(target.box, inc.box)
        target.occurrences += inc.occurrences
        effects = []
        if inc.active and target.state == "cleared":
            target.state, target.t_cleared, target.t_occurrence = "open", None, inc.t_change
            effects = self._alarm(target, t, recurrence=True, t_change=inc.t_change)
        inc.state, inc.merged_into, inc.active = "merged", target.id, {}
        self._emit("merge", incident=inc.id, into=target.id, t=t, category=inc.category, answer=inc.answer,
                   occurrences=target.occurrences, state=target.state)
        return effects

    def _remember(self, inc: Incident, embs: list[np.ndarray]) -> None:
        """Add looks to an incident, keeping keep_embs of them and keeping them diverse: when full, the older of the two
        most alike goes. Keeping only the latest forgot the looks of an incident's rarer spots: on the school gate,
        live, 24 occurrences at one spot pushed out the others' and each was asked about again (2026-10-25)."""
        kept = inc.embs + list(embs)
        while len(kept) > self.p.keep_embs:
            m = np.stack(kept)
            sim = m @ m.T
            np.fill_diagonal(sim, -np.inf)
            i, j = np.unravel_index(int(np.argmax(sim)), sim.shape)
            kept.pop(min(i, j))
        inc.embs = kept

    def _alarm(self, inc: Incident, t: float, recurrence: bool = False, t_change: float | None = None) -> list[dict]:
        """Raise the incident's alarm, or reopen it if it was closed; nothing while it is open. t_change: when the
        occurrence that raised it started changing (for the service's bookmark)."""
        if inc.alarm_open:
            return []
        inc.alarm_open, inc.t_alarm = True, t
        inc.alarms += 1
        self._emit("alarm", incident=inc.id, t=t, owner=inc.owner, priority=inc.priority, recurrence=recurrence,
                   occurrences=inc.occurrences)
        return [{"alarm": inc.id, "owner": inc.owner, "priority": inc.priority, "recurrence": recurrence,
                 "reopen": inc.alarms > 1, "t": t, "t_change": t_change if t_change is not None else t}]

    def _close_alarm(self, inc: Incident, t: float, reason: str) -> list[dict]:
        inc.alarm_open = False
        self._emit("alarm_closed", incident=inc.id, t=t, reason=reason)
        return [{"close_alarm": inc.id, "reason": reason, "t": t, "t_cleared": inc.t_cleared}]

    def on_change_closed(self, camera: str, change_id: int, t: float, how: str) -> list[dict]:
        """Tier 0 saw the spot look as before (or the scene jumped). An incident clears when its largest active change
        closes: a small piece that never looks quite as before must not keep it open forever. Its alarm closes later,
        once it has stayed cleared for close_after_s (tick)."""
        self.held.pop((camera, change_id), None)
        incident_id = self.change_to_incident.pop((camera, change_id), None)
        if incident_id is None:
            return []
        inc = self.incidents[incident_id]
        area = inc.active.pop(change_id, 0)
        if inc.active and area < max(inc.active.values()):
            return []
        for rest in list(inc.active):
            self.change_to_incident.pop((camera, rest), None)
        inc.active.clear()
        if inc.state != "open":
            return []           # pending: the answer finds it already clear
        inc.state, inc.t_cleared = "cleared", t
        self._emit("clear", incident=inc.id, t=t, how=how, occurrences=inc.occurrences)
        return []

    def on_operator(self, incident_id: str, verdict: str, t: float) -> list[dict]:
        """An operator's verdict on a card (F7, the board's buttons): "confirmed" or "rejected". Rejecting teaches the
        card's looks as harmless at its spot (the next change there that looks like it is skipped, provisionally like
        any skip) and closes its alarm. Confirming overrules Hafnia's rejections at the spot that look like the card,
        so the next such change joins it instead of being skipped, and puts its alarm in progress. A card can be
        rejected after it was confirmed, not the other way round. ValueError if the verdict does not apply."""
        if problem := self.verdict_problem(incident_id, verdict):
            raise ValueError(problem)
        inc = self.incidents[incident_id]
        overruled = self._verdict(inc, verdict, t)
        self._emit("operator", incident=inc.id, t=t, verdict=verdict, overruled=overruled, state=inc.state)
        if verdict == "confirmed":
            return [{"confirm_alarm": inc.id, "t": t}]
        return self._close_alarm(inc, t, "rejected") if inc.alarm_open else []

    def verdict_problem(self, incident_id: str, verdict: str) -> str | None:
        """Why an operator's verdict cannot apply to this incident now, or None (the board checks before passing one
        on)."""
        inc = self.incidents.get(incident_id)
        if verdict not in ("confirmed", "rejected"):
            return f"unknown verdict {verdict!r}"
        if inc is None:
            return f"no incident {incident_id}"
        if not inc.category or inc.merged_into or inc.state not in ("open", "cleared"):
            return f"{incident_id} cannot take a verdict (state {inc.state})"
        if inc.operator == verdict:
            return f"{incident_id} is already {verdict}"
        return None

    def _verdict(self, inc: Incident, verdict: str, t: float) -> int:
        """The operator's verdict into the memory (live and in replays); returns how many of Hafnia's rejections at
        the spot it overruled."""
        inc.operator, inc.t_verdict = verdict, t
        if verdict == "rejected":
            inc.state = "rejected"
            self.rejections += [(inc.camera, inc.box, e, inc.id, "operator") for e in inc.embs]
            return 0
        looks = np.stack(inc.embs)
        kept = [r for r in self.rejections
                if r[4] == "operator" or r[0] != inc.camera or _overlap(r[1], inc.box) < self.p.min_overlap
                or float(np.max(looks @ r[2])) < self.p.recur_sim]
        overruled = len(self.rejections) - len(kept)
        self.rejections = kept
        return overruled

    # --- reading -----------------------------------------------------------------------------------------------------
    def snapshot(self) -> list[dict]:
        return [i.public() for i in self.incidents.values()]

    @classmethod
    def replay(cls, log: Path, params: Params | None = None) -> "Ledger":
        """Rebuild the state from an event log (after a restart, or for the board and the summary)."""
        led = cls(None, params)
        for line in log.read_text(encoding="utf-8").splitlines():
            if line.strip():
                led.apply(json.loads(line))
        return led

    def apply(self, e: dict) -> None:
        """One event of the log, as _emit wrote it: replay() applies them all; the board applies new ones as the log
        grows (clearway/board.py)."""
        k = e["kind"]
        if k == "ask":
            self._n = max(self._n, int(e["incident"].split("-")[1]))
            inc = Incident(e["incident"], e["camera"], tuple(e["box"]), e["t_change"], e["t"], t_last=e["t"],
                           active={e["change"]: e.get("area", 0)}, embs=[np.array(e["emb"], np.float32)],
                           t_occurrence=e["t_change"], like=e.get("like", ""))
            self.incidents[inc.id] = inc
            self.change_to_incident[(e["camera"], e["change"])] = inc.id
        elif k in ("fragment", "recur"):
            inc = self.incidents[e["incident"]]
            inc.active[e["change"]] = e.get("area", _area(inc.box))
            inc.t_last = e["t"]
            if k == "fragment":
                inc.box = tuple(e["incident_box"])
            self.change_to_incident[(e["camera"], e["change"])] = inc.id
            if k == "recur":
                if inc.state == "cleared" and e["state"] == "open":
                    inc.t_cleared, inc.t_occurrence = None, e["t_change"]
                inc.occurrences, inc.state = e["occurrences"], e["state"]
                self._remember(inc, [np.array(e["emb"], np.float32)])
        elif k == "answer":
            inc = self.incidents[e["incident"]]
            inc.state, inc.answer, inc.t_answer, inc.clip = e["state"], e["answer"], e["t"], e["clip"]
            inc.owner, inc.priority = e["owner"], e["priority"]
            inc.category = e["category"] if e["category"] in OWNERS else ""
            if inc.state == "cleared":
                inc.t_cleared = e["t"]
            if inc.state == "dismissed":
                self.rejections += [(inc.camera, inc.box, x, inc.id, "hafnia") for x in inc.embs]
        elif k == "merge":
            inc, target = self.incidents[e["incident"]], self.incidents[e["into"]]
            inc.category, inc.answer, inc.t_answer = e["category"], e["answer"], e["t"]
            inc.owner, inc.priority = OWNERS[e["category"]]
            for c, area in inc.active.items():
                target.active[c] = area
                self.change_to_incident[(inc.camera, c)] = target.id
            self._remember(target, inc.embs)
            if target.state == "rejected":
                self.rejections += [(inc.camera, inc.box, x, target.id, "operator") for x in inc.embs]
            target.box = _union(target.box, inc.box)
            if target.state == "cleared" and e["state"] == "open":
                target.t_cleared, target.t_occurrence = None, inc.t_change
            target.occurrences, target.state = e["occurrences"], e["state"]
            inc.state, inc.merged_into, inc.active = "merged", target.id, {}
        elif k == "alarm":
            inc = self.incidents[e["incident"]]
            inc.t_alarm, inc.alarms, inc.alarm_open = e["t"], inc.alarms + 1, True
        elif k == "alarm_closed":
            self.incidents[e["incident"]].alarm_open = False
        elif k == "clear":
            inc = self.incidents[e["incident"]]
            for c in inc.active:
                self.change_to_incident.pop((inc.camera, c), None)
            inc.state, inc.t_cleared, inc.active = "cleared", e["t"], {}
        elif k == "failed":
            inc = self.incidents[e["incident"]]
            for c in inc.active:
                self.change_to_incident.pop((inc.camera, c), None)
            inc.state, inc.active = "failed", {}
        elif k == "operator":
            self._verdict(self.incidents[e["incident"]], e["verdict"], e["t"])

def _jsonable(o):
    if isinstance(o, np.ndarray):
        return [round(float(v), 5) for v in o]
    if isinstance(o, (set, tuple)):
        return list(o)
    if isinstance(o, np.generic):
        return o.item()
    raise TypeError(type(o))
