import os
import io
import json
import uuid
import base64
import tempfile
import warnings

warnings.filterwarnings("ignore")

import boto3
import torch
import torchvision.transforms as transforms
from PIL import Image
import numpy as np
from flask import Flask, request, jsonify
from google.cloud import storage
from pathlib import Path

app = Flask(__name__)

# Configuration
GCS_BUCKET = "ecolens-media-savio-v2"
AWS_REGION = "ap-southeast-4"
DYNAMODB_TABLE = "ecolens-media"
S3_BUCKET = "ecolens-media-savio-melbourne"

# Device setup
if torch.cuda.is_available():
    DEVICE = "cuda"
elif torch.backends.mps.is_available():
    DEVICE = "mps"
else:
    DEVICE = "cpu"

print("Using device:", DEVICE)

# Supported species classes
CLASSES = [
    "Alectura_lathami",
    "Antechinus_agilis",
    "Bos_taurus",
    "Burhinus_grallarius",
    "Canis_familiaris",
    "Chalcophaps_longirostris",
    "Colluricincla_harmonica",
    "Corcorax_melanorhamphos",
    "Dacelo_novaeguineae",
    "Dama_dama",
    "Eopsaltria_australis",
    "Felis_catus",
    "Geopelia_humeralis",
    "Gymnorhina_tibicen",
    "Homo_sapiens",
    "Isoodon_macrourus",
    "Lepus_europaeus",
    "Macropus_giganteus",
    "Menura_novaehollandiae",
    "Mus_musculus",
    "Oryctolagus_cuniculus",
    "Perameles_nasuta",
    "Pitta_versicolor",
    "Rattus",
    "Rattus_fuscipes",
    "Rattus_rattus",
    "Strepera_graculina",
    "Sus_scrofa",
    "Tachyglossus_aculeatus",
    "Thylogale_stigmatica",
    "Trichosurus_caninus",
    "Trichosurus_cunninghami",
    "Trichosurus_vulpecula",
    "Varanus_varius",
    "Vombatus_ursinus",
    "Vulpes_vulpes",
    "Wallabia_bicolor",
    "Canis_dingo",
    "Capra_hircus",
    "Casuarius_casuarius",
    "Heteromyias_cinereifrons",
    "Hypsiprymnodon_moschatus",
    "Megapodius_reinwardt",
    "Notamacropus_rufogriseus",
    "Orthonyx_spaldingii",
    "Uromys_caudimaculatus",
]

# Global model variables
megadetector_model = None
species_model = None

# Video extensions
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}


def is_video(s3_key):
    """Check if the S3 key refers to a video file"""
    ext = os.path.splitext(s3_key.lower())[1]
    return ext in VIDEO_EXTENSIONS or 'uploads/videos/' in s3_key


def download_model_from_gcs(blob_name, local_path):
    """Download model file from GCS if not already present"""
    if os.path.exists(local_path):
        print(f"Model already exists at {local_path}")
        return
    print(f"Downloading {blob_name} from GCS...")
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(blob_name)
    blob.download_to_filename(local_path)
    print(f"Downloaded {blob_name} to {local_path}")


def load_models():
    """Load both models into memory"""
    global megadetector_model, species_model

    os.makedirs("/tmp/models", exist_ok=True)

    download_model_from_gcs("models/mdv5a.pt", "/tmp/models/mdv5a.pt")
    download_model_from_gcs("models/model.pt", "/tmp/models/model.pt")

    if megadetector_model is None:
        print("Loading MegaDetector...")
        from megadetector.detection import run_detector_batch
        megadetector_model = run_detector_batch
        print("MegaDetector loaded")

    if species_model is None:
        print("Loading SpeciesNet...")
        species_model = torch.load(
            "/tmp/models/model.pt", map_location=DEVICE, weights_only=False
        )
        species_model.eval()
        species_model.to(DEVICE)
        print("SpeciesNet loaded")


def run_megadetector(image_path):
    """Run MegaDetector on image and return detections"""
    from megadetector.detection import run_detector_batch
    results = run_detector_batch.load_and_run_detector_batch(
        image_file_names=[image_path], model_file="/tmp/models/mdv5a.pt"
    )
    return results[0] if results else None


def crop_detections(image_path, detections, conf_threshold=0.05):
    """Crop detected animals from image"""
    crops = []
    img = Image.open(image_path).convert("RGB")
    W, H = img.size

    for detection in detections.get("detections", []):
        if detection["category"] != "1":
            continue
        if detection["conf"] < conf_threshold:
            continue

        x, y, w, h = detection["bbox"]
        left = int(x * W)
        top = int(y * H)
        right = int((x + w) * W)
        bottom = int((y + h) * H)

        crop = img.crop((left, top, right, bottom))
        crop = crop.resize((600, 600), Image.BILINEAR)
        crops.append(crop)

    return crops


@torch.no_grad()
def classify_crop(crop_image):
    """Classify a cropped animal image"""
    transform = transforms.Compose([
        transforms.Resize((480, 480)),
        transforms.ToTensor(),
    ])

    img = transform(crop_image)
    img = img.unsqueeze(0)
    img = img.permute(0, 2, 3, 1)
    img = img.to(DEVICE)

    logits = species_model(img)
    probs = torch.softmax(logits, dim=1)[0].cpu().numpy()

    best_idx = np.argmax(probs)
    return CLASSES[best_idx], float(probs[best_idx])


