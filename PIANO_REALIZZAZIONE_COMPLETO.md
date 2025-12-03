# Piano di Realizzazione Completo: Alexa Skill "Il Mio Blocco Note"

## Indice
1. [Panoramica del Progetto](#panoramica-del-progetto)
2. [Architettura del Sistema](#architettura-del-sistema)
3. [Requisiti Tecnici](#requisiti-tecnici)
4. [Struttura del Database](#struttura-del-database)
5. [Modello di Interazione Alexa](#modello-di-interazione-alexa)
6. [Flussi Conversazionali Ottimizzati](#flussi-conversazionali-ottimizzati)
7. [Implementazione Backend](#implementazione-backend)
8. [Gestione degli Stati di Sessione](#gestione-degli-stati-di-sessione)
9. [Ordine di Priorità degli Handler](#ordine-di-priorità-degli-handler)
10. [Configurazione e Variabili d'Ambiente](#configurazione-e-variabili-dambiente)
11. [Guida all'Implementazione Passo-Passo](#guida-allimplementazione-passo-passo)

---

## 1. Panoramica del Progetto

### Obiettivo
Creare un'Alexa Skill in italiano che permetta agli utenti di:
- Dettare e salvare note vocali
- Rileggere le note salvate
- Inviare le note via email
- Configurare la cancellazione automatica delle note vecchie
- Gestire le impostazioni di retention

### Caratteristiche Principali
- **Multi-utente**: Ogni utente Alexa ha le proprie note isolate
- **Persistenza**: Note salvate in database SQLite
- **Email**: Invio note tramite SMTP configurabile
- **Auto-cleanup**: Cancellazione automatica note vecchie (opzionale)
- **Configurazione flessibile**: Messaggi personalizzabili via variabili d'ambiente

---

## 2. Architettura del Sistema

```
┌─────────────────┐
│  Alexa Device   │
└────────┬────────┘
         │ Voice Commands
         ▼
┌─────────────────────────────────┐
│   Amazon Alexa Service          │
│   (Intent Recognition)          │
└────────┬────────────────────────┘
         │ JSON Request
         ▼
┌─────────────────────────────────┐
│   Flask Web Server              │
│   (WebserviceSkillHandler)      │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   ASK SDK Request Handlers      │
│   - LaunchRequestHandler        │
│   - YesIntentHandler            │
│   - NoIntentHandler             │
│   - CaptureNoteIntentHandler    │
│   - StartWritingIntentHandler   │
│   - FinishIntentHandler         │
│   - ReadNotesIntentHandler      │
│   - SendEmailIntentHandler      │
│   - ConfigureIntentHandler      │
│   - SetRetentionIntentHandler   │
│   - CloseIntentHandler          │
│   - HelpIntentHandler           │
│   - CancelOrStopIntentHandler   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│   Database Layer (database.py)  │
│   - SQLite Operations           │
│   - User Settings Management    │
│   - Notes CRUD Operations       │
└─────────────────────────────────┘
```

---

## 3. Requisiti Tecnici

### Dipendenze Python
```
flask==2.3.0
python-dotenv==1.0.0
ask-sdk-core==1.18.0
ask-sdk-webservice-support==1.18.0
```

### Struttura dei File
```
alexa-blocco-note/
├── main.py                 # Applicazione Flask e handler Alexa
├── database.py             # Layer database SQLite
├── skill.json              # Modello di interazione Alexa
├── .env                    # Variabili d'ambiente (non committare)
├── .env.example            # Template variabili d'ambiente
├── requirements.txt        # Dipendenze Python
├── notes.db                # Database SQLite (generato automaticamente)
└── README.md               # Documentazione
```

---

## 4. Struttura del Database

### Tabella: `notes`
```sql
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT
);
```

**Campi:**
- `id`: Identificatore univoco della nota
- `content`: Testo della nota dettata dall'utente
- `timestamp`: Data e ora di creazione (formato: YYYY-MM-DD HH:MM:SS)
- `user_id`: ID utente Alexa (per isolamento multi-utente)

### Tabella: `user_settings`
```sql
CREATE TABLE IF NOT EXISTS user_settings (
    user_id TEXT PRIMARY KEY,
    retention_days INTEGER,
    auto_delete_enabled INTEGER DEFAULT 0
);
```

**Campi:**
- `user_id`: ID utente Alexa (chiave primaria)
- `retention_days`: Numero di giorni di retention (può essere NULL se non configurato)
- `auto_delete_enabled`: Flag booleano (0=disabilitato, 1=abilitato)

**Nota importante**: `retention_days` può essere NULL, ma quando si salva una configurazione con auto-delete disabilitato, si usa un valore di default (7 giorni) per evitare vincoli NOT NULL.

---

## 5. Modello di Interazione Alexa

### Invocation Name
```
"il mio blocco note"
```

### Intents Personalizzati

#### 1. StartWritingIntent
**Utterances:**
- "scrivi"
- "scrivere"
- "voglio scrivere"
- "inizia a scrivere"

**Slots:** Nessuno

#### 2. CaptureNoteIntent
**Utterances:**
- "{note}"

**Slots:**
- `note` (tipo: NoteType)

**Tipo NoteType (esempi):**
- "comprare il latte"
- "chiamare mamma"
- "appuntamento dal dentista"
- "pagare le bollette"
- "andare in palestra"
- "ricordami di fare la spesa"
- "idea per il progetto"

#### 3. FinishIntent
**Utterances:**
- "fine"
- "ho finito"
- "basta"

**Slots:** Nessuno

#### 4. ReadNotesIntent
**Utterances:**
- "rileggi"
- "rileggere"
- "leggi le note"
- "cosa ho scritto"

**Slots:** Nessuno

#### 5. SendEmailIntent
**Utterances:**
- "invia"
- "inviare"
- "manda email"
- "spedisci note"

**Slots:** Nessuno

#### 6. ConfigureIntent
**Utterances:**
- "configura"
- "configurazione"
- "impostazioni"
- "configura le impostazioni"
- "apri impostazioni"

**Slots:** Nessuno

#### 7. SetRetentionIntent
**Utterances:**
- "cancella note più vecchie di {days} giorni"
- "imposta scadenza a {days} giorni"
- "tieni le note per {days} giorni"
- "elimina dopo {days} giorni"
- "scadenza {days} giorni"
- "ritenzione {days} giorni"
- "imposta scadenza"
- "cambia scadenza"
- "modifica scadenza"
- "configura scadenza"

**Slots:**
- `days` (tipo: AMAZON.NUMBER)

#### 8. CloseIntent
**Utterances:**
- "chiudi"
- "esci"

**Slots:** Nessuno

### Intents Built-in Amazon

- **AMAZON.YesIntent**: Gestisce risposte affermative ("sì")
- **AMAZON.NoIntent**: Gestisce risposte negative ("no")
- **AMAZON.HelpIntent**: Richiesta di aiuto
- **AMAZON.CancelIntent**: Annullamento operazione
- **AMAZON.StopIntent**: Stop skill
- **AMAZON.NavigateHomeIntent**: Navigazione home

---

## 6. Flussi Conversazionali Ottimizzati

### 6.1 Flusso: Lancio Skill
```
User: "Alexa, apri il mio blocco note"
Alexa: "Ciao, cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?"

[Sistema esegue cleanup automatico note vecchie in background, solo se user_settings.auto_delete_enabled = 1]
```

### 6.2 Flusso: Scrittura Nota
```
User: "Alexa, apri il mio blocco note"
Alexa: "Ciao, cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?"

User: "scrivi"
Alexa: "Dimmi pure."

User: "comprare il latte"
Alexa: "Ricevuto. Altro?"

User: "chiamare mamma"
Alexa: "Ricevuto. Altro?"

User: "fine"
Alexa: "Salvato. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
```

**Ottimizzazioni:**
- Risposta breve "Dimmi pure" invece di frasi lunghe
- "Ricevuto. Altro?" per conferma rapida
- Buffer in memoria fino a "fine" per permettere correzioni

### 6.3 Flusso: Lettura Note
```
User: "rileggi"
Alexa: "Ecco le tue ultime note: Nota 1 del 03/12/2025 10:30: comprare il latte. 
        Nota 2 del 03/12/2025 10:31: chiamare mamma. 
        Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
```

**Ottimizzazioni:**
- Massimo 5 note più recenti per evitare risposte troppo lunghe
- Formato data configurabile nel file .env
- Ritorno automatico al menu

### 6.4 Flusso: Invio Email
```
User: "invia"
Alexa: [Richiede permesso email se non concesso]
       "Email inviata. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
```

**Ottimizzazioni:**
- Gestione permessi Alexa automatica
- Supporto SMTP configurabile (SSL/STARTTLS/NONE) in file .env
- Autenticazione opzionale

### 6.5 Flusso: Configurazione Auto-Delete (OTTIMIZZATO)
```
User: "configura"
Alexa: "È possibile attivare la cancellazione automatica delle note dopo un periodo 
        che definisci. Vuoi attivare la cancellazione automatica?"

--- SCENARIO A: Abilitazione ---
User: "sì"
Alexa: "Dopo quanti giorni dovrò cancellare le note?"

User: "sette"
Alexa: "Configurazione salvata. La cancellazione automatica è attiva dopo 7 giorni. 
        Cosa vuoi fare ora?"

--- SCENARIO B: Disabilitazione ---
User: "no"
Alexa: "Configurazione salvata. La cancellazione automatica è disattivata. 
        Cosa vuoi fare ora?Scrivi, Rileggi, Invia o Chiudi?"
```

**Ottimizzazioni critiche:**
1. **YesIntent/NoIntent PRIMA di CaptureNoteIntent** nell'ordine handler
2. Gestione stato `config_state` in sessione
3. Parsing numeri con regex da input vocale
4. Valore default (7 giorni) quando auto-delete disabilitato

### 6.6 Flusso: Gestione Errori Stato
```
User: "rileggi" (mentre sta scrivendo)
Alexa: "Hai una nota in sospeso. Di 'Fine' per salvarla, o continua a dettare."

User: "invia" (mentre sta scrivendo)
Alexa: "Hai una nota in sospeso. Di 'Fine' per salvarla prima di inviare."

User: "fine" (senza essere in modalità scrittura)
Alexa: "Non stavo scrivendo. Cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?"
```

**Ottimizzazioni:**
- Controllo stato sessione prima di ogni azione
- Messaggi specifici per ogni conflitto di stato
- Prevenzione perdita dati

---

## 7. Implementazione Backend

### 7.1 Funzioni Database (database.py)

#### init_db()
```python
def init_db():
    """Inizializza database con tabelle e gestisce migrazioni."""
    # Crea tabelle notes e user_settings
    # Gestisce ALTER TABLE per backward compatibility
    # Gestisce eccezioni OperationalError per colonne esistenti
```

#### save_note(text, user_id)
```python
def save_note(text, user_id):
    """Salva una nota per un utente specifico."""
    # INSERT INTO notes (content, user_id) VALUES (?, ?)
```

#### get_notes(user_id, limit=5)
```python
def get_notes(user_id, limit=5):
    """Recupera le ultime N note di un utente."""
    # SELECT content, timestamp FROM notes 
    # WHERE user_id = ? 
    # ORDER BY timestamp DESC LIMIT ?
    # Ritorna: [(content, timestamp), ...]
```

#### get_all_notes(user_id)
```python
def get_all_notes(user_id):
    """Recupera tutte le note di un utente (per email)."""
    # SELECT content, timestamp FROM notes 
    # WHERE user_id = ? 
    # ORDER BY timestamp DESC
```

#### set_auto_delete_config(user_id, enabled, days=None)
```python
def set_auto_delete_config(user_id, enabled, days=None):
    """Salva configurazione auto-delete."""
    # IMPORTANTE: Usa default 7 giorni se days è None
    # retention_days = days if days is not None else 7
    # INSERT OR REPLACE INTO user_settings 
    # (user_id, auto_delete_enabled, retention_days) 
    # VALUES (?, ?, ?)
```

#### get_auto_delete_config(user_id)
```python
def get_auto_delete_config(user_id):
    """Recupera configurazione auto-delete."""
    # SELECT auto_delete_enabled, retention_days 
    # FROM user_settings WHERE user_id = ?
    # Ritorna: (enabled: bool, days: int|None)
```

#### cleanup_old_notes(user_id)
```python
def cleanup_old_notes(user_id):
    """Cancella note vecchie se auto-delete abilitato."""
    # 1. Recupera configurazione
    # 2. Se auto_delete_enabled == False, return 0
    # 3. Se days è None, return 0
    # 4. DELETE FROM notes WHERE user_id = ? 
    #    AND timestamp < datetime('now', '-{days} days')
    # Ritorna: numero note cancellate
```

### 7.2 Handler Alexa (main.py)

#### Struttura Base Handler
```python
class NomeHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        # Determina se questo handler può gestire la richiesta
        return is_intent_name("NomeIntent")(handler_input)
    
    def handle(self, handler_input):
        # Logica di gestione
        # 1. Recupera attributi sessione
        # 2. Controlla stato
        # 3. Esegue operazioni
        # 4. Aggiorna stato
        # 5. Ritorna risposta
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(reprompt)
                .response
        )
```

#### Gestione User ID
```python
def get_user_id(handler_input):
    """Estrae user_id dalla richiesta Alexa."""
    return handler_input.request_envelope.session.user.user_id
```

---

## 8. Gestione degli Stati di Sessione

### Stati Principali

#### 8.1 Stato WRITING
**Quando attivo:** Dopo "scrivi" fino a "fine"

**Attributi sessione:**
```python
session_attr["state"] = "WRITING"
session_attr["note_buffer"] = ["testo1", "testo2", ...]
```

**Comportamento:**
- CaptureNoteIntent aggiunge al buffer
- FinishIntent salva e resetta
- ReadNotesIntent/SendEmailIntent bloccati con messaggio

#### 8.2 Stato CONFIG_AUTO_DELETE_QUESTION
**Quando attivo:** Dopo "configura"

**Attributi sessione:**
```python
session_attr["config_state"] = "AUTO_DELETE_QUESTION"
```

**Comportamento:**
- YesIntent → transizione a DAYS_QUESTION
- NoIntent → salva config disabilitata e resetta

#### 8.3 Stato DAYS_QUESTION
**Quando attivo:** Dopo risposta "sì" a auto-delete

**Attributi sessione:**
```python
session_attr["config_state"] = "DAYS_QUESTION"
session_attr["auto_delete_enabled"] = True
```

**Comportamento:**
- CaptureNoteIntent estrae numero e salva config
- Parsing con regex: `re.findall(r'\d+', text)`

#### 8.4 Stato MENU (default)
**Quando attivo:** Dopo lancio, dopo azioni completate

**Attributi sessione:**
```python
session_attr["state"] = "MENU" (o assente)
session_attr["config_state"] = None
```

**Comportamento:**
- Tutti gli intent principali disponibili

---

## 9. Ordine di Priorità degli Handler

**CRITICO**: L'ordine di registrazione determina la priorità di matching.

### Ordine Corretto
```python
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StartWritingIntentHandler())
sb.add_request_handler(YesIntentHandler())          # PRIMA di CaptureNote
sb.add_request_handler(NoIntentHandler())           # PRIMA di CaptureNote
sb.add_request_handler(CaptureNoteIntentHandler())  # Dopo Yes/No
sb.add_request_handler(FinishIntentHandler())
sb.add_request_handler(ReadNotesIntentHandler())
sb.add_request_handler(SendEmailIntentHandler())
sb.add_request_handler(SetRetentionIntentHandler())
sb.add_request_handler(ConfigureIntentHandler())
sb.add_request_handler(CloseIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
```

**Perché questo ordine:**
1. **YesIntent/NoIntent prima di CaptureNoteIntent**: CaptureNote ha pattern generico `{note}` che cattura tutto, incluso "sì"/"no"
2. **Intent specifici prima di generici**: Più specifico = più alta priorità
3. **Exception handler ultimo**: Cattura errori non gestiti

---

## 10. Configurazione e Variabili d'Ambiente

### File .env (Esempio Completo)
```bash
# Security
VERIFY_SIGNATURE=False  # True in produzione

# SMTP Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_ENCRYPTION=STARTTLS  # SSL, STARTTLS, NONE

# Date Format
DATE_FORMAT=%d/%m/%Y %H:%M

# Messages - Launch & Menu
MSG_LAUNCH="Ciao, cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?"
MSG_MENU_FULL="Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
MSG_MENU_SHORT="Cosa vuoi fare?"

# Messages - Writing
MSG_START_WRITING="Dimmi pure."
MSG_NOTE_RECEIVED="Ricevuto. Altro?"
MSG_NOTE_SAVED="Salvato. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
MSG_NOTHING_SAID="Non hai detto nulla. Cosa vuoi fare ora?"
MSG_NOT_WRITING="Non stavo scrivendo. Cosa vuoi fare? Scrivi, Rileggi, Invia o Chiudi?"
MSG_PENDING_NOTE="Hai una nota in sospeso. Di 'Fine' per salvarla, o continua a dettare."
MSG_PENDING_NOTE_SEND="Hai una nota in sospeso. Di 'Fine' per salvarla prima di inviare."
MSG_WRITING_IN_PROGRESS="Stai scrivendo. Di 'Fine' quando hai finito."

# Messages - Reading
MSG_NO_NOTES="Non hai ancora salvato nessuna nota. Cosa vuoi fare?"
MSG_READ_NOTES_PREFIX="Ecco le tue ultime note: "
MSG_NOTE_FORMAT="Nota {num} del {date}: {content}"

# Messages - Email
MSG_EMAIL_SENT="Email inviata. Cosa vuoi fare ora? Scrivi, Rileggi, Invia o Chiudi?"
MSG_EMAIL_PERMISSION="Per inviare le note, ho bisogno del permesso di accedere alla tua email. Ho inviato una scheda alla tua app Alexa. Per favore abilita i permessi nelle impostazioni."
MSG_EMAIL_NOT_FOUND="Non riesco a trovare il tuo indirizzo email. Controlla le impostazioni."
MSG_NO_NOTES_TO_SEND="Non ci sono note da inviare."
MSG_EMAIL_ERROR="C'è stato un errore nell'invio dell'email."
MSG_EMAIL_SUBJECT="Le tue note Alexa"
MSG_EMAIL_BODY_PREFIX="Ecco le tue note:\n\n"

# Messages - Configuration
MSG_CONFIG_AUTO_DELETE_QUESTION="È possibile attivare la cancellazione automatica delle note dopo un periodo che definisci. Vuoi attivare la cancellazione automatica?"
MSG_CONFIG_DAYS_QUESTION="Dopo quanti giorni dovrò cancellare le note?"
MSG_CONFIG_SAVED_ENABLED="Configurazione salvata. La cancellazione automatica è attiva dopo {days} giorni. Cosa vuoi fare ora?"
MSG_CONFIG_SAVED_DISABLED="Configurazione salvata. La cancellazione automatica è disattivata. Cosa vuoi fare ora?"
MSG_CONFIG_INVALID_NUMBER="Non ho capito il numero. Dopo quanti giorni dovrò cancellare le note?"

# Messages - Retention
MSG_RETENTION_SET="Ho impostato la scadenza a {days} giorni."
MSG_CLEANUP_DONE="Ho cancellato {count} vecchie note."

# Messages - General
MSG_HELP="Puoi dirmi di scrivere una nota o di rileggere le tue note. Cosa vuoi fare?"
MSG_NOT_UNDERSTOOD="Non ho capito. Vuoi scrivere, rileggere o inviare?"
MSG_GOODBYE="Arrivederci!"
MSG_ERROR="Scusa, ho avuto un problema. Riprova."
MSG_SMTP_CONFIG_ERROR="Errore di configurazione del server email."
```

### Caricamento Variabili
```python
from dotenv import load_dotenv
import os

# Carica .env PRIMA di importare altri moduli
load_dotenv(override=True)

# Accesso variabili con fallback
MSG_LAUNCH = os.environ.get("MSG_LAUNCH", "Default message")
```

---

## 11. Guida all'Implementazione Passo-Passo

### FASE 1: Setup Progetto (30 minuti)

#### Step 1.1: Creare Struttura Directory
```bash
mkdir alexa-blocco-note
cd alexa-blocco-note
```

#### Step 1.2: Creare requirements.txt
```
flask==2.3.0
python-dotenv==1.0.0
ask-sdk-core==1.18.0
ask-sdk-webservice-support==1.18.0
```

#### Step 1.3: Installare Dipendenze
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

#### Step 1.4: Creare .env
Copiare il template dalla sezione 10 e personalizzare.

---

### FASE 2: Implementare Database Layer (45 minuti)

#### Step 2.1: Creare database.py
```python
import sqlite3
import os

DB_NAME = "notes.db"
```

#### Step 2.2: Implementare init_db()
- Creare tabella `notes`
- Creare tabella `user_settings`
- Gestire ALTER TABLE per backward compatibility

#### Step 2.3: Implementare Funzioni CRUD
Nell'ordine:
1. `save_note(text, user_id)`
2. `get_notes(user_id, limit=5)`
3. `get_all_notes(user_id)`

#### Step 2.4: Implementare Funzioni Configurazione
1. `set_auto_delete_config(user_id, enabled, days=None)`
   - **IMPORTANTE**: Default 7 giorni se None
2. `get_auto_delete_config(user_id)`
   - Ritorna tupla (enabled: bool, days: int|None)

#### Step 2.5: Implementare Cleanup
1. `cleanup_old_notes(user_id)`
   - Controllare enabled flag
   - Usare datetime SQLite per calcolo

#### Step 2.6: Testare Database
```python
# Test script
if __name__ == "__main__":
    init_db()
    save_note("Test note", "user123")
    notes = get_notes("user123")
    print(notes)
```

---

### FASE 3: Creare Modello Interazione Alexa (30 minuti)

#### Step 3.1: Creare skill.json
Struttura base:
```json
{
    "interactionModel": {
        "languageModel": {
            "invocationName": "il mio blocco note",
            "intents": [],
            "types": []
        }
    }
}
```

#### Step 3.2: Aggiungere Intent Built-in
- AMAZON.CancelIntent
- AMAZON.HelpIntent
- AMAZON.StopIntent
- AMAZON.NavigateHomeIntent
- AMAZON.YesIntent
- AMAZON.NoIntent

#### Step 3.3: Aggiungere Intent Personalizzati
Nell'ordine (vedi sezione 5):
1. StartWritingIntent
2. CaptureNoteIntent
3. FinishIntent
4. ReadNotesIntent
5. SendEmailIntent
6. ConfigureIntent
7. SetRetentionIntent
8. CloseIntent

#### Step 3.4: Definire Tipo NoteType
Aggiungere esempi di note comuni.

---

### FASE 4: Implementare Flask App Base (30 minuti)

#### Step 4.1: Creare main.py - Imports
```python
from flask import Flask, request
from dotenv import load_dotenv
import os
import logging

load_dotenv(override=True)

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler, AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.api_client import DefaultApiClient
from ask_sdk_model import Response
from ask_sdk_webservice_support.webservice_handler import WebserviceSkillHandler
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
import database
```

#### Step 4.2: Inizializzare Flask e SkillBuilder
```python
app = Flask(__name__)
sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

database.init_db()
```

#### Step 4.3: Caricare Messaggi da .env
Creare costanti MSG_* per tutti i messaggi (vedi sezione 10).

#### Step 4.4: Implementare get_user_id()
```python
def get_user_id(handler_input):
    return handler_input.request_envelope.session.user.user_id
```

---

### FASE 5: Implementare Handler Base (1 ora)

#### Step 5.1: LaunchRequestHandler
```python
class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("LaunchRequest")(handler_input)
    
    def handle(self, handler_input):
        user_id = get_user_id(handler_input)
        deleted = database.cleanup_old_notes(user_id)
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} old notes")
        
        speak_output = MSG_LAUNCH
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
```

#### Step 5.2: HelpIntentHandler
```python
class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.HelpIntent")(handler_input)
    
    def handle(self, handler_input):
        return (
            handler_input.response_builder
                .speak(MSG_HELP)
                .ask(MSG_HELP)
                .response
        )
```

#### Step 5.3: CancelOrStopIntentHandler
```python
class CancelOrStopIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))
    
    def handle(self, handler_input):
        return handler_input.response_builder.speak(MSG_GOODBYE).response
```

#### Step 5.4: SessionEndedRequestHandler
```python
class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_request_type("SessionEndedRequest")(handler_input)
    
    def handle(self, handler_input):
        return handler_input.response_builder.response
```

#### Step 5.5: CatchAllExceptionHandler
```python
class CatchAllExceptionHandler(AbstractExceptionHandler):
    def can_handle(self, handler_input, exception):
        return True
    
    def handle(self, handler_input, exception):
        logger.error(exception, exc_info=True)
        return (
            handler_input.response_builder
                .speak(MSG_ERROR)
                .ask(MSG_ERROR)
                .response
        )
```

---

### FASE 6: Implementare Flusso Scrittura Note (1 ora)

#### Step 6.1: StartWritingIntentHandler
```python
class StartWritingIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("StartWritingIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["state"] = "WRITING"
        session_attr["note_buffer"] = []
        
        return (
            handler_input.response_builder
                .speak(MSG_START_WRITING)
                .ask(MSG_START_WRITING)
                .response
        )
```

#### Step 6.2: CaptureNoteIntentHandler
**IMPORTANTE**: Gestire sia WRITING che CONFIG_DAYS_QUESTION

```python
class CaptureNoteIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CaptureNoteIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        state = session_attr.get("state")
        config_state = session_attr.get("config_state")
        
        # Gestione configurazione giorni
        if config_state == "DAYS_QUESTION":
            slots = handler_input.request_envelope.request.intent.slots
            note_text = slots["note"].value if slots["note"].value else ""
            
            import re
            numbers = re.findall(r'\d+', note_text)
            
            if numbers:
                days = int(numbers[0])
                user_id = get_user_id(handler_input)
                auto_delete_enabled = session_attr.get("auto_delete_enabled", True)
                
                database.set_auto_delete_config(user_id, enabled=auto_delete_enabled, days=days)
                
                session_attr["config_state"] = None
                session_attr["auto_delete_enabled"] = False
                
                speak_output = MSG_CONFIG_SAVED_ENABLED.format(days=days)
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(speak_output)
                        .response
                )
            else:
                speak_output = MSG_CONFIG_INVALID_NUMBER
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(speak_output)
                        .response
                )
        
        # Gestione scrittura note
        if state == "WRITING":
            slots = handler_input.request_envelope.request.intent.slots
            note_text = slots["note"].value if slots["note"].value else ""
            
            # Check finish keywords
            finish_keywords = ["fine", "finito", "basta", "ho finito"]
            if note_text.lower().strip() in finish_keywords:
                user_id = get_user_id(handler_input)
                buffer = session_attr.get("note_buffer", [])
                full_note = " ".join(buffer)
                
                if full_note:
                    database.save_note(full_note, user_id)
                    speak_output = MSG_NOTE_SAVED
                else:
                    speak_output = MSG_NOTHING_SAID
                
                session_attr["state"] = "MENU"
                session_attr["note_buffer"] = []
                
                return (
                    handler_input.response_builder
                        .speak(speak_output)
                        .ask(speak_output)
                        .response
                )
            
            # Normal capture
            buffer = session_attr.get("note_buffer", [])
            buffer.append(note_text)
            session_attr["note_buffer"] = buffer
            
            logger.info(f"Added '{note_text}' to buffer")
            
            return (
                handler_input.response_builder
                    .speak(MSG_NOTE_RECEIVED)
                    .ask(MSG_NOTE_RECEIVED)
                    .response
            )
        else:
            return (
                handler_input.response_builder
                    .speak(MSG_NOT_UNDERSTOOD)
                    .ask(MSG_NOT_UNDERSTOOD)
                    .response
            )
```

#### Step 6.3: FinishIntentHandler
```python
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
            
            session_attr["state"] = "MENU"
            session_attr["note_buffer"] = []
            
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .response
            )
        else:
            return (
                handler_input.response_builder
                    .speak(MSG_NOT_WRITING)
                    .ask(MSG_NOT_WRITING)
                    .response
            )
```

---

### FASE 7: Implementare Lettura Note (30 minuti)

#### Step 7.1: ReadNotesIntentHandler
```python
class ReadNotesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ReadNotesIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        state = session_attr.get("state")
        
        # Check if writing
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
        
        # Normal flow
        user_id = get_user_id(handler_input)
        notes_data = database.get_notes(user_id)
        
        if notes_data:
            date_format = os.environ.get("DATE_FORMAT", "%d/%m/%Y %H:%M")
            formatted_notes = []
            
            for i, (content, timestamp) in enumerate(notes_data, 1):
                try:
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                    formatted_date = dt.strftime(date_format)
                except Exception as e:
                    logger.error(f"Date parsing error: {e}")
                    formatted_date = timestamp
                
                formatted_notes.append(MSG_NOTE_FORMAT.format(
                    num=i, date=formatted_date, content=content
                ))
            
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
```

---

### FASE 8: Implementare Invio Email (1 ora)

#### Step 8.1: SendEmailIntentHandler
```python
class SendEmailIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SendEmailIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        state = session_attr.get("state")
        
        # Check if writing
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
        
        # Get user email
        svc_client_fact = handler_input.service_client_factory
        ups_service = svc_client_fact.get_ups_service()
        
        try:
            email_addr = ups_service.get_profile_email()
        except Exception as e:
            logger.error(f"Error fetching email: {e}", exc_info=True)
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
                dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                formatted_date = dt.strftime(date_format)
            except Exception as e:
                logger.error(f"Date parsing error: {e}")
                formatted_date = timestamp
            
            formatted_notes.append(f"{i}. [{formatted_date}] {content}")
        
        notes_text = "\n".join(formatted_notes)
        
        # Send email
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = int(os.environ.get("SMTP_PORT", 587))
        smtp_user = os.environ.get("SMTP_USER", "").strip() or None
        smtp_password = os.environ.get("SMTP_PASSWORD", "").strip() or None
        smtp_encryption = os.environ.get("SMTP_ENCRYPTION", "STARTTLS").upper()
        
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
            
            logger.info(f"Sending email to {email_addr}")
            
            if smtp_encryption == "SSL":
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            elif smtp_encryption == "STARTTLS":
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    if smtp_user and smtp_password:
                        server.login(smtp_user, smtp_password)
                    server.send_message(msg)
            
            logger.info("Email sent successfully")
            speak_output = MSG_EMAIL_SENT
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return (
                handler_input.response_builder
                    .speak(MSG_EMAIL_ERROR)
                    .response
            )
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )
```

---

### FASE 9: Implementare Configurazione (1 ora)

#### Step 9.1: ConfigureIntentHandler
```python
class ConfigureIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("ConfigureIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["config_state"] = "AUTO_DELETE_QUESTION"
        
        return (
            handler_input.response_builder
                .speak(MSG_CONFIG_AUTO_DELETE_QUESTION)
                .ask(MSG_CONFIG_AUTO_DELETE_QUESTION)
                .response
        )
```

#### Step 9.2: YesIntentHandler
```python
class YesIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.YesIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        config_state = session_attr.get("config_state")
        
        if config_state == "AUTO_DELETE_QUESTION":
            session_attr["config_state"] = "DAYS_QUESTION"
            session_attr["auto_delete_enabled"] = True
            
            return (
                handler_input.response_builder
                    .speak(MSG_CONFIG_DAYS_QUESTION)
                    .ask(MSG_CONFIG_DAYS_QUESTION)
                    .response
            )
        else:
            return (
                handler_input.response_builder
                    .speak(MSG_NOT_UNDERSTOOD)
                    .ask(MSG_NOT_UNDERSTOOD)
                    .response
            )
```

#### Step 9.3: NoIntentHandler
```python
class NoIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("AMAZON.NoIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        config_state = session_attr.get("config_state")
        
        if config_state == "AUTO_DELETE_QUESTION":
            user_id = get_user_id(handler_input)
            database.set_auto_delete_config(user_id, enabled=False)
            
            session_attr["config_state"] = None
            session_attr["auto_delete_enabled"] = False
            
            return (
                handler_input.response_builder
                    .speak(MSG_CONFIG_SAVED_DISABLED)
                    .ask(MSG_CONFIG_SAVED_DISABLED)
                    .response
            )
        else:
            return (
                handler_input.response_builder
                    .speak(MSG_NOT_UNDERSTOOD)
                    .ask(MSG_NOT_UNDERSTOOD)
                    .response
            )
```

#### Step 9.4: SetRetentionIntentHandler (Legacy)
```python
class SetRetentionIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("SetRetentionIntent")(handler_input)
    
    def handle(self, handler_input):
        slots = handler_input.request_envelope.request.intent.slots
        days_slot = slots.get("days")
        days = days_slot.value if days_slot else None
        
        if days:
            try:
                days_int = int(days)
                user_id = get_user_id(handler_input)
                database.set_retention_days(user_id, days_int)
                speak_output = MSG_RETENTION_SET.format(days=days_int)
            except ValueError:
                speak_output = MSG_ERROR
        else:
            from ask_sdk_model.dialog import ElicitSlotDirective
            speak_output = "Per quanti giorni vuoi conservare le note?"
            return (
                handler_input.response_builder
                    .speak(speak_output)
                    .ask(speak_output)
                    .add_directive(
                        ElicitSlotDirective(
                            slot_to_elicit="days",
                            updated_intent=handler_input.request_envelope.request.intent
                        )
                    )
                    .response
            )
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(MSG_MENU_SHORT)
                .response
        )
```

#### Step 9.5: CloseIntentHandler
```python
class CloseIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        return is_intent_name("CloseIntent")(handler_input)
    
    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        if session_attr.get("state") == "WRITING":
            session_attr["state"] = "MENU"
            session_attr["note_buffer"] = []
        
        # Silent exit
        return handler_input.response_builder.response
```

---

### FASE 10: Registrazione Handler e Flask Setup (30 minuti)

#### Step 10.1: Registrare Handler (ORDINE CRITICO)
```python
# Register handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(StartWritingIntentHandler())
sb.add_request_handler(YesIntentHandler())          # PRIMA di CaptureNote
sb.add_request_handler(NoIntentHandler())           # PRIMA di CaptureNote
sb.add_request_handler(CaptureNoteIntentHandler())
sb.add_request_handler(FinishIntentHandler())
sb.add_request_handler(ReadNotesIntentHandler())
sb.add_request_handler(SendEmailIntentHandler())
sb.add_request_handler(SetRetentionIntentHandler())
sb.add_request_handler(ConfigureIntentHandler())
sb.add_request_handler(CloseIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())
```

#### Step 10.2: Configurare Skill
```python
verify_signature = os.environ.get("VERIFY_SIGNATURE", "True").lower() == "true"
skill = sb.create()
skill.api_client = DefaultApiClient()
skill_adapter = WebserviceSkillHandler(
    skill=skill, 
    verify_signature=verify_signature, 
    verify_timestamp=verify_signature
)
```

#### Step 10.3: Creare Route Flask
```python
@app.route("/", methods=['POST'])
def invoke_skill():
    return skill_adapter.verify_request_and_dispatch(request.headers, request.data)

if __name__ == '__main__':
    app.run(debug=True)
```

---

### FASE 11: Testing e Deployment (1 ora)

#### Step 11.1: Test Locale con ngrok
```bash
# Terminal 1
python3 main.py

# Terminal 2
ngrok http 5000
```

#### Step 11.2: Configurare Alexa Developer Console
1. Creare nuova skill
2. Impostare invocation name: "il mio blocco note"
3. Copiare skill.json nel JSON Editor
4. Build model
5. Configurare endpoint HTTPS (ngrok URL)
6. Testare con Alexa Simulator

#### Step 11.3: Test Flussi Critici
1. **Scrittura nota**: "scrivi" → "test" → "fine"
2. **Lettura**: "rileggi"
3. **Configurazione**: "configura" → "sì" → "7"
4. **Email**: "invia" (richiede permessi)
5. **Chiusura**: "chiudi"

#### Step 11.4: Verificare Database
```bash
sqlite3 notes.db
.tables
SELECT * FROM notes;
SELECT * FROM user_settings;
.quit
```

---

## Checklist Finale Pre-Deployment

### Database
- [ ] Tabelle create correttamente
- [ ] Indici su user_id per performance
- [ ] Backup automatico configurato

### Codice
- [ ] Tutti gli handler implementati
- [ ] Ordine handler corretto (Yes/No prima di CaptureNote)
- [ ] Logging configurato
- [ ] Gestione errori completa

### Configurazione
- [ ] .env configurato correttamente
- [ ] SMTP testato
- [ ] Messaggi personalizzati
- [ ] VERIFY_SIGNATURE=True in produzione

### Testing
- [ ] Tutti i flussi testati
- [ ] Gestione stati verificata
- [ ] Multi-utente testato
- [ ] Auto-cleanup verificato

### Sicurezza
- [ ] .env in .gitignore
- [ ] Signature verification abilitata
- [ ] Credenziali SMTP sicure
- [ ] Permessi Alexa configurati

---

## Ottimizzazioni Avanzate (Opzionali)

### Performance
1. **Connection Pooling**: Usare `sqlite3.connect()` con pool
2. **Indici Database**: Aggiungere indici su `user_id` e `timestamp`
3. **Caching**: Cache configurazione utente in memoria

### UX
1. **Conferme Brevi**: Ridurre verbosità risposte
2. **Suggerimenti Contestuali**: Adattare menu al contesto
3. **Gestione Errori Vocali**: Migliorare parsing numeri

### Scalabilità
1. **Database Remoto**: Migrare a PostgreSQL/MySQL
2. **Session Storage**: Redis per attributi sessione
3. **Logging Centralizzato**: CloudWatch/Elasticsearch

---

## Troubleshooting Comune

### Problema: "sì" catturato da CaptureNoteIntent
**Soluzione**: Verificare ordine handler, YesIntent PRIMA di CaptureNote

### Problema: NOT NULL constraint failed
**Soluzione**: Usare default value (7) in `set_auto_delete_config`

### Problema: Email non inviata
**Soluzione**: 
- Verificare SMTP_SERVER, SMTP_PORT
- Controllare credenziali
- Testare encryption mode (SSL/STARTTLS/NONE)

### Problema: Note non cancellate automaticamente
**Soluzione**:
- Verificare `auto_delete_enabled = 1`
- Controllare `retention_days` non NULL
- Testare `cleanup_old_notes()` manualmente

---

## Conclusione

Questo piano fornisce una guida completa per implementare l'Alexa Skill "Il Mio Blocco Note" da zero. Seguendo le fasi nell'ordine indicato e prestando attenzione ai punti critici evidenziati (ordine handler, gestione stati, configurazione database), si otterrà un'applicazione funzionale e robusta.

**Tempo stimato totale**: 6-8 ore per sviluppatore esperto

**Punti critici da ricordare**:
1. YesIntent/NoIntent PRIMA di CaptureNoteIntent
2. Default value (7) per retention_days quando auto-delete disabilitato
3. Controllo enabled flag in cleanup_old_notes
4. Gestione stati sessione per flussi multi-step
5. Parsing numeri con regex per input vocale

Buon sviluppo! 🚀
