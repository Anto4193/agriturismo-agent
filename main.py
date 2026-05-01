"""
Agente AI - Agriturismo
Riceve mail inoltrate, le analizza con Claude, manda riassunto su WhatsApp.
"""

import os
import json
import anthropic
from flask import Flask, request, jsonify
from twilio.rest import Client as TwilioClient
from datetime import datetime

app = Flask(__name__)

# Clienti API (le chiavi vengono da variabili d'ambiente su Railway)
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
twilio = TwilioClient(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])

WHATSAPP_TO   = os.environ["WHATSAPP_TO"]    # es. whatsapp:+393331234567
WHATSAPP_FROM = os.environ["WHATSAPP_FROM"]  # numero Twilio Sandbox


# ── Prompt di sistema ────────────────────────────────────────────────────────

SYSTEM_PROMPT = """Sei l'assistente AI di un agriturismo in Piemonte.
Il tuo compito è analizzare le email degli ospiti e produrre un JSON strutturato.

Rispondi SOLO con JSON valido, nessun testo extra. Formato:

{
  "mittente": "Nome Cognome",
  "email": "indirizzo@email.com",
  "lingua": "italiano|tedesco|inglese|francese|altro",
  "tipo": "richiesta_preventivo|prenotazione|info_generale|modifica|cancellazione|altro",
  "urgenza": "alta|normale|bassa",
  "riassunto": "2-3 righe in italiano, chiare e dirette",
  "dati_soggiorno": {
    "arrivo": "YYYY-MM-DD o null",
    "partenza": "YYYY-MM-DD o null",
    "notti": 0,
    "adulti": 0,
    "bambini": 0,
    "camera_richiesta": "descrizione o null"
  },
  "servizi_richiesti": ["colazione", "cena", "degustazione", "altro"],
  "azioni_suggerite": [
    "Rispondere con preventivo in tedesco",
    "Verificare disponibilità camera doppia con balcone"
  ],
  "risposta_bozza": "Bozza di risposta nella lingua dell'ospite, professionale e calorosa"
}"""


# ── Analisi mail con Claude ───────────────────────────────────────────────────

def analizza_mail(testo_mail: str) -> dict:
    """Manda il testo della mail a Claude e ottieni JSON strutturato."""
    risposta = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Analizza questa email:\n\n{testo_mail}"}]
    )
    testo = risposta.content[0].text.strip()
    # Rimuovi eventuali backtick markdown
    testo = testo.replace("```json", "").replace("```", "").strip()
    return json.loads(testo)


# ── Formatta messaggio WhatsApp ───────────────────────────────────────────────

def formatta_whatsapp(dati: dict) -> str:
    """Crea un messaggio WhatsApp leggibile dal telefono."""
    urgenza_emoji = {"alta": "🔴", "normale": "🟡", "bassa": "🟢"}.get(dati.get("urgenza"), "⚪")
    tipo_label = {
        "richiesta_preventivo": "💶 Preventivo",
        "prenotazione":         "✅ Prenotazione",
        "info_generale":        "ℹ️ Info",
        "modifica":             "✏️ Modifica",
        "cancellazione":        "❌ Cancellazione",
        "altro":                "📧 Mail",
    }.get(dati.get("tipo"), "📧 Mail")

    soggiorno = dati.get("dati_soggiorno", {})
    arrivo    = soggiorno.get("arrivo") or "—"
    partenza  = soggiorno.get("partenza") or "—"
    notti     = soggiorno.get("notti") or "—"
    adulti    = soggiorno.get("adulti") or "—"
    camera    = soggiorno.get("camera_richiesta") or "—"

    azioni = "\n".join(f"  • {a}" for a in dati.get("azioni_suggerite", []))

    ora = datetime.now().strftime("%H:%M")

    return f"""🌿 *Agriturismo — Nuova mail* ({ora})

{urgenza_emoji} {tipo_label} da *{dati.get('mittente', '?')}*
🌍 Lingua: {dati.get('lingua', '?').capitalize()}

📋 *Riassunto*
{dati.get('riassunto', '—')}

🗓️ *Soggiorno*
Arrivo: {arrivo}  →  Partenza: {partenza}
Notti: {notti}  |  Adulti: {adulti}
Camera: {camera}

✅ *Da fare*
{azioni}

💬 _Rispondi "bozza" per ricevere la bozza di risposta._"""


# ── Endpoint per le mail inoltrate (Webhook) ──────────────────────────────────

@app.route("/mail", methods=["POST"])
def ricevi_mail():
    """
    Apple Mail inoltra qui le mail degli ospiti.
    Accetta sia JSON che form-data (da servizi come Mailgun/Cloudmailbox).
    """
    # Supporta JSON e form-data
    if request.is_json:
        payload = request.get_json()
        testo   = payload.get("body-plain") or payload.get("text") or payload.get("body", "")
    else:
        testo = request.form.get("body-plain") or request.form.get("text", "")

    if not testo:
        return jsonify({"errore": "Nessun testo nella mail"}), 400

    try:
        dati    = analizza_mail(testo)
        messaggio = formatta_whatsapp(dati)

        # Manda WhatsApp
        twilio.messages.create(
            body=messaggio,
            from_=WHATSAPP_FROM,
            to=WHATSAPP_TO
        )

        # Salva localmente (poi sostituiremo con database)
        salva_ospite(dati)

        return jsonify({"ok": True, "mittente": dati.get("mittente")}), 200

    except json.JSONDecodeError as e:
        return jsonify({"errore": f"Claude non ha risposto in JSON: {e}"}), 500
    except Exception as e:
        return jsonify({"errore": str(e)}), 500


# ── Endpoint per ricevere "bozza" da WhatsApp ────────────────────────────────

@app.route("/whatsapp", methods=["POST"])
def rispondi_whatsapp():
    """Twilio manda qui i tuoi messaggi WhatsApp in entrata."""
    corpo = request.form.get("Body", "").strip().lower()

    if corpo == "bozza":
        # Recupera l'ultima bozza salvata
        ultima = leggi_ultima_bozza()
        risposta = ultima if ultima else "Nessuna bozza disponibile al momento."
    else:
        risposta = "Comandi: *bozza* → ultima bozza di risposta pronta."

    twilio.messages.create(
        body=risposta,
        from_=WHATSAPP_FROM,
        to=request.form.get("From")
    )
    return "", 204


# ── Persistenza minima (file JSON locale) ─────────────────────────────────────

ARCHIVIO = "ospiti.json"

def salva_ospite(dati: dict):
    try:
        archivio = json.load(open(ARCHIVIO)) if os.path.exists(ARCHIVIO) else []
    except Exception:
        archivio = []
    dati["_timestamp"] = datetime.now().isoformat()
    archivio.append(dati)
    with open(ARCHIVIO, "w") as f:
        json.dump(archivio, f, ensure_ascii=False, indent=2)

def leggi_ultima_bozza() -> str:
    try:
        archivio = json.load(open(ARCHIVIO))
        if archivio:
            return archivio[-1].get("risposta_bozza", "Nessuna bozza.")
    except Exception:
        pass
    return "Nessuna bozza disponibile."


# ── Avvio ─────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def health():
    return jsonify({"stato": "attivo", "agente": "Agriturismo AI"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
