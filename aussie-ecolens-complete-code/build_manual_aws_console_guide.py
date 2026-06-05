from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

OUT = "Aussie_EcoLens_AWS_Console_HD_Implementation_Guide.docx"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_text(cell, text, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(9)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER


def add_table(doc, headers, rows, widths=None):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.autofit = False
    for i, header in enumerate(headers):
        set_cell_text(table.rows[0].cells[i], header, bold=True)
        set_cell_shading(table.rows[0].cells[i], "E6F0ED")
        if widths:
            table.rows[0].cells[i].width = widths[i]
    for row in rows:
        cells = table.add_row().cells
        for i, value in enumerate(row):
            set_cell_text(cells[i], str(value))
            if widths:
                cells[i].width = widths[i]
    doc.add_paragraph()
    return table


def add_code(doc, text):
    p = doc.add_paragraph()
    p.style = "Code"
    for line in text.strip("\n").splitlines():
        run = p.add_run(line)
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
        run.font.color.rgb = RGBColor(31, 45, 51)
        p.add_run("\n")


def add_check(doc, text):
    p = doc.add_paragraph(style="List Bullet")
    p.add_run(text)


def add_step(doc, number, text):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.28)
    p.paragraph_format.first_line_indent = Inches(-0.28)
    marker = p.add_run(f"{number}. ")
    marker.bold = True
    marker.font.color.rgb = RGBColor.from_string("15594D")
    p.add_run(text)


