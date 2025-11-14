# heuristics.py 
import re
import time
from typing import List, Dict, Any, Optional

# ----------------------------
# Severity / Action constants
# ----------------------------
BLOCK = "BLOCK"    # do not proceed
WARN = "WARN"      # proceed but warn the user / log
RETRY = "RETRY"    # retry action (may include pause)
OK = "OK"          # no issue

# ----------------------------
# PII / Profanity / Unsafe lists
# ----------------------------
PII_PATTERNS = [
    r"\b\d{12}\b",                         # Aadhaar-like
    r"\b\d{3}-\d{2}-\d{4}\b",              # SSN
    r"\b\d{10}\b",                         # 10-digit phone numbers
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",  # email
    r"\b[A-Z]{5}\d{4}[A-Z]\b",             # PAN-like
    r"\b\d{16}\b",                         # credit card-like
]

BAD_WORDS = {
    "fuck", "shit", "bitch", "bastard", "asshole",
    "dick", "crap", "bloody", "slut"
}

UNSAFE_DOMAINS = [
    "darkweb", "onion", "tor2web", "malware", "phishing",
    "clickme", "hacktool", "pirated", "crackdownload"
]

# ----------------------------
# Low-level heuristics
# ----------------------------
def is_tool_not_available(tool_name: str, available_tools: Optional[List[str]]) -> bool:
    if not tool_name:
        return False
    if available_tools is None:
        return True
    return tool_name not in available_tools

def has_incomplete_perception(perception: Optional[str]) -> bool:
    if perception is None:
        return True
    text = perception.strip().lower()
    return text in ("", "none", "no observation", "no context available") or len(text.split()) < 3

def contains_pii(text: str) -> bool:
    if not text:
        return False
    for pattern in PII_PATTERNS:
        if re.search(pattern, text):
            return True
    return False

def detect_model_overload(error_message: Optional[str]) -> Optional[Dict[str, Any]]:
    if not error_message:
        return None
    msg = error_message.lower()
    if "503" in msg or "service unavailable" in msg or "model overload" in msg or "overloaded" in msg:
        return {"retry": True, "pause_seconds": 20, "reason": "model overload / 503"}
    return None

def contains_profanity(query: str) -> bool:
    if not query:
        return False
    # simple token check + substring fallback
    tokens = re.findall(r"\w+", query.lower())
    if any(t in BAD_WORDS for t in tokens):
        return True
    # substring scan for obfuscated profanity
    ql = query.lower()
    return any(b in ql for b in BAD_WORDS)

def contains_unsafe_link(text: str) -> bool:
    if not text:
        return False
    urls = re.findall(r"(https?://[^\s]+)", text.lower())
    if not urls:
        # check for bare domains mention
        domains = re.findall(r"\b[\w\-]+\.(?:onion|zip|click|xyz|ru|cn)\b", text.lower())
        urls = domains
    for url in urls:
        if any(bad in url for bad in UNSAFE_DOMAINS):
            return True
        if url.endswith((".zip", ".onion", ".click")):
            return True
    return False

def handle_overload_and_retry(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        If model_overload details present, perform the pause and return status.
        (Synchronous sleep — call from orchestrator if you want active waiting.)
        """
        overload = details.get("model_overload")
        if not overload:
            return {"Overload": False}
        pause = overload.get("pause_seconds", 20)
        # perform the sleep/pause in-place
        time.sleep(pause)
        return {"Overload": True, "paused_seconds": pause}


