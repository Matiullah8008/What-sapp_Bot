# WhatsApp AI Customer-Support Bot (template)

Working, tested webhook bot for the WhatsApp Cloud API.
One business = one JSON file in `businesses/`. No data mixing.

## What is built and verified

- `app.py` — Flask webhook: GET verification + POST incoming messages, replies via Cloud API
- `bot.py` — BotEngine: welcome, catalog, order info, FAQ keyword match, human handoff, Gemini AI fallback
- `businesses/demo_shop.json` — demo business template (copy per client)
- `test_bot.py` — 8 automated tests, all passing (run: `python3 test_bot.py`)

## Run locally

```
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python test_bot.py      # tests (no credentials needed)
.venv/bin/python app.py            # start server on :5000
```

## Go live (needs YOUR Meta account - cannot be done by the bot)

1. developers.facebook.com -> create App (Business) -> add WhatsApp product
2. API Setup: note Phone Number ID + temporary access token; add your WhatsApp number, verify it
3. Deploy this code somewhere public with HTTPS (Render.com free tier works)
4. In API Setup -> Configuration: set Callback URL to `https://YOUR-SERVER/webhook`,
   Verify Token = your WHATSAPP_VERIFY_TOKEN, Subscribe to `messages` field
5. Copy `.env.example` to `.env`, fill tokens + GEMINI_API_KEY (free at aistudio.google.com)
6. Send a WhatsApp message to the test number -> bot replies

## New client = new JSON file

Copy `businesses/demo_shop.json` to `businesses/client_name.json`,
edit name/faqs/catalog/handoff, set `BUSINESS_ID=client_name`.
