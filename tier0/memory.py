"""Plan C's verdict memory: Hafnia's past answers, remembered as SigLIP 2 embeddings, become a free filter.

The change detector (tier0/change.py) cannot tell a bus at its stop from a truck broken down in a lane: both changed
and stayed changed. Hafnia can, at one request each. On a busy real street that is hundreds of requests an hour, and
most are the same few harmless things again (the bus stop, a taxi rank, a delivery bay). So every answer is kept:
the changed spot's crop is embedded (google/siglip2-base-patch16-224, Apache-2.0) and stored with the camera, the box
and Hafnia's verdict. A new change is not sent if it overlaps a spot Hafnia rejected and looks like what it rejected
there, unless it looks even more like something Hafnia confirmed there. Every skip is counted, so the saving and the
misses it costs can be measured.

The same model scores a crop against short descriptions (zero-shot), which ranks changes when the budget is tight.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

MODEL = "google/siglip2-base-patch16-224"


class Embedder:
    """SigLIP 2 on the GPU in fp16; crops in, unit vectors out."""

    def __init__(self, model: str = MODEL, device: str = "cuda"):
        import torch
        from transformers import AutoModel, AutoProcessor
        self.torch = torch
        self.device = device
        self.model = AutoModel.from_pretrained(model, dtype=torch.float16).to(device).eval()
        self.proc = AutoProcessor.from_pretrained(model)

    def images(self, crops: list[np.ndarray]) -> np.ndarray:
        if not crops:
            return np.zeros((0, 768), np.float32)
        rgb = [cv2.cvtColor(c, cv2.COLOR_BGR2RGB) for c in crops]
        with self.torch.no_grad():
            x = self.proc(images=rgb, return_tensors="pt").to(self.device)
            e = self.model.get_image_features(pixel_values=x["pixel_values"].half())
            e = getattr(e, "pooler_output", e)
        e = e.float().cpu().numpy()
        return e / np.linalg.norm(e, axis=1, keepdims=True)

    def texts(self, prompts: list[str]) -> np.ndarray:
        with self.torch.no_grad():
            x = self.proc(text=prompts, padding="max_length", max_length=64, return_tensors="pt").to(self.device)
            e = self.model.get_text_features(**x)
            e = getattr(e, "pooler_output", e)
        e = e.float().cpu().numpy()
        return e / np.linalg.norm(e, axis=1, keepdims=True)

    def zero_shot(self, image_embs: np.ndarray, text_embs: np.ndarray) -> np.ndarray:
        """Probability per (crop, description), SigLIP's sigmoid with the model's own scale and bias."""
        scale = float(self.model.logit_scale.exp())
        bias = float(self.model.logit_bias)
        return 1 / (1 + np.exp(-(image_embs @ text_embs.T * scale + bias)))


def crop(frame: np.ndarray, box: tuple[int, int, int, int], pad: float = 0.5, min_side: int = 64) -> np.ndarray:
    """The box with pad on every side (context helps the model), at least min_side pixels."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = box
    bw, bh = max(x2 - x1, min_side), max(y2 - y1, min_side)
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    hw, hh = bw * (1 + 2 * pad) / 2, bh * (1 + 2 * pad) / 2
    return frame[max(0, int(cy - hh)):min(h, int(cy + hh)), max(0, int(cx - hw)):min(w, int(cx + hw))].copy()


def iou(a: tuple, b: tuple) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union else 0.0


@dataclass
class Entry:
    camera: str
    box: tuple[int, int, int, int]
    emb: np.ndarray
    incident: bool                   # Hafnia's verdict: something to report (True) or nothing (False)
    label: str = ""
    t: float = 0.0


@dataclass
class VerdictMemory:
    reject_sim: float = 0.85         # this similar to a rejected change at the same spot: do not ask again
    min_iou: float = 0.1             # "the same spot": boxes overlapping at least this much
    entries: list[Entry] = field(default_factory=list)

    def decide(self, camera: str, box: tuple, emb: np.ndarray) -> tuple[str, float, Entry | None]:
        """("skip" | "ask", similarity, the entry that decided)."""
        best_rej, best_conf = (0.0, None), (0.0, None)
        for e in self.entries:
            if e.camera != camera or iou(box, e.box) < self.min_iou:
                continue
            s = float(emb @ e.emb)
            if e.incident and s > best_conf[0]:
                best_conf = (s, e)
            if not e.incident and s > best_rej[0]:
                best_rej = (s, e)
        if best_rej[0] >= self.reject_sim and best_rej[0] > best_conf[0]:
            return "skip", best_rej[0], best_rej[1]
        return "ask", max(best_rej[0], best_conf[0]), None

    def add(self, entry: Entry) -> None:
        self.entries.append(entry)

    def save(self, path: Path) -> None:
        with path.open("w", encoding="utf-8") as f:
            for e in self.entries:
                f.write(json.dumps({"camera": e.camera, "box": list(e.box), "incident": e.incident, "label": e.label,
                                    "t": e.t, "emb": [round(float(v), 5) for v in e.emb]}) + "\n")

    @classmethod
    def load(cls, path: Path, **kw) -> "VerdictMemory":
        m = cls(**kw)
        for line in path.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            m.add(Entry(d["camera"], tuple(d["box"]), np.array(d["emb"], np.float32), d["incident"], d["label"], d["t"]))
        return m
