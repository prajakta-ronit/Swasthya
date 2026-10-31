# SWASTHYA AI

SWASTHYA AI is an educational laboratory-report assistant built with Streamlit. It extracts supported measurements from lab reports, compares results across reports, and provides optional AI-generated explanations. It is not a medical diagnostic tool.

## Features

- Account registration and login.
- Extract measurements from PDF, PNG, JPG, and JPEG reports.
- Save uploaded reports to the signed-in user's account, then select saved reports for analysis or comparison without uploading again.
- Encrypt saved report files and filenames at rest using Fernet authenticated encryption.
- Download extracted measurements as CSV and medical reports as PDF.
- Compare two reports and download the comparison as CSV or PDF.
- Optionally generate an explanation in English, Hindi, or Marathi and download it as PDF.
- Ask follow-up questions about the current report using the optional AI Assistant.

## Requirements

- Python 3.10 or later.
- Tesseract OCR installed and available on `PATH` for image-report extraction.
- Ollama installed and running locally if you want AI explanations and chat.

## Run locally

Create and activate a virtual environment, then install the project dependencies:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS or Linux, activate the environment with:

```bash
source venv/bin/activate
```

### Configure report encryption

Generate a Fernet encryption key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Create `.streamlit/secrets.toml` and add the generated value:

```toml
REPORT_ENCRYPTION_KEY = "paste-generated-key-here"
```

Alternatively, set the `SWASTHYA_REPORT_ENCRYPTION_KEY` environment variable. The key must remain stable across restarts and deployments. Back it up securely and separately from report backups; losing or changing the key makes saved reports unrecoverable. Do not commit the key to GitHub.

### Optional AI setup

Start Ollama and download the default model:

```bash
ollama pull llama3.2:3b
```

Set `OLLAMA_MODEL` to use another installed model. AI features are enabled by default and can be disabled by setting `AI_ENABLED=false` in Streamlit secrets.

### Start the app

```bash
streamlit run app.py
```

Create an account in the app, sign in, and open **Report Analysis** to upload a report or choose one already saved to your account.

## Tests

Run the test suite with:

```bash
python -m pytest -q
```

## Data and security

- Account records and saved-report metadata are stored in SQLite under `data/`.
- Encrypted report files are stored under `data/uploads/`.
- Reports are scoped to the logged-in account in application queries. Keep the application server, database, and backups access-controlled.
- Configure HTTPS at the hosting layer for deployments exposed over a network. Encryption at rest does not encrypt data in transit.
- The encryption key is not stored with the encrypted reports. Maintain a secure key backup.
- Medical reports contain sensitive information. Upload only to a deployment you trust, and delete reports when no longer needed.

## Medical disclaimer

This application provides educational information only. Extracted values can be incorrect; verify them against the original laboratory report. Explanations are not diagnoses or a substitute for professional medical advice. Consult a qualified healthcare professional about medical concerns.
