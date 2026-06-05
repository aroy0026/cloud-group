import csv
import os
from pathlib import Path

import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image

MODEL_PATH = os.environ.get("MODEL_PATH", "/app/model.pt")
LABELS_PATH = os.environ.get("LABELS_PATH", "/app/labels.txt")
CONFIDENCE_THRESHOLD = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.35"))

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_classes():
    # labels.txt is semicolon-delimited. Last column is common name; genus/species are columns 5/6.
    classes = []
    if Path(LABELS_PATH).exists():
        with open(LABELS_PATH, newline="") as f:
            for row in csv.reader(f, delimiter=";"):
                if len(row) >= 6:
                    genus = (row[4] or "").strip()
                    species = (row[5] or "").strip()
                    if genus and species:
                        classes.append(f"{genus}_{species}".lower())
    return classes or [
        "alectura_lathami",
        "bos_taurus",
        "canis_familiaris",
        "felis_catus",
        "sus_scrofa",
        "thylogale_stigmatica",
        "casuarius_casuarius",
        "uromys_caudimaculatus",
    ]


CLASSES = load_classes()
MODEL = torch.load(MODEL_PATH, map_location=DEVICE, weights_only=False)
MODEL.eval().to(DEVICE)

TRANSFORM = transforms.Compose(
    [
        transforms.Resize((480, 480)),
        transforms.ToTensor(),
    ]
)


@torch.no_grad()
def detect_tags_for_image(image_path):
    image = Image.open(image_path).convert("RGB")
    tensor = TRANSFORM(image).unsqueeze(0).permute(0, 2, 3, 1).to(DEVICE)
    logits = MODEL(tensor)
    probs = torch.softmax(logits, dim=1)[0].cpu().numpy()
    order = np.argsort(probs)[::-1]

    tags = {}
    for idx in order[:3]:
        confidence = float(probs[idx])
        if confidence < CONFIDENCE_THRESHOLD:
            continue
        label = CLASSES[int(idx)] if int(idx) < len(CLASSES) else f"class_{int(idx)}"
        tags[label] = tags.get(label, 0) + 1
    return tags

