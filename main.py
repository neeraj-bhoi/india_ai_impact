from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional
import re
import os

API_KEY = os.getenv("API_KEY")


app = FastAPI(title="Agentic Honey-Pot API")

conversation_store = {}

def detect_scam_type(text: str):
    text = text.lower()

    if any(word in text for word in ["bank", "account", "upi", "otp", "verify"]):
        return "BANK_FRAUD"

    if any(word in text for word in ["job", "hr", "interview", "salary", "offer"]):
        return "JOB_SCAM"

    if any(word in text for word in ["crypto", "bitcoin", "investment", "trading"]):
        return "CRYPTO_SCAM"

    return "UNKNOWN"


def generate_persona_reply(scam_type: str):
    if scam_type == "BANK_FRAUD":
        return "Sir, I don’t understand these bank things. My salary just came. Will money go away?"

    if scam_type == "JOB_SCAM":
        return "Please help me. I really need this job. What documents should I send first?"

    if scam_type == "CRYPTO_SCAM":
        return "I am new to crypto. Is this safe? My friend lost money before."

    return "Okay"


def extract_intelligence(text: str):
    bank_accounts = re.findall(r"\b\d{9,18}\b", text)
    upi_ids = re.findall(r"\b[a-zA-Z0-9._-]+@[a-zA-Z]+\b", text)
    phishing_links = re.findall(r"https?://\S+", text)

    return {
        "bank_accounts": list(set(bank_accounts)),
        "upi_ids": list(set(upi_ids)),
        "phishing_links": list(set(phishing_links))
    }


class ScamMessage(BaseModel):
    conversation_id: str
    message: str


@app.get("/honeypot")
def honeypot_status():
    return {
        "status": "Honeypot API is live. Use POST /honeypot to send messages."
    }


@app.post("/honeypot")
def honeypot_endpoint(
    data: ScamMessage,
    x_api_key: Optional[str] = Header(None)
):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    history = conversation_store.get(data.conversation_id, [])
    history.append(data.message)
    conversation_store[data.conversation_id] = history

    full_text = " ".join(history)

    scam_type = detect_scam_type(full_text)
    scam_detected = scam_type != "UNKNOWN"
    intelligence = extract_intelligence(full_text)

    persona_map = {
        "BANK_FRAUD": "confused_salaried_user",
        "JOB_SCAM": "desperate_final_year_student",
        "CRYPTO_SCAM": "curious_tech_newbie",
        "UNKNOWN": "normal_user"
    }

    return {
        "conversation_id": data.conversation_id,
        "scam_detected": scam_detected,
        "scam_type": scam_type,
        "persona": persona_map.get(scam_type),
        "engagement": {
            "turns": len(history),
            "status": "active" if scam_detected else "monitoring"
        },
        "extracted_intelligence": intelligence,
        "reply_to_scammer": generate_persona_reply(scam_type)
    }
