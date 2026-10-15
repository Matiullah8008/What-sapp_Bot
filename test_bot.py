"""Local tests: simulate Meta webhook calls WITHOUT real WhatsApp credentials."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault("WHATSAPP_VERIFY_TOKEN", "test_secret")

import app as app_module  # noqa: E402

client = app_module.app.test_client()

captured = []  # (to, text) pairs "sent"


def fake_send(to, text):
    captured.append((to, text))
    return {"mocked": True}


app_module.send_whatsapp = fake_send

passed = failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print("PASS:", name)
    else:
        failed += 1
        print("FAIL:", name)


# 1. webhook verification - correct token
r = client.get("/webhook?hub.mode=subscribe&hub.verify_token=test_secret&hub.challenge=CHALLENGE123")
check("verify ok returns challenge", r.status_code == 200 and r.data.decode() == "CHALLENGE123")

# 2. webhook verification - wrong token
r = client.get("/webhook?hub.mode=subscribe&hub.verify_token=wrong&hub.challenge=x")
check("verify wrong token -> 403", r.status_code == 403)

# 3. incoming "hi" -> welcome
payload = {"entry": [{"changes": [{"value": {"messages": [
    {"from": "923001234567", "type": "text", "text": {"body": "hi"}}
]}}]}]}
r = client.post("/webhook", json=payload)
check("incoming hi -> 200 ok", r.status_code == 200)
check("welcome reply sent", captured and "Welcome to Demo General Store" in captured[-1][1])

# 4. incoming "catalog" -> product list
payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "catalog"
client.post("/webhook", json=payload)
check("catalog reply has products", "Basmati Rice 5kg" in captured[-1][1] and "Rs 1850" in captured[-1][1])

# 5. FAQ keyword match
payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "delivery time?"
client.post("/webhook", json=payload)
check("FAQ delivery answer", "24 hours" in captured[-1][1])

# 6. human handoff
payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "human"
client.post("/webhook", json=payload)
check("handoff reply", "0300-1234567" in captured[-1][1])

# 7. unknown question, no GEMINI key -> fallback
payload["entry"][0]["changes"][0]["value"]["messages"][0]["text"]["body"] = "do you sell cars?"
client.post("/webhook", json=payload)
check("fallback reply", "did not understand" in captured[-1][1])

# 8. non-text message ignored (no crash, no new send)
n = len(captured)
payload["entry"][0]["changes"][0]["value"]["messages"][0] = {
    "from": "923001234567", "type": "image", "image": {"id": "x"}}
r = client.post("/webhook", json=payload)
check("non-text ignored, still 200", r.status_code == 200 and len(captured) == n)

print("\n{} passed, {} failed".format(passed, failed))
sys.exit(1 if failed else 0)
