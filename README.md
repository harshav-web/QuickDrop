# QuickDrop

QuickDrop is a temporary file-sharing web application built with Python, FastAPI, SQLite, HTML, CSS, and JavaScript.

Users can upload a file, choose an expiry period, and share a unique download link. The starter version supports 1 hour, 6 hours, 24 hours, and 7 days, with a 50 MB upload limit.

## Features

- Drag-and-drop file upload
- Unique, randomly generated sharing links
- Expiry choices: 1 hour, 6 hours, 24 hours, or 7 days
- Download without creating an account
- Upload progress indicator
- SQLite database for file metadata
- Expired-file cleanup when the application starts or an upload/file-info/download API is requested
- FastAPI interactive API documentation

## Project structure

```text
QuickDrop/
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   └── models.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── uploads/
│   └── .gitkeep
├── requirements.txt
├── .gitignore
└── README.md
```

## Run on Windows

Open PowerShell or Command Prompt in the project folder.

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

Open the application:

- Website: http://127.0.0.1:8000
- API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/` | Open the website |
| GET | `/api/health` | Check API status |
| POST | `/api/upload` | Upload a file |
| GET | `/api/files/{token}` | Get file information |
| GET | `/download/{token}` | Download a shared file |

## Upload to GitHub

Create a new empty repository on GitHub. Then run these commands from the project folder:

```bash
git init
git add .
git commit -m "Initial QuickDrop project"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/QuickDrop.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username.

## Deployment notes

GitHub Pages only hosts static frontend files; it cannot run this FastAPI backend. Deploy the FastAPI application to a Python-capable hosting service.

For production, configure persistent file storage and a persistent database. The local `uploads` folder and SQLite database may be lost on some hosting platforms when instances restart or redeploy.

The current cleanup runs when the app starts and when upload, file-info, or download endpoints are called. For production, configure a scheduled background cleanup task.

Before making the service public, add HTTPS, rate limiting, stronger file-content validation, malware scanning, monitoring, and appropriate storage limits. Do not treat the original starter version as a hardened public file-hosting service.
