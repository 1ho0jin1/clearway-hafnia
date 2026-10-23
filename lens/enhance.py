"""Super-resolution for the lens: enlarge the cropped spot with a learned upscaler instead of plain interpolation.

Hafnia samples a few frames per second from each clip and, at a clip's full frame, a distant road user is a handful
of pixels (the crashed SUV of test_11: about 30 px long). Cropping and enlarging helped there
(run/lens-test_11-20261021T144445Z). Plain bicubic enlargement only blurs; a super-resolution model restores edges.
It can also invent texture that was never there, which is why every use is measured against bicubic on the same
crops (plan C, M1) before it goes into the product.

Real-ESRGAN (Wang, Xie, Dong, Shan, "Real-ESRGAN: Training Real-World Blind Super-Resolution with Pure Synthetic
Data", ICCV workshops 2021; code and weights BSD-3-Clause), loaded with spandrel (MIT), so no basicsr. Two models:
- "general": realesr-general-x4v3, a compact network (about 1.2 M parameters) for video; the default.
- "x4plus": RealESRGAN_x4plus, the large RRDB network (about 16.7 M parameters); sharper, slower.
Weights download on first use into models/realesrgan (git-ignored) and are checked against their SHA-256.
"""
from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
WEIGHTS = REPO / "models" / "realesrgan"
MODELS = {
    "general": ("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesr-general-x4v3.pth",
                "8dc7edb9ac80ccdc30c3a5dca6616509367f05fbc184ad95b731f05bece96292"),
    "x4plus": ("https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth",
               "4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1"),
}


def weights(name: str) -> Path:
    url, sha = MODELS[name]
    path = WEIGHTS / url.rsplit("/", 1)[1]
    if not path.exists():
        WEIGHTS.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != sha:
        raise RuntimeError(f"{path.name}: SHA-256 {digest} does not match {sha}; delete it and try again")
    return path


class SuperRes:
    """4x super-resolution of BGR uint8 images on the GPU (fp16 where the model allows)."""

    def __init__(self, name: str = "general", device: str = "cuda"):
        import torch
        from spandrel import ModelLoader
        self.torch = torch
        self.device = device
        self.model = ModelLoader().load_from_file(str(weights(name))).to(device).eval()
        self.half = bool(self.model.supports_half)
        if self.half:
            self.model.model.half()
        self.scale = self.model.scale

    def upscale(self, img: np.ndarray) -> np.ndarray:
        t = self.torch.from_numpy(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).to(self.device)
        t = t.permute(2, 0, 1)[None].float().div(255)
        if self.half:
            t = t.half()
        with self.torch.no_grad():
            out = self.model(t)
        out = out[0].float().clamp(0, 1).mul(255).round().byte().permute(1, 2, 0).cpu().numpy()
        return cv2.cvtColor(out, cv2.COLOR_RGB2BGR)

    def upscale_all(self, frames: list[np.ndarray]) -> list[np.ndarray]:
        return [self.upscale(f) for f in frames]


def bicubic(frames: list[np.ndarray], scale: int = 4) -> list[np.ndarray]:
    """The baseline every super-resolution result is compared with."""
    return [cv2.resize(f, (f.shape[1] * scale, f.shape[0] * scale), interpolation=cv2.INTER_CUBIC) for f in frames]
