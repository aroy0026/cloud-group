import base64
import json

from flask import Flask, jsonify, request

from processor import detect_query_file, process_media

app = Flask(__name__)


@app.post("/")
def pubsub_push():
    envelope = request.get_json(force=True, silent=True)
    if not envelope or "message" not in envelope:
        return ("Bad Request", 400)
    payload = base64.b64decode(envelope["message"]["data"]).decode("utf-8")
    job = json.loads(payload)
    process_media(job)
    return ("", 204)


@app.post("/query-file")
def query_file():
    # Used by AWS query API. It returns detected tags only and does not persist media.
    tags = detect_query_file(request.data)
    return jsonify({"tags": tags})


@app.get("/health")
def health():
    return jsonify({"ok": True})

