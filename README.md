# Construction Change AI

A Python backend for organizing construction projects and their documents, with the goal of identifying potential construction changes from project records and drawing revisions.

The current version supports creating and listing projects, uploading and listing documents, and processing text-based PDFs into structured RFI, drawing, and contract records. Extraction uses pdfplumber followed by document-specific rules. OCR and automated change detection are not implemented yet.

## Technology

- FastAPI for the HTTP API and interactive documentation
- PostgreSQL for project and document records
- SQLAlchemy with Psycopg 3 for database access
- Pydantic for request/response schemas and environment configuration
- pdfplumber for PDF text extraction
- Local filesystem storage for uploaded files

## Repository structure

```text
backend/
├── app/
│   ├── main.py           # Application initialization and router registration
│   ├── config.py         # Environment settings
│   ├── db.py             # Database engine, sessions, and model base
│   ├── models/           # Database table definitions
│   ├── schemas/          # Request and response validation
│   ├── routers/          # Project and document endpoints
│   └── services/         # PDF extraction and document-specific parsers
├── requirements.txt
├── .env                  # Local configuration; not committed
├── .venv/                # Local virtual environment; not committed
└── uploads/              # Uploaded files; not committed
```

The local `construction_change_datasets/` and `test/data/` directories are excluded from Git. Sample PDFs are not included in a fresh clone; provide your own files to exercise processing. Neither directory is required to start the API.

## Local setup

These commands assume Linux or macOS, Python 3.10 or newer, and a running PostgreSQL server.

### 1. Clone the repository and install dependencies

```bash
git clone https://github.com/ZeusTucZ/projecta.git
cd projecta/backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Processing requires `pdfplumber`. If your dependency snapshot does not yet include it, install it with `python -m pip install pdfplumber`.

If the repository is already cloned, start from its `backend` directory. Activate the virtual environment each time you open a new terminal.

### 2. Create the PostgreSQL database

Create a database named `construction_ai` using pgAdmin or a PostgreSQL administration tool. The application database user must have permission to connect and create tables in it.

The application creates missing tables at startup. It does not create the database itself, and it does not migrate existing tables when model definitions change.

For an existing database created before drawing discipline was added, stop the API and run this in pgAdmin's Query Tool against the application database:

```sql
ALTER TABLE drawing_revisions
ADD COLUMN IF NOT EXISTS discipline VARCHAR(100);
```

Commit the change if using an explicit transaction, then restart the API. Existing rows remain unchanged except for the new nullable column; processing does not backfill their discipline automatically. Fresh databases get this column through the current model. This manual update is a temporary approach until versioned migrations are introduced.


### 3. Configure the connection

Create `backend/.env` with your local connection details:

```dotenv
DATABASE_URL=postgresql+psycopg://YOUR_USER:YOUR_PASSWORD@localhost:5432/construction_ai
```

Replace the placeholders with your PostgreSQL credentials. URL-encode special characters in the username or password when necessary. Keep this file out of Git.

Settings are loaded from `backend/.env`; an existing `DATABASE_URL` environment variable takes precedence.

### 4. Start the API

Run from `backend` with the virtual environment activated:

```bash
python -m uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000/
- Interactive documentation: http://127.0.0.1:8000/docs

PostgreSQL must be available at startup because `main.py` calls `Base.metadata.create_all(bind=engine)`. Use Ctrl+C to stop the development server.

## Available endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Return the API welcome message |
| POST | `/projects/` | Create a project |
| GET | `/projects/` | List all projects |
| POST | `/projects/{project_id}/documents` | Upload a document to an existing project |
| GET | `/projects/{project_id}/documents` | List the project's document metadata |
| POST | `/documents/{document_id}/process-rfi` | Extract and save RFI fields |
| POST | `/documents/{document_id}/process-drawings` | Extract and save drawing metadata by page |
| POST | `/documents/{document_id}/process-contract` | Extract and save a contract and its sections |

### Create a project

In `/docs`, select `POST /projects/`, click **Try it out**, and submit:

```json
{
  "name": "Rock Valley School",
  "description": "Construction document analysis"
}
```

