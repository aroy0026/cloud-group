# AWS S3 Bucket Setup
## EcoLens — Day 1, Phase 2

---

## S3 Config Reference

```
Bucket Name:   ecolens-media-savio-melbourne
Region:        ap-southeast-4
ARN:           arn:aws:s3:::ecolens-media-savio-melbourne
Public Access: Enabled
Folders:       uploads/ thumbnails/ models/
```

---

## What This Does

S3 stores all uploaded media files (images and videos), generated thumbnails,
and ML model files. The bucket is publicly readable so uploaded files can be
viewed directly via URL without AWS credentials.

---

## Step 1 — Create the Bucket

```powershell
aws s3api create-bucket `
  --bucket ecolens-media-savio-melbourne `
  --region ap-southeast-4 `
  --create-bucket-configuration LocationConstraint=ap-southeast-4
```

> S3 bucket names are globally unique across all AWS accounts.

---

## Step 2 — Disable Block Public Access

By default AWS blocks all public access on new buckets. This lifts all
four restrictions so the bucket policy can make files publicly readable.

```powershell
aws s3api put-public-access-block `
  --bucket ecolens-media-savio-melbourne `
  --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

---

## Step 3 — Attach Public Read Policy

Allows anyone on the internet to read (GET) any object in the bucket.
This is what makes uploaded wildlife images viewable via direct URL.

```powershell
aws s3api put-bucket-policy `
  --bucket ecolens-media-savio-melbourne `
  --policy '{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"PublicReadGetObject\",\"Effect\":\"Allow\",\"Principal\":\"*\",\"Action\":\"s3:GetObject\",\"Resource\":\"arn:aws:s3:::ecolens-media-savio-melbourne/*\"}]}'
```

---

## Step 4 — Create Folder Structure

S3 has no real folders — it is a flat key-value store. These are empty
placeholder objects ending with `/` that simulate folders in the console.

```powershell
aws s3api put-object --bucket ecolens-media-savio-melbourne --key uploads/
aws s3api put-object --bucket ecolens-media-savio-melbourne --key thumbnails/
aws s3api put-object --bucket ecolens-media-savio-melbourne --key models/
```

| Folder       | Purpose                          |
|--------------|----------------------------------|
| uploads/     | Original uploaded images/videos  |
| thumbnails/  | Auto-generated thumbnail images  |
| models/      | GCP ML model files               |

---

## Verification

```powershell
aws s3 ls s3://ecolens-media-savio-melbourne/
```

Expected output:
```
PRE models/
PRE thumbnails/
PRE uploads/
```

---

## Checklist

```
☑ Bucket created (ecolens-media-savio-melbourne) in ap-southeast-4
☑ Block public access disabled
☑ Public read bucket policy attached
☑ uploads/ folder created
☑ thumbnails/ folder created
☑ models/ folder created
☑ Verified via aws s3 ls
```
