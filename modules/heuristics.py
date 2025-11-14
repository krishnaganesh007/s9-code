# # modules/heuristics.py
# import re
# import json
# from typing import Optional, Any, Dict, List

# # Standardized heuristic result
# def _hr(name: str, passed: bool, score: float, reason: str, action: str) -> Dict[str, Any]:
#     return {
#         "heuristic": name,
#         "pass": bool(passed),
#         "score": float(round(max(0.0, min(1.0, score)), 3)),
#         "reason": reason,
#         "actionable": action,
#     }


# # ---------------------------
# # QUERY-ONLY HEURISTICS
# # ---------------------------

# def heuristic_ambiguity_detection(query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Detects if the query is ambiguous / too short / likely to be misinterpreted.
#     - Flags queries that are very short (<8 chars), very few tokens (<3),
#       or use vague words (something, info about, tell me).
#     """
#     tokens = re.findall(r"\w+", query or "")
#     low_tokens = len(tokens) < 3
#     short_len = len(query.strip()) < 10
#     vague_words = bool(re.search(r"\b(info|something|things|stuff|anything|thing)\b", query, re.I))
#     score = 1.0
#     reason_parts = []
#     if low_tokens or short_len:
#         score -= 0.6
#         reason_parts.append("very short or few tokens")
#     if vague_words:
#         score -= 0.3
#         reason_parts.append("contains vague words")
#     passed = score > 0.4
#     reason = " & ".join(reason_parts) or "query looks specific"
#     action = "Ask clarifying question before processing" if not passed else "Proceed"
#     return _hr("ambiguity_detection", passed, score, reason, action)


# def heuristic_sensitive_info_in_query(query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Detect PII or account-like numbers in the query (emails, phone numbers, long digits).
#     """
#     email = bool(re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", query))
#     phone = bool(re.search(r"\b\d{6,15}\b", query)) and not bool(re.search(r"\bhttps?://", query))
#     file_path = bool(re.search(r"[A-Za-z]:\\|/home/|\/[^\s]+\.pdf", query))
#     score = 1.0
#     reasons = []
#     if email:
#         reasons.append("contains email")
#         score -= 0.4
#     if phone:
#         reasons.append("contains long digit sequence (possible account/phone)")
#         score -= 0.4
#     if file_path:
#         reasons.append("contains a file path (local file reference)")
#         score -= 0.1
#     passed = score > 0.6
#     action = "Redact or confirm before proceeding" if not passed else "OK"
#     return _hr("sensitive_info_detection", passed, score, "; ".join(reasons) or "no PII detected", action)


# def heuristic_tool_selection_hint(query: str, context: Optional[Dict] = None, available_tools: Optional[List[str]] = None) -> Dict[str, Any]:
#     """
#     Check if query contains domain keywords that map to known capabilities (websearch, documents, math, summarizer).
#     If available_tools provided, checks for potential mismatches.
#     """
#     kw_map = {
#         "websearch": r"\b(search|website|web|https?://|site:)\b",
#         "documents": r"\b(pdf|document|paper|report|upload|file|pages|extract)\b",
#         "math": r"\b(sum|log|exp|calculate|compute|solve|equation|value)\b",
#         "summarizer": r"\b(summariz|summary|summarise|tl;dr)\b",
#     }
#     hits = []
#     for tool, patt in kw_map.items():
#         if re.search(patt, query, re.I):
#             hits.append(tool)
#     score = min(1.0, 0.2 + 0.25 * len(hits))
#     reason = f"Detected suggested tools: {hits}" if hits else "No strong tool hint"
#     action = "Prefer tools: " + ", ".join(hits) if hits else "Let perception decide"
#     # If available_tools provided and none of hits are in available_tools, warn
#     if available_tools is not None and hits:
#         mismatch = [h for h in hits if h not in available_tools]
#         if mismatch:
#             return _hr("tool_selection_hint", False, 0.2, f"Suggested tools {hits} but not available: {mismatch}", f"Consider fallback tools among {available_tools}")
#     return _hr("tool_selection_hint", True, score, reason, action)


# # ---------------------------
# # RESULT-ONLY HEURISTICS
# # ---------------------------

