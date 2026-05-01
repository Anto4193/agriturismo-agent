# 🌿 Agriturismo AI — Guida all'installazione

Questo agente riceve le mail degli ospiti, le analizza con Claude AI e ti manda
un riassunto su WhatsApp con la bozza di risposta già pronta.

---

## Cosa ti serve (tutto gratuito)

| Strumento | Cosa fa | Piano gratuito |
|-----------|---------|----------------|
| GitHub | Conserva il codice | ✅ Sì |
| Railway | Esegue l'agente 24/7 | ✅ Sì (500h/mese) |
| Twilio | Manda WhatsApp | ✅ Sì (sandbox) |
| Cloudmailbox | Riceve le mail inoltrate | ✅ Sì |
| Anthropic API | Analizza le mail con Claude | ~0,01€ per mail |

---

## Passo 1 — Carica il codice su GitHub

1. Vai su [github.com](https://github.com) e accedi al tuo account
2. Clicca **"New repository"** → nome: `agriturismo-agent`
3. Lascia tutto come default, clicca **"Create repository"**
4. Carica i file `main.py` e `requirements.txt` con il pulsante **"Add file → Upload files"**

---

## Passo 2 — Configura Twilio per WhatsApp

1. Vai su [twilio.com](https://twilio.com) e crea un account gratuito
2. Nel pannello, vai su **Messaging → Try it out → Send a WhatsApp message**
3. Segui le istruzioni per attivare la **Sandbox WhatsApp**
   - Ti verrà chiesto di mandare un messaggio da WhatsApp al numero Twilio
4. Annota questi valori (li userai dopo):
   - `TWILIO_ACCOUNT_SID` (nella homepage del pannello)
   - `TWILIO_AUTH_TOKEN` (nella homepage del pannello)
   - `WHATSAPP_FROM` = `whatsapp:+14155238886` (numero sandbox)
   - `WHATSAPP_TO` = `whatsapp:+39TUONUMERO`

---

## Passo 3 — Ottieni la chiave API Anthropic

1. Vai su [console.anthropic.com](https://console.anthropic.com)
2. Clicca **"API Keys" → "Create Key"**
3. Copia la chiave (inizia con `sk-ant-...`) — salvala, la vedrai solo una volta

---

## Passo 4 — Pubblica su Railway

1. Vai su [railway.app](https://railway.app) e accedi con il tuo account GitHub
2. Clicca **"New Project → Deploy from GitHub repo"**
3. Seleziona `agriturismo-agent`
4. Railway rileva automaticamente che è un'app Python e la avvia

### Aggiungi le variabili d'ambiente

Nel pannello Railway, vai su **Variables** e aggiungi:

```
ANTHROPIC_API_KEY    = sk-ant-...la tua chiave...
TWILIO_ACCOUNT_SID   = ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN    = xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
WHATSAPP_FROM        = whatsapp:+14155238886
WHATSAPP_TO          = whatsapp:+39TUONUMERO
```

5. Vai su **Settings → Networking → Generate Domain**
   - Railway ti darà un URL pubblico tipo: `agriturismo-agent.up.railway.app`
   - **Annotalo** — ti serve per i passaggi successivi

---

## Passo 5 — Configura Cloudmailbox (ricezione mail)

Cloudmailbox riceve le mail inoltrate da Apple Mail e le manda al tuo agente.

1. Vai su [cloudmailbox.io](https://cloudmailbox.io) e crea un account gratuito
2. Crea una casella di posta tipo: `ospiti@tuoagriturismo.cloudmailbox.io`
3. Nelle impostazioni, imposta il **Webhook URL**:
   ```
   https://agriturismo-agent.up.railway.app/mail
   ```

---

## Passo 6 — Configura Apple Mail per inoltrare

1. Apri **Mail** sul Mac
2. Vai su **Impostazioni → Regole → Aggiungi regola**
3. Condizione: **"Da" contiene** → lascia vuoto (oppure filtra per mittenti)
   - Oppure: **"Oggetto" non contiene** → "noreply" per escludere newsletter
4. Azione: **Inoltra a** → `ospiti@tuoagriturismo.cloudmailbox.io`
5. Clicca **OK**

Da questo momento ogni mail che ricevi viene analizzata automaticamente.

---

## Passo 7 — Configura il webhook WhatsApp in entrata

Per ricevere i tuoi comandi WhatsApp (es. "bozza"):

1. In Twilio, vai su **Messaging → Settings → WhatsApp Sandbox Settings**
2. Nel campo **"When a message comes in"** incolla:
   ```
   https://agriturismo-agent.up.railway.app/whatsapp
   ```
3. Metodo: **HTTP POST** → Salva

---

## Come funziona nella pratica

```
Ospite manda mail
      ↓
Apple Mail la riceve e la inoltra a Cloudmailbox
      ↓
Cloudmailbox chiama il tuo agente su Railway
      ↓
L'agente chiede a Claude di analizzarla
      ↓
Tu ricevi un WhatsApp con riassunto + azioni
      ↓
Rispondi "bozza" → ricevi la risposta già scritta
      ↓
Copi, controlli, invii
```

---

## Comandi WhatsApp disponibili

| Comando | Risposta |
|---------|----------|
| `bozza` | Ultima bozza di risposta pronta all'invio |

Altri comandi verranno aggiunti nelle fasi successive (es. `disponibilità`, `ospiti oggi`).

---

## Problemi comuni

**Non ricevo il WhatsApp**
→ Verifica che il tuo numero sia registrato nella Sandbox Twilio
→ Controlla le variabili d'ambiente su Railway

**Errore sul webhook**
→ Vai su Railway → Logs per vedere l'errore specifico
→ Verifica che l'URL del webhook finisca con `/mail`

**Claude non risponde**
→ Verifica che `ANTHROPIC_API_KEY` sia corretta e abbia credito

---

## Prossimi passi (Fase 3)

Nella prossima fase collegheremo **Wubook** per:
- Leggere disponibilità in tempo reale
- Generare preventivi automatici con prezzi variabili
- Aggiornare il calendario ospiti

---

*Generato da Claude AI — Aggiornato: giugno 2025*
