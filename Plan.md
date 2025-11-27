# Alexa Note Taker Skill Implementation Plan

## Goal Description

Create a simple Alexa skill hosted on a local Python server that allows users to dictate notes. The skill will accumulate text until the user says "FINISH", at which point it saves the note to a local SQLite database.

## User Review Required

> [!IMPORTANT]
> **VPS Deployment & SSL**: Since you are deploying to a VPS, you must ensure your server has a valid SSL certificate (e.g., via Let's Encrypt). Alexa requires the endpoint to be HTTPS with a trusted certificate. You can run the Python application using a WSGI server like gunicorn behind a web server (Apache/Nginx) that handles the SSL termination.

## Proposed Changes

### Project Structure

#### [NEW] requirements.txt
```txt
flask
ask-sdk-core
ask-sdk-webservice-support
ask-sdk-model
gunicorn  # for production serving on VPS
```

#### [NEW] main.py
Flask application entry point.
- Route `/` or `/api/skill` to handle POST requests from Alexa.
- Skill handlers:
  - **LaunchRequestHandler**: Welcome message.
  - **CaptureNoteIntentHandler**: Appends spoken text to session attributes.
  - **FinishIntentHandler**: Saves session buffer to SQLite and says goodbye.
  - Help/Stop/Cancel handlers.

#### [NEW] database.py
- `init_db()`: Create `notes` table if not exists.
- `save_note(text)`: Insert note into SQLite.

#### [NEW] skill.json
JSON definition of the Interaction Model.
- **Locale**: it-IT
- **Intents**:
  - **StartWritingIntent**: Triggered by "scrivi". Transitions to note taking mode.
  - **ReadNotesIntent**: Triggered by "rileggi". Reads saved notes.
  - **CaptureNoteIntent**: Captures the raw text of the note.
  - **FinishIntent**: Triggered by "FINE" to save.
  - **CloseIntent**: Triggered by "CHIUDI" to end the skill.
  - **SendEmailIntent**: Triggered by "INVIA". Sends notes to user's email and exits silently.

#### [MODIFY] main.py
- Enable ApiClient in SkillBuilder to fetch user email.
- **SendEmailIntentHandler**:
  - Fetch user email via UpsServiceClient.
  - Retrieve all notes from DB.
  - Send email using SMTP (requires SMTP config).
  - Return empty response (silent exit).

## Verification Plan

### Automated Tests

**test_skill.py**: Mock UpsServiceClient and smtplib to verify flow.

### Manual Verification

**Configuration**: Enable "Email Address" permission in Alexa Developer Console.

**SMTP Setup**: Set environment variables `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`.

**Test**:
1. "Apri il mio blocco note"
2. "Invia" → [Alexa exits silently]
3. Check inbox for email with notes.