The name is required and the description is optional. Save the returned project ID for document requests.

### Upload and list documents

In `/docs`, select `POST /projects/{project_id}/documents` and provide:

- `project_id`: the ID of an existing project
- `document_type`: exactly `drawing`, `rfi`, or `contract`
- `file`: the file to upload

The upload uses multipart form data, not a JSON body. `document_type` describes the document's category, not its file extension: use `drawing` for a drawing PDF, not `pdf`.

Then call `GET /projects/{project_id}/documents` to see the saved metadata. An existing project with no documents returns an empty list. An unknown project returns HTTP 404. Unsupported document categories return HTTP 400.

### Process an uploaded PDF

1. Upload a PDF with the appropriate document type.
2. Copy the returned document ID (not the project ID).
3. In `/docs`, call the matching processing endpoint with that ID. No new file upload is needed.
4. Inspect the structured response and compare it with the original PDF.

Processing reads the stored file, extracts text page by page in memory, applies the relevant rules, and saves structured results in PostgreSQL. Raw extracted page text is not stored separately. The original file remains on disk, and successful processing sets the document status to `processed`. This status means extraction was saved, not that its accuracy or commercial impact has been verified.

| Type | Saved results | Repeat processing |
| --- | --- | --- |
| RFI | Number, issue date, drawing reference, subject, question, response, potential impact, and identifying page | Updates the existing RFI record |
| Drawing | Drawing number, revision, title, and discipline for each parsed page | Returns HTTP 409 if drawing records already exist |
| Contract | Contract number, trade, and sections with numbers, titles, full text, and starting pages | Returns HTTP 409 if a contract record already exists |

Missing documents or stored files return HTTP 404. A mismatched document type returns HTTP 400. Unrecognized required fields or sections return HTTP 422; RFI and contract processing also explicitly reject empty text extraction. Malformed or unreadable PDFs may still produce unhandled errors.

### Manual verification

Using trusted, text-based samples, check that:

- Extracted RFI fields, drawing identifiers, and contract sections match the source PDFs.
- Multiline questions, responses, and clauses retain their full wording.
- Saved records link to the correct document.
- Repeat requests follow the behavior described above.
- Missing required information produces an understandable error.

The parsers were developed around a small set of sample layouts. These checks do not establish accuracy across arbitrary construction documents.

## Data and storage

- `projects` stores project records.
- `documents` stores filenames, categories, file paths, upload timestamps, and processing status.
- `rfis` stores extracted RFI fields, with at most one record per document.
- `drawing_revisions` stores individual drawing revisions and their discipline.
- `contracts` stores contract-level fields, with at most one record per document.
- `contract_sections` stores clauses linked to their parent contract.
- `potential_changes` defines future findings; current processing does not generate these records.

Drawing processing does not yet populate `previous_revision_id` or persist the parser's source page. RFI and contract-section source pages are stored. Contract relationships allow the parent and its sections to be saved together.

Files are stored separately from PostgreSQL in `uploads/{project_id}/{filename}`. Because the upload directory is relative to the process's working directory, start the server from `backend` to keep files under `backend/uploads/`.

## Current limitations

This is an early local-development backend:

- Uploading and processing are separate operations; uploads alone do not extract content.
- OCR is not implemented. Image-only scans require a future OCR step; mixed PDFs can also contain pages that ordinary text extraction misses.
- Rules assume one RFI or contract per PDF and one drawing per page. They use sample-specific labels and headings, including contract headings such as `Section 4.2 - Scope of Work`.
- Repeated labels, unusual layouts, and OCR-like text errors are not comprehensively handled. No confidence scoring or review workflow is implemented.
- Drawing geometry, revision matching, and automated construction-change detection are not implemented.
- Processing runs synchronously during the request; background jobs and concurrency-safe reprocessing are not implemented.
- Uploads use the supplied filename. Reusing a filename within a project overwrites its stored file; filename/path sanitization is not yet implemented.
- There are no explicit upload size or content checks, authentication, or access controls.
- A database failure after file storage can leave a file without a saved document record.
- Schema changes require a migration strategy; startup table creation does not update existing tables.

Use trusted files locally while these behaviors are being developed.