def setup_styles(doc):
    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.08

    for style_name, size, color in [
        ("Title", 24, "14211E"),
        ("Heading 1", 16, "15594D"),
        ("Heading 2", 12.5, "176B7C"),
        ("Heading 3", 11.2, "24413B"),
    ]:
        style = styles[style_name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor.from_string(color)
        style.font.bold = True
        style.paragraph_format.space_before = Pt(10 if "Heading" in style_name else 0)
        style.paragraph_format.space_after = Pt(5)

    code = styles.add_style("Code", 1)
    code.font.name = "Consolas"
    code.font.size = Pt(8.5)
    code.paragraph_format.space_before = Pt(3)
    code.paragraph_format.space_after = Pt(6)
    code.paragraph_format.left_indent = Inches(0.18)


def build():
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(0.75)
    section.left_margin = Inches(0.72)
    section.right_margin = Inches(0.72)
    setup_styles(doc)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.add_run("Aussie EcoLens AWS Console HD Implementation Guide")
    subtitle = doc.add_paragraph()
    subtitle.add_run("Manual AWS setup for Cognito, S3, Lambda inline code, API Gateway, SNS, and deployment checks.").bold = True
    doc.add_paragraph("Use this guide when you want to paste Lambda source manually in the AWS console instead of deploying one zip per Lambda function. A shared Lambda Layer is still required for third-party Python packages; AWS inline code cannot import Google Cloud client libraries without a layer.")

    doc.add_heading("1. Target Architecture", level=1)
    add_check(doc, "AWS Cognito protects the React UI and every REST API route using a JWT authorizer.")
    add_check(doc, "S3 receives browser uploads using presigned PUT URLs and emits ObjectCreated events.")
    add_check(doc, "Lambda presign_upload reserves SHA-256 checksums before upload to prevent duplicate storage.")
    add_check(doc, "Lambda ingest_dispatcher copies the S3 object to GCP Cloud Storage and publishes a Pub/Sub processing job.")
    add_check(doc, "GCP Cloud Run creates thumbnails, extracts 1 frame per second for videos, runs the ML model, writes Firestore metadata, and triggers tag notifications.")
    add_check(doc, "API Gateway routes query, thumbnail lookup, query-by-file, bulk tag editing, delete, and notification watch operations.")

    doc.add_heading("2. Manual Console Values To Prepare", level=1)
    add_table(
        doc,
        ["Value", "Example", "Where used"],
        [
            ["AWS region", "ap-southeast-2", "Cognito, S3, Lambda, API Gateway, SNS"],
            ["S3 upload bucket", "fit5225-aussie-ecolens-uploads", "UPLOAD_BUCKET"],
            ["GCP project id", "your-gcp-project-id", "GCP_PROJECT_ID"],
            ["GCP processing bucket", "fit5225-aussie-ecolens-processing", "GCP_BUCKET"],
            ["Pub/Sub topic", "projects/PROJECT/topics/media-processing", "PUBSUB_TOPIC"],
            ["Frontend origin", "http://localhost:5174 or deployed HTTPS URL", "CORS_ORIGIN and S3 CORS"],
            ["Cloud Run query endpoint", "https://.../query-file", "QUERY_FILE_PROCESSOR_URL"],
        ],
        [Inches(1.55), Inches(2.7), Inches(2.1)],
    )

    doc.add_heading("3. Cognito Setup", level=1)
    for i, step in enumerate([
        "Open AWS Cognito, create a User Pool, and choose email sign-in.",
        "Required attributes: email, given_name, family_name. Keep email verification enabled.",
        "Create an app client for a single-page application. Do not create a client secret.",
        "Record the User Pool ID and Client ID for frontend .env and API Gateway JWT authorizer.",
        "In the frontend, set VITE_COGNITO_USER_POOL_ID and VITE_COGNITO_CLIENT_ID.",
    ], start=1):
        add_step(doc, i, step)

    doc.add_heading("4. S3 Upload Bucket", level=1)
    for i, step in enumerate([
        "Create the upload bucket and block all public access.",
        "Enable server-side encryption with SSE-S3.",
        "Add CORS allowing PUT and GET from your frontend origin.",
        "Do not make uploaded objects public. The app uses presigned URLs and GCP signed URLs.",
    ], start=1):
        add_step(doc, i, step)
    add_code(doc, """
[
  {
    "AllowedHeaders": ["*"],
    "AllowedMethods": ["PUT", "GET"],
    "AllowedOrigins": ["https://YOUR_FRONTEND_DOMAIN"],
    "ExposeHeaders": ["ETag"],
    "MaxAgeSeconds": 3000
  }
]
""")

    doc.add_heading("5. Shared Lambda Dependency Layer", level=1)
    doc.add_paragraph("Manual inline Lambda code can only import the Python standard library and runtime-included AWS SDK packages. These functions also import Google Cloud SDK packages and requests, so create one shared layer and attach it to every Python Lambda.")
    for i, step in enumerate([
        "Open AWS CloudShell in the same region.",
        "Run the commands below to build a Python 3.12 compatible layer.",
        "In Lambda, create a layer named aussie-ecolens-python-deps from layer.zip.",
        "Attach the layer to all six Lambda functions.",
    ], start=1):
        add_step(doc, i, step)
    add_code(doc, """
mkdir -p layer/python
python3 -m pip install -t layer/python boto3 google-cloud-firestore google-cloud-storage google-cloud-pubsub google-auth requests
cd layer
zip -r ../layer.zip python
""")

    doc.add_heading("6. IAM Role For Lambda", level=1)
    doc.add_paragraph("Create one execution role for all functions for coursework simplicity. For a stricter HD explanation, mention that production would split these permissions per function.")
    add_code(doc, """
Logs:
  AWSLambdaBasicExecutionRole

Inline policy:
  s3:GetObject, s3:PutObject, s3:DeleteObject, s3:HeadObject on arn:aws:s3:::YOUR_UPLOAD_BUCKET/*
  secretsmanager:GetSecretValue on the GCP service-account secret ARN
  sns:CreateTopic, sns:Publish, sns:Subscribe, sns:Unsubscribe on arn:aws:sns:REGION:ACCOUNT_ID:aussie-ecolens-*
""")

    doc.add_heading("7. Store GCP Service Account In AWS Secrets Manager", level=1)
    for i, step in enumerate([
        "In GCP, create a service account for AWS dispatcher/API access.",
        "Grant it Storage Object Admin on the GCP processing bucket, Datastore User for Firestore, and Pub/Sub Publisher on the media-processing topic.",
        "Download the JSON key.",
        "In AWS Secrets Manager, create a secret named gcp-firestore-service-account and paste the full JSON as plaintext.",
    ], start=1):
        add_step(doc, i, step)

    doc.add_heading("8. Create Lambda Functions Manually", level=1)
    doc.add_paragraph("Create each Lambda in the AWS console with runtime Python 3.12, architecture x86_64, handler handler.handler, the shared IAM role, and the shared dependency layer. In the inline editor, create handler.py for the function handler and a common folder containing the four common helper files.")
    add_table(
        doc,
        ["Lambda", "Local handler source", "Timeout", "Memory"],
        [
            ["presign_upload", "aws/lambdas/presign_upload/handler.py", "60 s", "512 MB"],
            ["ingest_dispatcher", "aws/lambdas/ingest_dispatcher/handler.py", "300 s", "1024 MB"],
            ["query_api", "aws/lambdas/query_api/handler.py", "60 s", "512 MB"],
            ["tag_api", "aws/lambdas/tag_api/handler.py", "60 s", "512 MB"],
            ["delete_api", "aws/lambdas/delete_api/handler.py", "60 s", "512 MB"],
            ["notification_api", "aws/lambdas/notification_api/handler.py", "60 s", "512 MB"],
        ],
        [Inches(1.3), Inches(3.3), Inches(0.75), Inches(0.75)],
    )
    doc.add_paragraph("Common files to create under each Lambda's common/ folder:")
    for file in [
        "aws/lambdas/common/auth.py",
        "aws/lambdas/common/gcp.py",
        "aws/lambdas/common/response.py",
        "aws/lambdas/common/storage.py",
    ]:
        add_check(doc, file)

    doc.add_heading("9. Lambda Environment Variables", level=1)
    add_table(
        doc,
        ["Variable", "Value"],
        [
            ["UPLOAD_BUCKET", "Your S3 upload bucket"],
            ["GCP_SECRET_ID", "gcp-firestore-service-account"],
            ["GCP_BUCKET", "Your GCP processing bucket"],
            ["GCP_PROJECT_ID", "Your GCP project id"],
            ["PUBSUB_TOPIC", "projects/PROJECT/topics/media-processing"],
            ["CORS_ORIGIN", "Your frontend origin"],
            ["AWS_REGION", "ap-southeast-2"],
            ["SNS_TOPIC_PREFIX", "arn:aws:sns:REGION:ACCOUNT_ID:aussie-ecolens-"],
            ["QUERY_FILE_PROCESSOR_URL", "Cloud Run URL ending in /query-file; required on query_api"],
        ],
        [Inches(2.0), Inches(4.2)],
    )

    doc.add_heading("10. S3 Trigger", level=1)
    for i, step in enumerate([
        "Open the S3 upload bucket, Properties, Event notifications.",
        "Create event name ingest-dispatcher-trigger.",
        "Prefix: uploads/. Event type: All object create events.",
        "Destination: Lambda function ingest_dispatcher.",
        "If AWS asks for permission, allow S3 to invoke the Lambda.",
    ], start=1):
        add_step(doc, i, step)

    doc.add_heading("11. API Gateway HTTP API", level=1)
    for i, step in enumerate([
        "Create an HTTP API.",
        "Create Lambda integrations for presign_upload, query_api, tag_api, delete_api, and notification_api.",
        "Create a JWT authorizer using Cognito issuer https://cognito-idp.REGION.amazonaws.com/USER_POOL_ID and audience CLIENT_ID.",
        "Attach the JWT authorizer to every route below. Do not leave routes public.",
        "Enable CORS for Authorization and Content-Type headers from your frontend origin.",
    ], start=1):
        add_step(doc, i, step)
    add_table(
        doc,
        ["Route", "Lambda integration", "Purpose"],
        [
            ["POST /uploads/presign", "presign_upload", "Checksum dedupe and presigned S3 upload"],
            ["GET /media/{mediaId}", "query_api", "Poll upload processing status"],
            ["POST /query/tags", "query_api", "AND query with minimum tag counts"],
            ["POST /query/species", "query_api", "Species query without counts"],
            ["POST /query/thumbnail", "query_api", "Thumbnail URL to full image URL"],
            ["POST /query/file", "query_api", "Temporary uploaded query image"],
            ["POST /media/tags/bulk", "tag_api", "Bulk add/remove tags"],
            ["POST /media/delete", "delete_api", "Delete media, thumbnails, indexes, DB rows"],
            ["POST /notifications/watch", "notification_api", "Create tag email watch"],
            ["POST /notifications/unwatch", "notification_api", "Disable tag watch"],
        ],
        [Inches(2.0), Inches(1.6), Inches(2.8)],
    )

    doc.add_heading("12. SNS Notifications", level=1)
    add_check(doc, "notification_api creates SNS topics idempotently for watched tags using the configured SNS_TOPIC_PREFIX.")
    add_check(doc, "Users must confirm the SNS subscription email before notifications can arrive.")
    add_check(doc, "Cloud Run can publish directly to SNS if AWS credentials are configured, or call an AWS notification endpoint if you choose that variant.")

    doc.add_heading("13. Frontend Deployment", level=1)
    add_code(doc, """
cd frontend
cp ../.env.example .env
# Set VITE_COGNITO_USER_POOL_ID, VITE_COGNITO_CLIENT_ID, VITE_API_BASE_URL
npm install
npm run build
""")
    add_check(doc, "For demo, you can run npm run dev -- --host 127.0.0.1 --port 5173.")
    add_check(doc, "For hosted demo, deploy frontend/dist through Amplify Hosting or S3 + CloudFront.")

    doc.add_heading("14. HD Demo Test Order", level=1)
    for i, step in enumerate([
        "Create a new Cognito user with email, first name, last name, and password. Verify email.",
        "Sign in and confirm unauthenticated users cannot call API Gateway routes.",
        "Upload a test image. Show checksum calculation, successful presign, S3 upload, status polling, and READY result.",
        "Upload the same file again. Show duplicate blocked before upload storage is wasted.",
        "Upload a video. Explain 1 frame per second extraction in Cloud Run.",
        "Run tag count query such as felis_catus:1 and a multi-tag AND query.",
        "Run species query, thumbnail URL query, and query-by-file.",
        "Select multiple results, bulk add a tag, bulk remove a tag, then delete selected media.",
        "Create a watch for a tag and confirm SNS subscription email.",
    ], start=1):
        add_step(doc, i, step)

    doc.add_heading("15. Common Demo Failures And Fixes", level=1)
    add_table(
        doc,
        ["Symptom", "Likely cause", "Fix"],
        [
            ["401/403 from API", "JWT authorizer missing or wrong audience", "Check Cognito Client ID and Authorization header"],
            ["Lambda cannot import google.cloud", "Layer missing", "Attach shared dependency layer to every Lambda"],
            ["S3 upload CORS error", "Frontend origin not allowed", "Update bucket CORS and API CORS"],
            ["Query by file fails", "QUERY_FILE_PROCESSOR_URL missing", "Set Cloud Run /query-file URL on query_api"],
            ["No processing after upload", "S3 trigger missing or metadata absent", "Check ObjectCreated trigger and presign metadata"],
            ["SNS watch creates no email", "Subscription not confirmed", "Open email and confirm subscription"],
        ],
        [Inches(1.75), Inches(2.2), Inches(2.3)],
    )

    doc.add_heading("16. Final Marking Checklist", level=1)
    for item in [
        "Cognito sign-up, email verification, sign-in, and sign-out work.",
        "All API Gateway routes are JWT-protected.",
        "S3 bucket is private, encrypted, and CORS-configured.",
        "All six Lambda functions use handler.handler and include common helper files.",
        "Shared dependency layer is attached to all Lambdas.",
        "Checksum dedupe blocks repeated uploads.",
        "Cloud Run writes tags, file type, full URL, thumbnail URL, and status to Firestore.",
        "Queries implement logical AND with minimum counts.",
        "Bulk tag edit, delete, thumbnail lookup, query-by-file, and notifications are demo-ready.",
    ]:
        add_check(doc, item)

    doc.add_page_break()
    doc.add_heading("Appendix A. Local Files To Copy Into AWS Console", level=1)
    doc.add_paragraph("Paste these files from your workspace into the Lambda console. Use the exact filenames and folder names shown.")
    add_table(
        doc,
        ["Console path", "Workspace source"],
        [
            ["handler.py", "aws/lambdas/presign_upload/handler.py"],
            ["handler.py", "aws/lambdas/ingest_dispatcher/handler.py"],
            ["handler.py", "aws/lambdas/query_api/handler.py"],
            ["handler.py", "aws/lambdas/tag_api/handler.py"],
            ["handler.py", "aws/lambdas/delete_api/handler.py"],
            ["handler.py", "aws/lambdas/notification_api/handler.py"],
            ["common/auth.py", "aws/lambdas/common/auth.py"],
            ["common/gcp.py", "aws/lambdas/common/gcp.py"],
            ["common/response.py", "aws/lambdas/common/response.py"],
            ["common/storage.py", "aws/lambdas/common/storage.py"],
        ],
        [Inches(2.0), Inches(4.2)],
    )

    doc.core_properties.title = "Aussie EcoLens AWS Console HD Implementation Guide"
    doc.core_properties.subject = "FIT5225 Assignment 2 AWS manual setup guide"
    doc.save(OUT)


if __name__ == "__main__":
    build()
