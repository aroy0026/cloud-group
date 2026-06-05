Design a responsive web UI for a multi‑cloud wildlife media tagging platform called “Aussie EcoLens”. The app is used by students and researchers to upload wildlife images/videos, view auto‑generated tags, run complex queries, and manage tags and notifications. The UI must look clean, professional, and easy to demo in a university assignment.

Overall style:
- Platform: Desktop‑first responsive web app (1440px width), with layouts that gracefully collapse for tablet.
- Visual style: Modern, minimal, with a nature / conservation theme. Use an earthy palette (deep green as primary, lighter greens and neutral greys as accents, white backgrounds). Avoid heavy gradients; prefer flat or very subtle shadows.
- Typography: A single modern sans‑serif family (e.g. Inter / Roboto style), clear hierarchy with H1/H2 for page titles and 14–16px body text.
- Components: Material‑style buttons, text fields, dropdowns, tabs and cards with rounded corners. Consistent spacing, alignment, and 8px spacing grid.
- Feedback: Use snackbars/toasts and inline validation messages for success, error, and warning states.

Create the following main screens:

1) Authentication screens (Sign‑up and Sign‑in)
- A centred auth card with the app logo/name “Aussie EcoLens” at the top and a short subtitle: “Multi‑cloud wildlife media tagging platform”.
- Sign‑up form fields: First name, Last name, Email, Password, Confirm password. Include clear labels, placeholders, and password help text (e.g. “At least 8 characters, with letters and numbers”).
- Sign‑in form fields: Email, Password.
- Primary actions: “Sign up” and “Sign in” buttons, plus a secondary text link to switch between sign‑up and sign‑in.
- States:
  - Default, error (e.g., invalid credentials, weak password), and loading (button with spinner).
  - A small message area where Cognito‑style messages could appear (e.g., “Please check your email to verify your account”).
- Access control hint: Include a subtle note under the forms: “You must sign in to upload media or run queries.”

2) Main application shell (after login)
- A top navigation bar containing:
  - App logo/name on the left (“Aussie EcoLens”).
  - Current user email or avatar on the right with a dropdown menu (“Profile”, “Sign out”).
- A left sidebar navigation with clear icons and labels:
  - “Dashboard”
  - “Upload media”
  - “Search media”
  - “Tags & notifications”
- The main content area should show the active page’s title and content. Include breadcrumb‑style page titles (e.g., “Search / Tags & counts”).

3) Upload media page (Auth & Upload UI – HD‑level)
- Layout:
  - Page title: “Upload media”.
  - Short description: “Upload wildlife images and videos. Duplicates are automatically detected using file checksums.”
- Components:
  - A drag‑and‑drop upload area with an icon and text like “Drop files here or click to browse”.
  - A file selector button (“Choose files”) supporting multiple selections.
  - A right‑side or bottom panel listing selected files with columns: File name, Type, Size, Status.
- Status indicators:
  - “Ready to upload”, “Calculating checksum…”, “Duplicate file detected”, “Uploading…”, “Uploaded, processing tags and thumbnails…”.
  - Use coloured badges or pill tags to show the status for each file.
- Feedback:
  - When a duplicate is detected, show an inline warning in the row (e.g., yellow badge “Duplicate – already in library”) and a toast notification at the bottom.
  - When upload succeeds, show a green toast “Upload successful. Thumbnails and tags are being generated.”
  - When upload fails, show a red toast with an error message.
- Optional: a small “Recent uploads” panel at the bottom, showing thumbnail, species tags, and upload time.

4) Search media page with tabs (Queries UI – HD‑level)
This page must be designed to support all four query types and make them visually distinct but unified.

- Layout:
  - Page title: “Search media”.
  - Tabs component with four tabs:
    1) “By tags & counts”
    2) “By species”
    3) “By thumbnail URL”
    4) “By file”
- Shared results area:
  - Below the tabs, a “Results” section showing cards in a responsive grid.
  - Each card shows:
    - Thumbnail image (for videos, a thumbnail with a small “video” icon overlay).
    - File name or ID.
    - Tag chips (e.g., “koala ×3”, “wombat ×2”).
    - File type icon (image or video).
    - A checkbox (for later bulk actions).
  - Clicking on an image thumbnail opens a full‑size image viewer modal with the larger image, tags, and metadata. For videos, show a larger thumbnail with a “Open video URL” primary button.
  - Include a “No results yet” empty state with an illustration and text: “Try adjusting your search criteria.”