# def heuristic_malformed_tool_output(result: Any, query: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Detect if the result looks like an error or malformed output (sandbox errors, Traceback, empty results).
#     """
#     if result is None:
#         return _hr("malformed_tool_output", False, 0.0, "result is None", "Investigate tool response or retry")
#     # String checks
#     if isinstance(result, str):
#         if "sandbox error" in result.lower() or "traceback" in result.lower() or result.strip() == "":
#             return _hr("malformed_tool_output", False, 0.0, "result contains error markers or empty string", "Inspect tool logs and tool implementation")
#     # Dict/list: attempt basic shape validation
#     if isinstance(result, dict):
#         if "error" in result or "exception" in result:
#             return _hr("malformed_tool_output", False, 0.0, "result dict contains error field", "Inspect tool output schema")
#     return _hr("malformed_tool_output", True, 1.0, "output shape appears normal", "OK")


# def heuristic_relevance_score(query: str, result: Any, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Basic lexical overlap between query and result. Returns low score if overlap small.
#     Works best when result is text or stringifiable.
#     """
#     if result is None:
#         return _hr("relevance_score", False, 0.0, "no result to compare", "Retry retrieval or inspect tools")
#     q_words = set(re.findall(r"\w{3,}", query.lower()))
#     # string representation
#     try:
#         if isinstance(result, (dict, list)):
#             text = json.dumps(result)
#         else:
#             text = str(result)
#     except Exception:
#         text = str(result)
#     r_words = set(re.findall(r"\w{3,}", text.lower()))
#     if not q_words:
#         return _hr("relevance_score", False, 0.0, "query had no keywords", "Ask for clarification")
#     overlap = q_words.intersection(r_words)
#     ratio = len(overlap) / max(1, len(q_words))
#     score = ratio
#     passed = score >= 0.3
#     reason = f"keyword overlap {len(overlap)}/{len(q_words)}"
#     action = "If low, re-run retrieval with stricter query or different tools"
#     return _hr("relevance_score", passed, score, reason, action)


# def heuristic_overconfidence_in_result(result: Any, query: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Detect hedging vs confident claims. If output is a single sentence authoritative claim but lacks sources, warn.
#     Very heuristic: triggers if text uses definitive verbs and no 'source' mentions.
#     """
#     if not isinstance(result, str):
#         return _hr("overconfidence_in_result", True, 1.0, "non-string result (cannot evaluate confidence heuristically)", "OK")
#     # detect definite assertions
#     definitive = bool(re.search(r"\b(is|are|was|paid|cost|equals|proved)\b", result, re.I))
#     sources = bool(re.search(r"\b(source|cite|id:|http://|https://)\b", result, re.I))
#     hedges = bool(re.search(r"\b(might|may|could|likely|probably|appear)\b", result, re.I))
#     score = 1.0
#     reason_parts = []
#     if definitive and not sources and not hedges:
#         score -= 0.5
#         reason_parts.append("assertive claim without cited sources")
#     if hedges:
#         score -= 0.2
#         reason_parts.append("contains hedging")
#     passed = score > 0.5
#     action = "Request citations or provenance" if not passed else "OK"
#     return _hr("overconfidence_in_result", passed, score, "; ".join(reason_parts) or "confidence check OK", action)


# # ---------------------------
# # QUERY + RESULT HEURISTICS
# # ---------------------------

# def heuristic_cyclic_behavior_detection(query: str, result: Any, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Detect repetitive tool usage in session traces. Expects context to optionally contain 'tool_calls' (list of dicts with 'tool' names).
#     Flags if the same tool invoked > 3 times recently.
#     """
#     tool_calls = []
#     if context and isinstance(context, dict):
#         tool_calls = context.get("tool_calls") or context.get("task_progress") or []
#     names = [t.get("tool") if isinstance(t, dict) else getattr(t, "tool_name", None) for t in tool_calls]
#     # count last 6 entries
#     recent = names[-6:]
#     frequency = {}
#     for n in recent:
#         if not n:
#             continue
#         frequency[n] = frequency.get(n, 0) + 1
#     high = [k for k, v in frequency.items() if v >= 3]
#     if high:
#         return _hr("cyclic_behavior", False, 0.15, f"Repeated tool calls for {high}", "Limit retries; change tool selection or abort")
#     return _hr("cyclic_behavior", True, 1.0, "no cyclic pattern detected", "OK")


