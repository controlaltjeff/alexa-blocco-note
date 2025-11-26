from flask import Flask, request
from dotenv import load_dotenv
import os
import logging

# Load environment variables first
load_dotenv(override=True)

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
from ask_sdk_model.services.ups import UpsServiceClient
from ask_sdk_model.services.service_exception import ServiceException
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import database

app = Flask(__name__)
sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize DB
database.init_db()

# Load message constants from environment variables
MSG_LAUNCH = os.environ.get("MSG_LAUNCH", "Ciao, cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?")
MSG_MENU_FULL = os.environ.get("MSG_MENU_FULL", "Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?")
MSG_MENU_SHORT = os.environ.get("MSG_MENU_SHORT", "Cosa vuoi fare?")
MSG_START_WRITING = os.environ.get("MSG_START_WRITING", "Dimmi pure.")
MSG_NOTE_RECEIVED = os.environ.get("MSG_NOTE_RECEIVED", "Ricevuto. Altro?")
MSG_NOTE_SAVED = os.environ.get("MSG_NOTE_SAVED", "Salvato. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?")
MSG_NOTHING_SAID = os.environ.get("MSG_NOTHING_SAID", "Non hai detto nulla. Cosa vuoi fare ora?")
MSG_NOT_WRITING = os.environ.get("MSG_NOT_WRITING", "Non stavo scrivendo. Cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?")
MSG_PENDING_NOTE = os.environ.get("MSG_PENDING_NOTE", "Hai una nota in sospeso. Di 'Fine' per salvarla, o continua a dettare.")
MSG_PENDING_NOTE_SEND = os.environ.get("MSG_PENDING_NOTE_SEND", "Hai una nota in sospeso. Di 'Fine' per salvarla prima di inviare.")
MSG_WRITING_IN_PROGRESS = os.environ.get("MSG_WRITING_IN_PROGRESS", "Stai scrivendo. Di 'Fine' quando hai finito.")
MSG_NO_NOTES = os.environ.get("MSG_NO_NOTES", "Non hai ancora salvato nessuna nota. Cosa vuoi fare?")
MSG_READ_NOTES_PREFIX = os.environ.get("MSG_READ_NOTES_PREFIX", "Ecco le tue ultime note: ")
MSG_NOTE_FORMAT = os.environ.get("MSG_NOTE_FORMAT", "Nota {num} del {date}: {content}")
MSG_EMAIL_SENT = os.environ.get("MSG_EMAIL_SENT", "Email inviata. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?")
MSG_EMAIL_PERMISSION = os.environ.get("MSG_EMAIL_PERMISSION", "Per inviare le note, ho bisogno del permesso di accedere alla tua email. Ho inviato una scheda alla tua app Alexa. Per favore abilita i permessi nelle impostazioni.")
MSG_EMAIL_NOT_FOUND = os.environ.get("MSG_EMAIL_NOT_FOUND", "Non riesco a trovare il tuo indirizzo email. Controlla le impostazioni.")
MSG_NO_NOTES_TO_SEND = os.environ.get("MSG_NO_NOTES_TO_SEND", "Non ci sono note da inviare.")
MSG_EMAIL_ERROR = os.environ.get("MSG_EMAIL_ERROR", "C'è stato un errore nell'invio dell'email.")
MSG_EMAIL_SUBJECT = os.environ.get("MSG_EMAIL_SUBJECT", "Le tue note Alexa")
MSG_EMAIL_BODY_PREFIX = os.environ.get("MSG_EMAIL_BODY_PREFIX", "Ecco le tue note:\n\n")
MSG_HELP = os.environ.get("MSG_HELP", "Puoi dirmi di scrivere una nota o di rileggere le tue note. Cosa vuoi fare?")
MSG_NOT_UNDERSTOOD = os.environ.get("MSG_NOT_UNDERSTOOD", "Non ho capito. Vuoi scrivere, rileggere o inviare?")
MSG_GOODBYE = os.environ.get("MSG_GOODBYE", "Arrivederci!")
MSG_ERROR = os.environ.get("MSG_ERROR", "Scusa, ho avuto un problema. Riprova.")
MSG_SMTP_CONFIG_ERROR = os.environ.get("MSG_SMTP_CONFIG_ERROR", "Errore di configurazione del server email.")

