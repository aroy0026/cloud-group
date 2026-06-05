# Model Files

The clean source bundle excludes the two large model binaries:

```text
gcp/cloudrun_processor/model.pt
gcp/cloudrun_processor/mdv5a.pt
```

They are not secrets, but they are large binary artifacts and should usually stay out of Git. The original copies currently exist here:

```text
/Users/alphinroy/Projects/cloud group/aussie-ecolens-platform/gcp/cloudrun_processor/model.pt
/Users/alphinroy/Projects/cloud group/aussie-ecolens-platform/gcp/cloudrun_processor/mdv5a.pt
```

Before building the Cloud Run container, either copy them manually:

```bash
cp "/Users/alphinroy/Projects/cloud group/aussie-ecolens-platform/gcp/cloudrun_processor/model.pt" \
  "/Users/alphinroy/Projects/cloud repotr/aussie-ecolens-complete-code/gcp/cloudrun_processor/model.pt"

cp "/Users/alphinroy/Projects/cloud group/aussie-ecolens-platform/gcp/cloudrun_processor/mdv5a.pt" \
  "/Users/alphinroy/Projects/cloud repotr/aussie-ecolens-complete-code/gcp/cloudrun_processor/mdv5a.pt"
```

Or place the official assignment model folder next to this repository as `../AussieEcoLense` and run:

```bash
./scripts_prepare_models.sh
```

The model path is configurable through Cloud Run environment variables:

```text
MODEL_PATH=/app/model.pt
LABELS_PATH=/app/labels.txt
CONFIDENCE_THRESHOLD=0.35
```

To upgrade the model without source-code changes, copy the new model into the Cloud Run image, deploy a new image tag/revision, and update `MODEL_PATH` and `LABELS_PATH`.