# def heuristic_premature_abandonment(query: str, result: Any, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Detect cases where the agent returned a max-steps or failure token instead of an answer.
#     Looks for phrases like 'Max steps reached', 'No answer', or empty final answers.
#     """
#     if isinstance(result, str):
#         if "max steps reached" in result.lower() or "no answer" in result.lower() or result.strip() == "":
#             return _hr("premature_abandonment", False, 0.0, "agent returned fallback/no answer", "Consider retrying with different tools or increasing max_steps")
#     return _hr("premature_abandonment", True, 1.0, "answer provided", "OK")


# def heuristic_edge_case_detector(query: str, result: Any, context: Optional[Dict] = None) -> Dict[str, Any]:
#     """
#     Try to detect if query concerns a potentially rare or critical edge case.
#     Simple heuristics:
#      - Query contains words like 'edge case', 'rare', 'critical', 'audit', 'legal', 'financial'
#      - Result contains numeric values or transactions (financial data) without provenance
#     """
#     edge_keywords = bool(re.search(r"\b(edge case|rare|critical|audit|legal|financial|transaction|paid|amount|invoice)\b", query + " " + (str(result) if result else ""), re.I))
#     if not edge_keywords:
#         return _hr("edge_case_detector", True, 1.0, "no edge-case keywords detected", "OK")
#     # if both query and result have numeric money-like tokens but no sources, warn
#     money_in_result = bool(re.search(r"\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b", str(result)))  # simple money-ish detection
#     source_present = bool(re.search(r"\b(source|id:|cite|http://|https://)\b", str(result), re.I))
#     score = 1.0
#     reason = "edge keywords detected"
#     if money_in_result and not source_present:
#         score -= 0.6
#         reason += "; numeric/financial result without provenance"
#     passed = score > 0.5
#     action = "Require provenance or do not auto-accept" if not passed else "OK"
#     return _hr("edge_case_detector", passed, score, reason, action)


# # ---------------------------
# # Helper runners
# # ---------------------------

# PRE_QUERY_HEURISTICS = [
#     heuristic_ambiguity_detection,
#     heuristic_sensitive_info_in_query,
#     heuristic_tool_selection_hint,
# ]

# POST_RESULT_HEURISTICS = [
#     heuristic_malformed_tool_output,
#     heuristic_relevance_score,
#     heuristic_overconfidence_in_result,
#     heuristic_cyclic_behavior_detection,
#     heuristic_premature_abandonment,
#     heuristic_edge_case_detector,
# ]


# def run_pre_query_checks(query: str, context: Optional[Dict] = None, available_tools: Optional[List[str]] = None) -> List[Dict[str, Any]]:
#     """
#     Run heuristics that should execute before the agent builds context.
#     Returns list of heuristic results.
#     """
#     results = []
#     for h in PRE_QUERY_HEURISTICS:
#         if h is heuristic_tool_selection_hint:
#             results.append(h(query, context, available_tools))
#         else:
#             results.append(h(query, context))
#     return results


# def run_post_result_checks(query: str, result: Any, context: Optional[Dict] = None) -> List[Dict[str, Any]]:
#     """
#     Run heuristics that should execute after agent has a result.
#     """
#     results = []
#     for h in POST_RESULT_HEURISTICS:
#         # the cyclic_detector and others expect both query and result and context
#         results.append(h(query, result, context))
#     return results


# # ---------------------------
# # Simple usage example (comment)
# # ---------------------------
# # from modules.heuristics import run_pre_query_checks, run_post_result_checks
# # pre = run_pre_query_checks("How much Anmol singh paid for his DLF apartment via Capbridge?", available_tools=["websearch","documents"])
# # # If pre contains a failing heuristic with actionable != "OK", you might prompt the user for clarification
# # # Then run agent and get `result`
# # post = run_post_result_checks(query, result, {"tool_calls": [{"tool":"search_stored_documents"}, ...]})
# # for r in post: print(r)



# heuristics.py  (modify/append to your existing file)
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


