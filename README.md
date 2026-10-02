# Construction Change AI

A Python backend for organizing construction projects and their documents, with the goal of identifying potential construction changes from project records and drawing revisions.

The current version supports creating and listing projects, uploading documents, and listing a project's documents. PDF extraction, OCR, metadata identification, and automated change detection are planned and are not implemented yet.

## Technology

- FastAPI for the HTTP API and interactive documentation
- PostgreSQL for project and document records
- SQLAlchemy with Psycopg 3 for database access
- Pydantic for request/response schemas and environment configuration
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
│   └── routers/          # Project and document endpoints
├── requirements.txt
├── .env                  # Local configuration; not committed
├── .venv/                # Local virtual environment; not committed
└── uploads/              # Uploaded files; not committed
```

The local `construction_change_datasets/` directory contains development datasets and is currently excluded from Git. It is not required to start the API.

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

If the repository is already cloned, start from its `backend` directory. Activate the virtual environment each time you open a new terminal.

### 2. Create the PostgreSQL database

Create a database named `construction_ai` using pgAdmin or a PostgreSQL administration tool. The application database user must have permission to connect and create tables in it.

The application creates missing tables at startup. It does not create the database itself, and it does not migrate existing tables when model definitions change.

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

## Data and storage

- `projects` stores project records.
- `documents` stores filenames, categories, file paths, upload timestamps, and processing status.
- `drawing_revisions` defines records for individual drawing revisions.
- `potential_changes` defines findings that can later be reviewed.

The last two tables have models, but the current endpoints do not populate them automatically.

Files are stored separately from PostgreSQL in `uploads/{project_id}/{filename}`. Because the upload directory is relative to the process's working directory, start the server from `backend` to keep files under `backend/uploads/`.

## Current limitations

This is an early local-development backend:

- Uploading a document does not extract text, perform OCR, identify drawing metadata, or detect changes.
- Uploads use the supplied filename. Reusing a filename within a project overwrites its stored file; filename/path sanitization is not yet implemented.
- There are no explicit upload size or content checks, authentication, or access controls.
- A database failure after file storage can leave a file without a saved document record.
- Schema changes require a migration strategy; startup table creation does not update existing tables.

Use trusted files locally while these behaviors are being developed.
