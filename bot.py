"""BotEngine: WhatsApp AI customer-support bot logic (per-business template)."""
import json
import os

import requests

BASE = os.path.dirname(os.path.abspath(__file__))


class BotEngine:
    def __init__(self, business_id="demo_shop"):
        path = os.path.join(BASE, "businesses", f"{business_id}.json")
        with open(path, encoding="utf-8") as f:
            self.cfg = json.load(f)
        self.business_id = business_id
        self.gemini_key = os.environ.get("GEMINI_API_KEY", "")

    # ---------- main entry ----------
    def reply(self, text):
        t = text.strip().lower()

        if t in ("hi", "hello", "salam", "assalamualaikum", "aoa", "start"):
            return self.cfg["welcome"]

        if any(k in t for k in ("catalog", "product", "menu", "price", "rate", "item")):
            return self.catalog_text()

        if any(k in t for k in ("order", "buy", "book")):
            return self.cfg.get("order_info", "")

        if any(k in t for k in ("human", "agent", "call", "contact", "number", "insan")):
            return self.cfg.get("handoff", "")

        for faq in self.cfg.get("faqs", []):
            for kw in faq["keywords"]:
                if kw.lower() in t:
                    return faq["answer"]

        return self.ai_reply(text)

    # ---------- helpers ----------
    def catalog_text(self):
        lines = ["*{}* - Product Catalog:".format(self.cfg["name"])]
        for p in self.cfg.get("catalog", []):
            lines.append("- {} - Rs {}".format(p["name"], p["price"]))
        lines.append("Reply with the product name to order.")
        return "\n".join(lines)

    def ai_reply(self, text):
        if not self.gemini_key:
            return self.cfg.get(
                "fallback",
                "Sorry, I did not understand. Type 'catalog' for products or 'human' to talk to our team.",
            )
        prompt = (
            "You are the customer support assistant for {name}. {about}\n"
            "FAQs: {faqs}\nCatalog: {catalog}\n"
            "Customer asked: {q}\n"
            "Answer briefly (under 60 words), friendly, in the customer's language. "
            "If you do not know the answer, say you will connect them to a human."
        ).format(
            name=self.cfg["name"],
            about=self.cfg.get("about", ""),
            faqs=json.dumps(self.cfg.get("faqs", [])),
            catalog=json.dumps(self.cfg.get("catalog", [])),
            q=text,
        )
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent"
            r = requests.post(
                url,
                params={"key": self.gemini_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=20,
            )
            data = r.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:  # noqa: BLE001 - fall back gracefully
            print("AI error:", e)
            return self.cfg.get("fallback", "Sorry, please type 'human' to talk to our team.")
