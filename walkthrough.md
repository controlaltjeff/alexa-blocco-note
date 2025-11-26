# Alexa Note Taker Skill Walkthrough

## Overview
This is a simple Alexa skill that allows users to dictate notes which are saved to a local SQLite database. The skill is built with Flask and the Alexa Skills Kit SDK for Python.

## Features
- **Write Notes**: Dictate notes continuously.
- **Read Notes**: Read back the last 5 saved notes (numbered and dated).
- **Multi-User**: Notes are saved per-user (based on Alexa User ID).
- **Persistent Session**: Loop back to the main menu after actions.
- **Implicit Save**: "Invia" or "Rileggi" commands automatically save any pending note buffer.
- **Smart Welcome**: Detects new sessions and greets the user if no notes are present.
- **Silent Exit**: "Chiudi" command ends the session without response.

## Prerequisites
- Python 3.8+
- An Alexa Developer Account
- A VPS with SSL (for production) OR `ngrok` (for local testing)

## Installation

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize Database**:
   The database `notes.db` will be created automatically when you run the application.
   *Note: The schema includes `user_id` to support multiple users.*

## Running the Server

### Local Testing (with ngrok)
1. Start the Flask app:
   ```bash
   # Disable signature verification for local testing if needed
   export VERIFY_SIGNATURE=False
   python3 main.py
   ```
2. Expose port 5000:
   ```bash
   ngrok http 5000
   ```
3. Copy the HTTPS URL from ngrok (e.g., `https://abcd-1234.ngrok.io`) to the Alexa Developer Console > Build > Endpoint > HTTPS.

### Production (VPS)
1. Run with Gunicorn:
   ```bash
   export VERIFY_SIGNATURE=True
   gunicorn -w 4 -b 0.0.0.0:5000 main:app
   ```
2. Configure Nginx/Apache as a reverse proxy with SSL (Let's Encrypt) pointing to port 5000.
3. Set the endpoint in Alexa Developer Console to your domain (e.g., `https://your-domain.com`).

## Alexa Configuration
1. Create a new Custom Skill in the Alexa Developer Console.
2. Go to **JSON Editor** and paste the contents of `skill.json`.
3. Save and Build the Model.

### 5. Email Configuration (New)
To use the "Invia" (Send Email) feature:

1.  **Alexa Permissions**:
    - Go to Alexa Developer Console -> Build -> Tools -> Permissions.
    - Enable **Email Address**.

2.  **SMTP Configuration (.env)**:
    I have created a `.env` file in the project directory. You can edit this file to configure your email settings easily.

    **Edit `.env`:**
    ```ini
    # Security
    VERIFY_SIGNATURE=True

    # Email Configuration
    SMTP_SERVER=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=your_email@gmail.com
    SMTP_PASSWORD=your_app_password
    
    # Encryption Mode: SSL, STARTTLS, or NONE
    SMTP_ENCRYPTION=NONE

    # Date Format (Italian: %d/%m/%Y %H:%M)
    DATE_FORMAT=%d/%m/%Y %H:%M
    ```
    
    - **SSL**: Use for port 465 (Implicit SSL).
    - **STARTTLS**: Use for port 587 (Explicit TLS).
    - **NONE**: Use for port 25 or internal servers without encryption.
    - **DATE_FORMAT**: Customize how dates appear in the email and when reading notes (Python strftime format).

## Usage
- **Open**: "Alexa, apri il mio blocco note"
    - *If you have no notes, it will greet you and ask if you want to write one.*
- **Write**: "Scrivi" -> Dictate notes -> "Fine"
- **Read**: "Rileggi" (Reads notes: "Nota 1 del [data]: [contenuto]")
- **Email**: "Invia" (Sends all notes to your Alexa account email, formatted with dates)
- **Close**: "Chiudi"
