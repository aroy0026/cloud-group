# Packaging Lambdas

Each Lambda needs:

- Its own `handler.py`
- The `common/` folder
- Dependencies from `aws/lambdas/requirements.txt`

Example:

```bash
mkdir -p build/presign_upload
cp -R aws/lambdas/common build/presign_upload/common
cp aws/lambdas/presign_upload/handler.py build/presign_upload/handler.py
python -m pip install -r aws/lambdas/requirements.txt -t build/presign_upload
cd build/presign_upload
zip -r ../presign_upload.zip .
```

Upload the ZIP to Lambda. Repeat for the other handlers.

