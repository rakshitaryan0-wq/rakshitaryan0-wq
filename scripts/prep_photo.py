#!/usr/bin/env python3
"""
prep_photo.py — one-time photo preparation for the ASCII portrait.

Pipeline:
  1. Isolate the subject from the background using OpenCV GrabCut
     (no model downloads needed, unlike rembg).
  2. Boost local contrast with CLAHE so a flatly-lit face gets real
     highlights and shadows.
  3. Composite onto pure white so the background maps to the blank
     end of the ASCII ramp (white -> spaces).

Usage:
    python scripts/prep_photo.py source-photo.png
Output:
    source-prepped.png  (grayscale)
"""
import sys

import cv2
import numpy as np


def remove_background(img_bgr: np.ndarray) -> np.ndarray:
    """Return a 0..1 float mask of the foreground subject via GrabCut.

    Uses mask-seeded GrabCut (not a plain rectangle) because when skin
    tones are close to the background color, a rectangle-only init eats
    into the face. Seeds tuned for a centered head-and-shoulders portrait.
    """
    h, w = img_bgr.shape[:2]
    mask = np.full((h, w), cv2.GC_PR_BGD, np.uint8)

    # Probable foreground: generous center region.
    cv2.rectangle(mask, (int(w*0.24), int(h*0.04)), (int(w*0.80), h-1),
                  cv2.GC_PR_FGD, -1)
    # Definite foreground: face ellipse + torso block.
    cv2.ellipse(mask, (int(w*0.50), int(h*0.40)),
                (int(w*0.11), int(h*0.28)), 0, 0, 360, cv2.GC_FGD, -1)
    cv2.rectangle(mask, (int(w*0.30), int(h*0.72)), (int(w*0.78), h-1),
                  cv2.GC_FGD, -1)

    # Definite background: edge strips (skip bottom, shoulders reach edges)
    mask[0:int(h*0.03), :] = cv2.GC_BGD
    mask[0:int(h*0.55), 0:int(w*0.10)] = cv2.GC_BGD
    mask[:, 0:int(w*0.06)] = cv2.GC_BGD
    mask[0:int(h*0.52), int(w*0.72):w] = cv2.GC_BGD
    # Wall patch left of the ear — probable bg, let GrabCut find the edge.
    mask[int(h*0.22):int(h*0.42), int(w*0.28):int(w*0.355)] = cv2.GC_PR_BGD

    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)
    cv2.grabCut(img_bgr, mask, None, bgd_model, fgd_model, 10,
                cv2.GC_INIT_WITH_MASK)

    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0)
    fg = fg.astype(np.float32)

    # Keep only the largest connected component (drops stray blobs).
    n, lab = cv2.connectedComponents((fg > 0.5).astype(np.uint8))
    if n > 1:
        sizes = [(lab == i).sum() for i in range(1, n)]
        keep = 1 + int(np.argmax(sizes))
        fg = (lab == keep).astype(np.float32)

    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    # Feather the mask edge slightly so hair doesn't get a hard cutout line.
    fg = cv2.GaussianBlur(fg, (7, 7), 0)
    return fg


def enhance_contrast(gray: np.ndarray) -> np.ndarray:
    """CLAHE — contrast-limited adaptive histogram equalization."""
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    return clahe.apply(gray)


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "source-photo.png"
    img = cv2.imread(src, cv2.IMREAD_COLOR)
    if img is None:
        sys.exit(f"could not read {src}")

    fg_mask = remove_background(img)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = enhance_contrast(gray)

    # Composite onto pure white: background -> 255 (maps to spaces).
    white = np.full_like(gray, 255, dtype=np.uint8)
    out = (gray.astype(np.float32) * fg_mask
           + white.astype(np.float32) * (1.0 - fg_mask))
    out = np.clip(out, 0, 255).astype(np.uint8)

    cv2.imwrite("source-prepped.png", out)
    print("wrote source-prepped.png", out.shape)


if __name__ == "__main__":
    main()