def get_user_id(handler_input):
    """Extract user_id from the Alexa request."""
    return handler_input.request_envelope.session.user.user_id

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = MSG_LAUNCH
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class StartWritingIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("StartWritingIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["state"] = "WRITING"
        session_attr["note_buffer"] = []
        
        speak_output = MSG_START_WRITING
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CaptureNoteIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CaptureNoteIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        state = session_attr.get("state")
        
        if state == "WRITING":
            slots = handler_input.request_envelope.request.intent.slots
            note_text = slots["note"].value if slots["note"].value else ""
            
            # Check if user said a finish keyword
            finish_keywords = ["fine", "finito", "basta", "ho finito"]
            if note_text.lower().strip() in finish_keywords:
                # User wants to finish - save the note
                user_id = get_user_id(handler_input)
                buffer = session_attr.get("note_buffer", [])
                full_note = " ".join(buffer)
                if full_note:
                    database.save_note(full_note, user_id)
                    speak_output = MSG_NOTE_SAVED
                else:
                    speak_output = MSG_NOTHING_SAID
                
                # Reset state
                session_attr["state"] = "MENU"
                session_attr["note_buffer"] = []
                
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(speak_output)
                        .response
                )
            
            # Normal note capture
            buffer = session_attr.get("note_buffer", [])
            buffer.append(note_text)
            session_attr["note_buffer"] = buffer
            
            speak_output = MSG_NOTE_RECEIVED
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        else:
            speak_output = MSG_NOT_UNDERSTOOD
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )


class FinishIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("FinishIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        state = session_attr.get("state")
        
        if state == "WRITING":
            user_id = get_user_id(handler_input)
            buffer = session_attr.get("note_buffer", [])
            full_note = " ".join(buffer)
            if full_note:
                database.save_note(full_note, user_id)
                speak_output = MSG_NOTE_SAVED
            else:
                speak_output = MSG_NOTHING_SAID
            
            # Reset state
            session_attr["state"] = "MENU"
            session_attr["note_buffer"] = []
            
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        else:
            speak_output = MSG_NOT_WRITING
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )

class ReadNotesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ReadNotesIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        state = session_attr.get("state")
        
        # Check if user is in WRITING mode
        if state == "WRITING":
            buffer = session_attr.get("note_buffer", [])
            if buffer:
                speak_output = MSG_PENDING_NOTE
            else:
                speak_output = MSG_WRITING_IN_PROGRESS
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        
        # Normal flow: read saved notes
        user_id = get_user_id(handler_input)
        notes_data = database.get_notes(user_id)
        if notes_data:
            # Format notes
            date_format = os.environ.get("DATE_FORMAT", "%d/%m/%Y %H:%M")
            formatted_notes = []
            
            for i, (content, timestamp) in enumerate(notes_data, 1):
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    formatted_date = dt.strftime(date_format)
                except Exception as e:
                    logger.error(f"Date parsing error: {e}")
                    formatted_date = timestamp
                
                # "Nota 1 del [data]: [contenuto]"
                formatted_notes.append(MSG_NOTE_FORMAT.format(num=i, date=formatted_date, content=content))
            notes_text = ". ".join(formatted_notes)
            speak_output = f"{MSG_READ_NOTES_PREFIX}{notes_text}. {MSG_MENU_FULL}"
        else:
            speak_output = MSG_NO_NOTES
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SendEmailIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SendEmailIntent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        state = session_attr.get("state")
        
        # Check if user is in WRITING mode
        if state == "WRITING":
            buffer = session_attr.get("note_buffer", [])
            if buffer:
                speak_output = MSG_PENDING_NOTE_SEND
            else:
                speak_output = MSG_WRITING_IN_PROGRESS
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        
        # Normal flow: send email
        # Get user email from Alexa API
        svc_client_fact = handler_input.service_client_factory
        ups_service = svc_client_fact.get_ups_service()
        
        try:
            email_addr = ups_service.get_profile_email()
        except Exception as e:
            logger.error(f"Error fetching email: {e}", exc_info=True)
            # If permission is missing, ask for it
            return (
                handler_input.response_builder
                    .speak(MSG_EMAIL_PERMISSION)
                    .with_ask_for_permissions_consent_card(["alexa::profile:email:read"])
                    .response
            )

        if not email_addr:
             return (
                handler_input.response_builder
                    .speak(MSG_EMAIL_NOT_FOUND)
                    .response
            )

        # Get notes
        user_id = get_user_id(handler_input)
        notes_data = database.get_all_notes(user_id)
        if not notes_data:
             return (
                handler_input.response_builder
                    .speak(MSG_NO_NOTES_TO_SEND)
                    .response
            )

        # Format notes
        date_format = os.environ.get("DATE_FORMAT", "%d/%m/%Y %H:%M")
        formatted_notes = []
        
        for i, (content, timestamp) in enumerate(notes_data, 1):
            try:
                # SQLite default timestamp is YYYY-MM-DD HH:MM:SS
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                formatted_date = dt.strftime(date_format)
            except Exception as e:
                logger.error(f"Date parsing error: {e}")
                formatted_date = timestamp
                
            formatted_notes.append(f"{i}. [{formatted_date}] {content}")
            
        notes_text = "\n".join(formatted_notes)
        
        # Send Email via SMTP
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        
        # Robust handling for optional credentials
        smtp_user = os.environ.get("SMTP_USER", "").strip() or None
        smtp_password = os.environ.get("SMTP_PASSWORD", "").strip() or None
        
        smtp_encryption = os.environ.get("SMTP_ENCRYPTION", "STARTTLS").upper()
        
        logger.info(f"SMTP Config: Server={smtp_server}:{smtp_port}, Encryption={smtp_encryption}, Auth={'Yes' if smtp_user else 'No'} (User='{smtp_user}')")

        if not smtp_server:
             logger.error("SMTP server configuration missing")
             return (
                handler_input.response_builder
                    .speak(MSG_SMTP_CONFIG_ERROR)
                    .response
            )

        try:
            msg = MIMEText(f"{MSG_EMAIL_BODY_PREFIX}{notes_text}")
            msg['Subject'] = MSG_EMAIL_SUBJECT
            msg['From'] = smtp_user if smtp_user else "alexa@local.test"
            msg['To'] = email_addr

            logger.info(f"Sending email to {email_addr} via {smtp_server}:{smtp_port} ({smtp_encryption})")
            
            if smtp_encryption == "SSL":
                # Use implicit SSL
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            elif smtp_encryption == "STARTTLS":
                # Use explicit TLS
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            else:
                # No encryption (NONE)
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            
            logger.info("Email sent successfully")
                
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return (
                handler_input.response_builder
                    .speak(MSG_EMAIL_ERROR)
                    .response
            )


        # Return to main menu after sending email
        speak_output = MSG_EMAIL_SENT
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CloseIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CloseIntent")(handler_input)

    def handle(self, handler_input):
        # Clear any pending buffer if in WRITING mode (discard unsaved notes)
        session_attr = handler_input.attributes_manager.session_attributes
        if session_attr.get("state") == "WRITING":
            session_attr["state"] = "MENU"
            session_attr["note_buffer"] = []
        
        # Silent exit as requested
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = MSG_HELP
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        speak_output = MSG_GOODBYE
        return handler_input.response_builder.speak(speak_output).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        return handler_input.response_builder.response

class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True

    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        speak_output = MSG_ERROR
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

# Register handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StartWritingIntentHandler())
sb.add_request_handler(CaptureNoteIntentHandler())
sb.add_request_handler(FinishIntentHandler())
sb.add_request_handler(ReadNotesIntentHandler())
sb.add_request_handler(SendEmailIntentHandler())
sb.add_request_handler(CloseIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler()) 
sb.add_exception_handler(CatchAllExceptionHandler())

# Configure API Client
# sb.skill_configuration.api_client = DefaultApiClient()

verify_signature = os.environ.get("VERIFY_SIGNATURE", "True").lower() == "true"
skill = sb.create()
skill.api_client = DefaultApiClient()
skill_adapter = WebserviceSkillHandler(skill=skill, verify_signature=verify_signature, verify_timestamp=verify_signature)

@app.route("/", methods=['POST'])
def invoke_skill():
    return skill_adapter.verify_request_and_dispatch(request.headers, request.data)

if __name__ == '__main__':
    app.run(debug=True)