def process_image(image_path):
    """Full ML pipeline for a single image: detect + classify"""
    tags = {}

    print("Running MegaDetector...")
    detections = run_megadetector(image_path)

    if not detections:
        print("No detections found")
        return tags

    print(f"Found {len(detections.get('detections', []))} detections")
    crops = crop_detections(image_path, detections)
    print(f"Processing {len(crops)} animal crops...")

    for crop in crops:
        species, confidence = classify_crop(crop)
        if confidence > 0.3:
            tags[species] = tags.get(species, 0) + 1
            print(f"Detected: {species} ({confidence:.3f})")

    return tags


def extract_frames(video_path):
    """Extract 1 frame per second from a video"""
    import cv2

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"Video: {total_frames} frames at {fps:.1f} fps")

    if fps <= 0:
        fps = 25  # fallback

    # Extract 1 frame per second
    frame_indices = [int(i * fps) for i in range(int(total_frames / fps))]

    frames = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)

    cap.release()
    print(f"Extracted {len(frames)} frames (1 per second)")
    return frames


def frame_to_pil(frame_array):
    """Convert numpy frame array to PIL Image"""
    return Image.fromarray(frame_array)


def frame_to_base64(frame_array):
    """Convert numpy frame array to base64 JPEG string"""
    pil_img = frame_to_pil(frame_array)
    buffer = io.BytesIO()
    pil_img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def process_video(video_path):
    """
    Full ML pipeline for video:
    - Extract frames
    - Run ML on each frame
    - Take MAX count per species across all frames
    - Return combined tags + first frame as base64 thumbnail
    """
    frames = extract_frames(video_path)

    if not frames:
        print("No frames extracted from video")
        return {}, None

    # First frame as thumbnail
    thumbnail_base64 = frame_to_base64(frames[0])

    # Run ML on each frame and collect tags
    all_frame_tags = []
    for i, frame in enumerate(frames):
        print(f"Processing frame {i+1}/{len(frames)}...")
        # Save frame to temp file for MegaDetector
        temp_path = f"/tmp/frame_{i}.jpg"
        pil_img = frame_to_pil(frame)
        pil_img.save(temp_path, format='JPEG')

        frame_tags = process_image(temp_path)
        print(f"Frame {i+1} tags: {frame_tags}")
        all_frame_tags.append(frame_tags)

        # Cleanup temp frame
        try:
            os.remove(temp_path)
        except:
            pass

    # Combine tags — take MAX count per species across all frames
    combined_tags = {}
    for frame_tags in all_frame_tags:
        for species, count in frame_tags.items():
            combined_tags[species] = max(combined_tags.get(species, 0), count)

    print(f"Combined video tags: {combined_tags}")
    return combined_tags, thumbnail_base64


def update_dynamodb(file_id, tags, thumbnail_url=None):
    """Update DynamoDB record with detected tags"""
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(DYNAMODB_TABLE)

    update_expr = "SET tags = :t, #s = :s"
    expr_values = {":t": tags, ":s": "ready"}

    if thumbnail_url:
        update_expr += ", thumbnail_url = :thumb"
        expr_values[":thumb"] = thumbnail_url

    table.update_item(
        Key={"file_id": file_id},
        UpdateExpression=update_expr,
        ExpressionAttributeValues=expr_values,
        ExpressionAttributeNames={"#s": "status"},
    )
    print(f"DynamoDB updated for file_id: {file_id}")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/tag", methods=["POST"])
def tag_image():
    try:
        data = request.get_json()
        print("Received request:", data)

        file_id = data.get("file_id")
        s3_key = data.get("s3_key")

        if not file_id or not s3_key:
            return jsonify({"error": "file_id and s3_key required"}), 400

        # Load models
        load_models()

        # Download file from S3
        s3 = boto3.client(
            "s3",
            region_name="ap-southeast-4",
            endpoint_url="https://s3.ap-southeast-4.amazonaws.com",
        )
        local_path = "/tmp/" + os.path.basename(s3_key)

        print(f"Downloading from S3: {s3_key}")
        s3.download_file(S3_BUCKET, s3_key, local_path)

        thumbnail_base64 = None

        if is_video(s3_key):
            # Video processing pipeline
            print("Processing as VIDEO")
            tags, thumbnail_base64 = process_video(local_path)
        else:
            # Image processing pipeline
            print("Processing as IMAGE")
            tags = process_image(local_path)

        print("Final tags:", tags)

        # Update DynamoDB (skip for temp query files)
        if not file_id.startswith('DO-NOT-SAVE-'):
            update_dynamodb(file_id, tags)

        # Cleanup
        try:
            os.remove(local_path)
        except:
            pass

        response = {
            "status": "success",
            "file_id": file_id,
            "tags": tags
        }

        # Include thumbnail for videos
        if thumbnail_base64:
            response["thumbnail_base64"] = thumbnail_base64
            response["thumbnail_content_type"] = "image/jpeg"

        return jsonify(response), 200

    except Exception as e:
        print("ERROR:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
