# Model Files

Required model files for Docker build:

- `model.pt`
- `mdv5a.pt`
- `labels.txt`

This rebuild folder should contain all three files before deployment. The `.pt` files are large binary assets, so they are ignored by git even when present locally.

If they are missing after cloning from git, copy them from the original model folder or shared project archive:

```bash
cp ../../AussieEcoLense/model.pt ./model.pt
cp ../../AussieEcoLense/mdv5a.pt ./mdv5a.pt
```

If you are using only the `project-from-scratch` folder, make sure `model.pt` and `mdv5a.pt` are copied into this `gcp-cloudrun/` directory before running `./deploy.sh`.
