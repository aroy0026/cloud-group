# Model Files

Required model files for Docker build:

- `model.pt`
- `mdv5a.pt`
- `labels.txt`

`labels.txt` is included here. The two `.pt` files are already present in:

```text
aussie-ecolens-complete-code/gcp/cloudrun_processor/
```

They are not duplicated into `gcp-cloudrun/` to avoid adding hundreds of megabytes twice.

Before building from this folder:

```bash
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/model.pt ./model.pt
cp ../aussie-ecolens-complete-code/gcp/cloudrun_processor/mdv5a.pt ./mdv5a.pt
```