4a) Tab: “By tags & counts”
- Form layout:
  - Explanatory text: “Search for media that contains all of the specified tags with minimum counts (logical AND).”
  - A dynamic list of rows with:
    - Text input for “Tag name”.
    - Numeric input for “Min count”.
    - Add/Remove row icons.
  - “Run search” primary button.
- Show example row values in placeholder text (e.g., row 1: tag “koala”, min count “3”; row 2: tag “wombat”, min count “2”).
- Include validation states if tag or min count is missing.

4b) Tab: “By species”
- Simpler form:
  - Single text input with label “Species”.
  - Placeholder example: “dingo”.
  - “Run search” button.
- Reuse the same results grid.

4c) Tab: “By thumbnail URL”
- Form:
  - Single text input labeled “Thumbnail URL”.
  - Placeholder: “https://storage.googleapis.com/.../thumbnails/image123.png”.
  - “Find original image” primary button.
- When results are returned, highlight that each card includes a button or link “Open full‑size image”.

4d) Tab: “By file”
- Form:
  - Drag‑and‑drop area / file picker similar to the upload page but labelled “Upload a file for query only”.
  - Helper text: “The file is analysed for tags but not stored permanently.”
  - “Run search” button.
- States:
  - Show progress: “Uploading temporary file…”, “Analyzing tags…”, “Searching for matching media…”.
  - Display results in the same results grid.

5) Tags & notifications page (Tag edit & general usability – HD‑level)
This screen is key for bulk tag editing, deleting files, and managing tag‑based notifications. It should showcase bulk operations clearly.

- Layout:
  - Page title: “Tags & notifications”.
  - Split view:
    - Left: “Tag management” section.
    - Right: “Tag subscriptions & notifications” section.

5a) Tag management section
- At the top, show a filter bar to narrow down media:
  - Search input (by filename or tag).
  - Optional dropdown filters (file type, date range).
- Below the filter, reuse the same media results grid but with prominent checkboxes on each card.
- Above the grid, include bulk action buttons:
  - Primary button: “Add tags”.
  - Secondary button: “Remove tags”.
  - Destructive button: “Delete selected”.
- When “Add tags” or “Remove tags” is clicked:
  - Open a modal dialog with:
    - A multi‑chip text input labeled “Tags to add” or “Tags to remove”.
    - Primary action: “Apply to selected files”.
    - Secondary action: “Cancel”.
  - Include helper text explaining the bulk operation: “For remove, tags not currently assigned will be ignored.”
- When “Delete selected” is clicked:
  - Show a confirmation dialog stating that both full media and thumbnails will be deleted and the entry removed from the database.
- Feedback:
  - Toast messages for success and error (e.g., “Tags successfully added to 5 files”, “3 files deleted”).

5b) Tag subscriptions & notifications section
- Design a simple “Notifications” card showing:
  - A list of “Subscribed tags” as chips, each with a small “x” to unsubscribe.
  - A text field + “Add subscription” button to subscribe to a new tag.
  - A short description: “Receive email notifications when new media with these tags is added.”
- Include a “Notification settings” sub‑section with simple toggles:
  - “Email me when new media for my tags is uploaded”.
  - “Include thumbnail previews in emails”.
- Provide an empty state for when no subscriptions exist yet, encouraging users to add tag subscriptions.

6) Global UX details and states
- Design consistent empty states, loading states (spinners), and error banners for each main area (upload, search, tag management).
- Ensure form controls are aligned, spacing is consistent, and primary buttons are visually prominent.
- Include a simple footer with a subtle note like “Built as a multi‑cloud serverless app for FIT5225”.

Deliverables:
- Create separate Figma frames for each major screen:
  - Sign‑up
  - Sign‑in
  - Dashboard shell
  - Upload media
  - Search media (with all four tabs visible in one frame)
  - Tags & notifications
- Use component variants for buttons, inputs (default, hover, focus, error), tabs (selected/unselected), and cards (selected/unselected) to reflect an HD‑level, production‑ready design system.