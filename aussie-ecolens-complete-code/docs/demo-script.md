# Demo Script

1. Show architecture diagram and explain AWS/GCP split.
2. Log out and try a protected action. Confirm blocked/redirected.
3. Sign in with Cognito.
4. Upload one image from `test_images`.
5. Show status changing from PRESIGNED/QUEUED/PROCESSING to READY.
6. Upload the same file again. Show duplicate detection.
7. Query by species, e.g. `felis_catus`.
8. Query by count, e.g. `felis_catus:1`.
9. Click/open full image from thumbnail.
10. Query by file with a temporary image. State it is not stored.
11. Select results and bulk add tag `reviewed`.
12. Remove tag `reviewed`.
13. Watch tag `dingo`, confirm SNS subscription, upload matching file, show email.
14. Delete one selected result and show DB/storage cleanup.
15. Open CloudWatch and Cloud Run logs if asked.

