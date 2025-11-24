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
import database

app = Flask(__name__)
sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize DB
database.init_db()

class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Ciao, cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?"
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
        
        speak_output = "Dimmi pure."
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
            
            buffer = session_attr.get("note_buffer", [])
            buffer.append(note_text)
            session_attr["note_buffer"] = buffer
            
            speak_output = "Ricevuto. Altro?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        else:
            speak_output = "Non ho capito. Vuoi scrivere, rileggere o inviare?"
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
            buffer = session_attr.get("note_buffer", [])
            full_note = " ".join(buffer)
            if full_note:
                database.save_note(full_note)
                speak_output = "Salvato. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
            else:
                speak_output = "Non hai detto nulla. Cosa vuoi fare ora?"
            
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
            speak_output = "Non stavo scrivendo. Cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?"
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
        notes = database.get_notes()
        if notes:
            notes_text = ". ".join(notes)
            speak_output = f"Ecco le tue ultime note: {notes_text}. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
        else:
            speak_output = "Non hai ancora salvato nessuna nota. Cosa vuoi fare?"
            
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
                    .speak("Per inviare le note, ho bisogno del permesso di accedere alla tua email. Ho inviato una scheda alla tua app Alexa. Per favore abilita i permessi nelle impostazioni.")
                    .with_ask_for_permissions_consent_card(["alexa::profile:email:read"])
                    .response
            )

        if not email_addr:
             return (
                handler_input.response_builder
                    .speak("Non riesco a trovare il tuo indirizzo email. Controlla le impostazioni.")
                    .response
            )

        # Get notes
        notes = database.get_all_notes()
        if not notes:
             return (
                handler_input.response_builder
                    .speak("Non ci sono note da inviare.")
                    .response
            )
            
        notes_text = "\n".join(notes)
        
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
                    .speak("Errore di configurazione del server email.")
                    .response
            )

        try:
            msg = MIMEText(f"Ecco le tue note:\n\n{notes_text}")
            msg['Subject'] = "Le tue note Alexa"
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
                    .speak("C'è stato un errore nell'invio dell'email.")
                    .response
            )

        # Silent exit
        return handler_input.response_builder.response

class CloseIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CloseIntent")(handler_input)

    def handle(self, handler_input):
        # Silent exit as requested
        return handler_input.response_builder.response

class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        speak_output = "Puoi dirmi di scrivere una nota o di rileggere le tue note. Cosa vuoi fare?"
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
        speak_output = "Arrivederci!"
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
        speak_output = "Scusa, ho avuto un problema. Riprova."
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
