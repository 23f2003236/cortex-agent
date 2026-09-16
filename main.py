import ast
import asyncio
import base64
import contextvars
import hashlib
import hmac
import ipaddress
import json
import math
import operator
import os
import re
import secrets
import socket
import threading
import time
import urllib.error
import urllib.request
from urllib.parse import urlparse
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

import database

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", override=True)

# ContextVar registries for securely propagating user ID and state across worker threads
_current_user_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("_current_user_id_ctx", default=None)
_current_harvested_plots_ctx: contextvars.ContextVar[list] = contextvars.ContextVar("_current_harvested_plots_ctx", default=[])

# Per-user streaming concurrency semaphore (max 2 active streams per user)
_user_stream_semaphore: dict[str, int] = {}
_stream_lock = threading.Lock()
MAX_CONCURRENT_STREAMS_PER_USER = 2

def acquire_user_stream(user_id: str) -> bool:
    with _stream_lock:
        active = _user_stream_semaphore.get(user_id, 0)
        if active >= MAX_CONCURRENT_STREAMS_PER_USER:
            return False
        _user_stream_semaphore[user_id] = active + 1
        return True

def release_user_stream(user_id: str):
    with _stream_lock:
        active = _user_stream_semaphore.get(user_id, 0)
        if active <= 1:
            _user_stream_semaphore.pop(user_id, None)
        else:
            _user_stream_semaphore[user_id] = active - 1

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "nvidia/nemotron-3-super-120b-a12b").strip()
NVIDIA_BASE_URL = os.getenv(
    "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
).strip()
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "32768"))
DEFAULT_INSECURE_SECRET = "cortex-agent-secure-token-secret-2026"
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

if not SECRET_KEY or SECRET_KEY == DEFAULT_INSECURE_SECRET:
    # Auto-generate a high-entropy 64-character secret and persist to .env
    generated_secret = secrets.token_hex(32)
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            env_content = env_path.read_text(encoding="utf-8")
            if "SECRET_KEY=" in env_content:
                env_content = re.sub(r"SECRET_KEY=.*", f"SECRET_KEY={generated_secret}", env_content)
            else:
                env_content = env_content.rstrip() + f"\n\n# Auto-generated cryptographic session secret\nSECRET_KEY={generated_secret}\n"
            env_path.write_text(env_content, encoding="utf-8")
        except Exception:
            pass
    SECRET_KEY = generated_secret
    os.environ["SECRET_KEY"] = generated_secret

SYSTEM_PROMPT = os.getenv(
    "SYSTEM_PROMPT",
    "You are Cortex, an advanced autonomous AI agent paired with real-time tools.\n\n"
    "1. REAL-TIME TOOLS & DISCIPLINE:\n"
    "- Available tools: calculator (arithmetic & scientific math: sqrt, sin, log, pi, e), web_search, fetch_webpage (up to 9k chars), wikipedia_lookup (en/hi), weather_lookup, current_datetime, remember (persistent cross-session memory).\n"
    "- Call tools when fresh facts, live data, prices, or precise calculations are needed. For general reasoning or trivial facts, reason directly.\n"
    "- PERSISTENT USER MEMORY: When the user shares personal details, preferences, tech stacks, constraints, or explicitly asks you to remember something (e.g. 'remember that...', 'yaad rakhna...'), invoke the 'remember' tool to store this fact across sessions. Note: The 'remember' tool is strictly WRITE-ONLY for saving new information. All previously saved memories are already provided in your system prompt under [STORED USER MEMORIES & PAST CONTEXT]. Never attempt to call 'remember' to read, search, or query memories; read the injected list directly. If the user asks what you remember or about their project/preferences and nothing is listed under stored memories, answer directly in natural Markdown that no details have been saved yet and invite them to share.\n"
    "- CODE INTELLIGENCE & ACCURACY: When asked to write code, algorithms, scripts, or data science pipelines (Python, JavaScript, SQL, HTML, etc.), write clean, production-grade, self-contained, and bug-free code inside standard markdown code fences. Provide clear explanations and steps so the user can easily run or integrate it into their environment.\n"
    "- NO RAW TOOL OUTPUT: Never emit raw JSON tool calls (e.g. {'tool': ...}), raw XML tool tags (<tool_call>, <function=...>), or pseudo-commands in your text response to the user. Always write clean, user-facing Markdown.\n"
    "- INLINE CITATIONS: When using web_search or wikipedia_lookup, cite your sources inline using markdown numbered reference links like [1](url), [2](url) or [Source](url) at the end of relevant factual claims so the user can easily trace and verify information.\n"
    "- Once tool research is obtained, synthesize immediately into a thorough, dense, and complete answer. Never output raw tool call tags (<tool_call>) or naked URLs alone.\n\n"
    "2. CONTEXTUAL & INTENT INTELLIGENCE:\n"
    "- Intelligently interpret ambiguous or phonetic phrasing in context (e.g. 'carrier' in jobs/AI context -> career/professions; 'algos' -> algorithms; 'models' -> AI models; 'EMI' in physics -> electromagnetic induction).\n"
    "- When asked about comparative trends, technologies, or careers, provide comprehensive, authoritative analysis with quantitative breakdowns, percentages, and actionable takeaways.\n\n"
    "3. ARCHITECTURE, CHARTS & CODE ACCURACY POLICY:\n"
    "- DIAGRAMS: NEVER draw wide, raw ASCII box-and-whisker or pipe trees (| BROWSER PROCESS |) in plain text; they wrap awkwardly and break on responsive screens. For architecture, component hierarchies, and workflows, use clean structured bullet trees with arrows (e.g. Browser UI ➔ IPC ➔ Renderer Process), structured Markdown comparison tables, or compact code blocks.\n"
    "- STRICT CHART POLICY (CRITICAL): NEVER generate an interactive chart (```chart) or visual widget UNLESS the user EXPLICITLY requests one in their prompt (e.g. 'chart banao', 'plot chart', 'create a bar chart', 'visualize in graph', 'generate chart'). For general questions, explanations, comparisons, roadmaps, or tutorials, DO NOT generate any unsolicited charts or visual widgets. Use clean markdown tables, bullet points, or code blocks instead.\n"
    "- ACCURATE CHARTS WHEN REQUESTED: When the user EXPLICITLY asks for a chart, the chart must be strictly accurate, quantitatively factual, and professionally labeled. Never output fake, random, or low-effort placeholder data. Format as ```chart with strictly valid JSON (balanced brackets, double quotes, no trailing commas) matching the Chart.js config structure (type, data: { labels: [...], datasets: [{ label: '...', data: [...] }] }, options).\n"
    "- CODE BLOCKS & ARTIFACTS: Programming code examples (HTML, CSS, JS, Python, SQL) MUST use standard markdown code blocks (e.g. ```html, ```css, ```python). Only format code as a dedicated downloadable artifact (e.g. ```html:app or ```python:filename=script.py) when the user explicitly requests to build an interactive web app or generate a standalone file. For standard code explanations, use regular code fences.\n"
    "- COMPLETENESS & PACING: Budget your explanations to deliver comprehensive conceptual depth, clean architecture breakdowns, and focused code snippets that reach a definitive conclusion. NEVER dump endless multi-thousand-line source code files that cause responses to hit token limits or cut off mid-sentence.\n"
    "- MATHEMATICS & FORMULAS: Format display equations on their own lines using $$...$$ (outside blockquotes, never prefix with >) and inline math with $...$ (never \\( or \\[).\n\n"
    "4. ATTACHED DOCUMENTS & SCANNED PDF POLICY:\n"
    "- When the user attaches a document or PDF where the extractable text is minimal, corrupted, or scanned (e.g. mostly repeated watermarks, photocopy images, or fragmentary lines), politely explain that the uploaded PDF contains scanned page images with limited selectable digital text.\n"
    "- NEVER STOP THERE OR LEAVE THE USER EMPTY-HANDED! If the user's prompt or filename indicates a recognizable topic, subject, textbook chapter, or concept (e.g., 'Selina Class 9 Physics Chapter 3 Laws of Motion', NCERT, standard algorithms, legal/business topics), PROACTIVELY DELIVER the complete, thorough, chapter-wise summary or answer using your deep domain knowledge (and DuckDuckGo web search if specific questions or exercises need lookup). Always ensure the user receives immediate, high-value assistance.\n\n"
    "5. TONE & STRUCTURE:\n"
    "- You have a vibrant, highly intelligent, and engaging persona like Claude and ChatGPT. Use clear markdown headers, comparison tables, bullet points, and tasteful emojis (🚀, 💡, ⚡, 📊, 🎯, 🧠, 🛠️, ✨) to make explanations modern, authoritative, and delightful to read.",
)

app = FastAPI(title="Cortex Agent", version="3.1.0")

CORS_ORIGINS_RAW = os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000")
ALLOWED_ORIGINS = [orig.strip() for orig in CORS_ORIGINS_RAW.split(",") if orig.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["http://localhost:8000", "http://127.0.0.1:8000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


# ---------------------------------------------------------------------------
# Auth Token Security & Dependency
# ---------------------------------------------------------------------------

def generate_token(user_id: str, username: str, expires_in_seconds: int = 60 * 60 * 24 * 30) -> str:
    """Generate a tamper-proof HMAC-SHA256 signed token."""
    payload = {
        "uid": user_id,
        "usr": username,
        "exp": int(time.time()) + expires_in_seconds,
    }
    payload_json = json.dumps(payload, separators=(",", ":"))
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{sig}"


def verify_token(token: str) -> Optional[dict[str, Any]]:
    """Verify the signature and expiry of a token."""
    try:
        parts = token.split(".")
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        expected_sig = hmac.new(SECRET_KEY.encode("utf-8"), payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None

        # Check if this token signature has been revoked on logout
        if database.is_token_revoked(sig):
            return None

        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload_json = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8")
        data = json.loads(payload_json)
        if data.get("exp", 0) < time.time():
            return None  # Token expired
        data["sig"] = sig
        return data
    except Exception:
        return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> dict[str, Any]:
    raw_token = None
    if authorization:
        if authorization.startswith("Bearer "):
            raw_token = authorization[7:].strip()
        else:
            raw_token = authorization.strip()

    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(raw_token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = database.get_user_by_id(token_data["uid"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


class RegisterPayload(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    email: Optional[str] = None


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=128)


@app.post("/api/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterPayload):
    clean_user = payload.username.strip().lower()
    if len(clean_user) < 3:
        raise HTTPException(status_code=400, detail="Username must be at least 3 characters.")
    if len(payload.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long.")

    try:
        user = database.create_user(clean_user, payload.password, payload.email)
    except ValueError as exc:
        err_str = str(exc)
        if "already registered" in err_str.lower() or "already taken" in err_str.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Username '{clean_user}' is already taken.")
        raise HTTPException(status_code=400, detail=err_str)

    token = generate_token(user["id"], user["username"])
    return {
        "ok": True,
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "is_guest": False,
        },
    }


@app.post("/api/auth/login")
def login(payload: LoginPayload):
    user = database.authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    token = generate_token(user["id"], user["username"])
    return {
        "ok": True,
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
        },
    }


@app.post("/api/auth/guest")
def guest_auth():
    """Create an anonymous ephemeral guest session with isolated data and quota."""
    user = database.create_guest_user()
    token = generate_token(user["id"], user["username"], expires_in_seconds=60 * 60 * 24)
    return {
        "ok": True,
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": "",
            "is_guest": True,
        },
    }


@app.get("/api/auth/me")
def auth_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "username": current_user["username"],
        "email": current_user.get("email", ""),
        "is_guest": bool(current_user.get("is_guest", False)),
        "created_at": current_user.get("created_at", ""),
    }


@app.post("/api/auth/logout")
def logout(authorization: Optional[str] = Header(None), current_user: dict = Depends(get_current_user)):
    """Revoke the current session token."""
    raw_token = ""
    if authorization:
        raw_token = authorization[7:].strip() if authorization.startswith("Bearer ") else authorization.strip()
    if raw_token and "." in raw_token:
        parts = raw_token.split(".")
        if len(parts) == 2:
            token_data = verify_token(raw_token)
            exp = token_data.get("exp", int(time.time()) + 3600) if token_data else int(time.time()) + 3600
            database.revoke_token(parts[1], current_user["id"], exp)
    return {"ok": True, "message": "Successfully logged out."}


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS = {
    "sqrt": math.sqrt,
    "cbrt": math.cbrt if hasattr(math, "cbrt") else lambda x: x ** (1 / 3),
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "floor": math.floor,
    "ceil": math.ceil,
    "degrees": math.degrees,
    "radians": math.radians,
}

_SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed.")
    if isinstance(node, ast.Name):
        name_lower = node.id.lower()
        if name_lower in _SAFE_CONSTANTS:
            return _SAFE_CONSTANTS[name_lower]
        raise ValueError(f"Unknown variable or constant '{node.id}'. Supported: {', '.join(_SAFE_CONSTANTS.keys())}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed.")
        return _ALLOWED_OPERATORS[op_type](
            _safe_eval(node.left), _safe_eval(node.right)
        )
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_OPERATORS:
            raise ValueError(f"Operator {op_type.__name__} is not allowed.")
        return _ALLOWED_OPERATORS[op_type](_safe_eval(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct mathematical function calls are supported.")
        fn_name = node.func.id.lower()
        if fn_name not in _SAFE_FUNCTIONS:
            raise ValueError(
                f"Function '{node.func.id}' is not supported. Allowed: {', '.join(sorted(_SAFE_FUNCTIONS.keys()))}"
            )
        fn = _SAFE_FUNCTIONS[fn_name]
        args = [_safe_eval(arg) for arg in node.args]
        return fn(*args)
    raise ValueError(f"Unsupported syntax: {type(node).__name__}")


@tool
def calculator(expression: str) -> str:
    """Evaluate an arithmetic or scientific math expression safely, e.g. '23 * (14 + 2) / 7',
    'sqrt(144) + sin(pi/2)', or 'log10(1000) * 5'.
    Supports +, -, *, /, //, %, **, parentheses, functions (sqrt, sin, cos, tan, log, log10, exp, abs, floor, ceil),
    and constants (pi, e)."""
    try:
        parsed = ast.parse(expression.strip(), mode="eval").body
        result = _safe_eval(parsed)
        return str(result)
    except Exception as exc:
        return f"Error evaluating expression: {exc}"


@tool
def current_datetime(timezone: str = "Asia/Kolkata") -> str:
    """Get the current date and time. Optionally pass an IANA timezone name
    like 'Asia/Kolkata', 'UTC', or 'America/New_York'. Defaults to Asia/Kolkata."""
    try:
        tz = ZoneInfo(timezone)
    except Exception:
        tz = ZoneInfo("UTC")
    now = datetime.now(tz)
    return now.strftime("%A, %d %B %Y, %I:%M %p %Z")


@tool
def web_search(query: str) -> str:
    """Search the web for current information, news, facts, or anything that
    might have changed recently or that you're unsure about. Returns a focused,
    deduplicated list of relevant results with titles, snippets, and links."""
    clean_query = query.strip().strip("\"'")
    if not clean_query:
        return "Please provide a non-empty search query."

    from duckduckgo_search import DDGS
    import time
    from urllib.parse import urlparse

    for attempt in range(3):
        try:
            results = []
            seen_domains = {}
            with DDGS(timeout=10) as ddgs:
                for r in ddgs.text(clean_query, max_results=14, backend="auto"):
                    title = r.get("title", "").strip()
                    body = r.get("body", "").strip()
                    href = r.get("href", "").strip()
                    if title and body and href:
                        try:
                            domain = urlparse(href).netloc.lower()
                        except Exception:
                            domain = href
                        if seen_domains.get(domain, 0) >= 2:
                            continue
                        seen_domains[domain] = seen_domains.get(domain, 0) + 1
                        results.append(f"- {title}: {body} (Source: {href})")
                        if len(results) >= 10:
                            break

            if results:
                return "\n".join(results)
            if attempt == 2:
                return f"No search results found for '{query}'."
        except Exception as exc:
            err_msg = str(exc)
            if ("ratelimit" in err_msg.lower() or "202" in err_msg) and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            if attempt < 2:
                time.sleep(1.0)
                continue
            # If rate limited on all attempts, provide helpful notice rather than failing outright
            return f"Note: Real-time search rate limit encountered for '{clean_query}'. Synthesize answer using knowledge base."

    return f"No search results found for '{query}'."


def is_safe_url(url: str) -> tuple[bool, str]:
    """Validate that a URL is safe to fetch and does not target internal / loopback / private IP addresses (SSRF protection)."""
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Malformed URL: {e}"

    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False, f"Disallowed scheme '{scheme}'. Only HTTP and HTTPS are permitted."

    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname in URL."

    hostname_lower = hostname.lower().strip(".")

    # Block localhost and local names directly
    if hostname_lower in ("localhost", "127.0.0.1", "::1") or hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        return False, f"Access to local or internal domain '{hostname}' is forbidden."

    # Validate port if specified
    port = parsed.port
    if port is not None and port not in (80, 443, 8080, 8443):
        return False, f"Access to port {port} is not permitted. Only standard web ports (80, 443) are allowed."

    # Resolve domain to IP addresses and verify none are private/loopback/link-local/reserved
    try:
        addr_info = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
    except socket.gaierror:
        return False, f"Could not resolve hostname '{hostname}'."
    except Exception as e:
        return False, f"DNS resolution failed: {e}"

    if not addr_info:
        return False, f"Could not resolve hostname '{hostname}' to any IP."

    for item in addr_info:
        sockaddr = item[4]
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
            if (
                ip.is_loopback
                or ip.is_private
                or ip.is_link_local
                or ip.is_multicast
                or ip.is_reserved
                or ip.is_unspecified
                or (hasattr(ip, "is_carrier_grade_nat") and ip.is_carrier_grade_nat)
            ):
                return False, f"Access to private/loopback IP {ip_str} is strictly forbidden."

            # Check IPv4 mapped in IPv6
            if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
                mapped_v4 = ip.ipv4_mapped
                if mapped_v4.is_loopback or mapped_v4.is_private or mapped_v4.is_link_local:
                    return False, f"Access to mapped private IPv4 {mapped_v4} is strictly forbidden."

            if ip_str.startswith("169.254."):
                return False, f"Access to link-local metadata IP {ip_str} is strictly forbidden."

        except ValueError:
            return False, f"Invalid resolved IP '{ip_str}'."

    return True, ""


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        is_safe, err = is_safe_url(newurl)
        if not is_safe:
            raise urllib.error.HTTPError(
                newurl, 403, f"SSRF Block: Redirect target is not safe: {err}", headers, fp
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@tool
def fetch_webpage(url: str) -> str:
    """Fetch and read the readable text content of a specific web URL (up to 9,000 characters).
    Preserves headings, tables, and lists. Use this to deep-dive into a specific link found in search results.
    Provide a full URL starting with http:// or https://."""
    try:
        import html
        import re
        import urllib.request

        clean_url = url.strip().strip("<>\"'")
        if not clean_url.startswith(("http://", "https://")):
            clean_url = "https://" + clean_url

        is_safe, sec_err = is_safe_url(clean_url)
        if not is_safe:
            return f"Security Error (SSRF Guard): Access to '{clean_url}' is blocked: {sec_err}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        req = urllib.request.Request(clean_url, headers=headers)
        opener = urllib.request.build_opener(SafeRedirectHandler())
        with opener.open(req, timeout=6) as response:
            content_type = response.headers.get_content_type()
            if "text" not in content_type and "html" not in content_type and "json" not in content_type:
                return f"Cannot read URL: unsupported content-type '{content_type}'."

            raw_bytes = response.read(600000)
            encoding = response.headers.get_content_charset() or "utf-8"
            try:
                raw_html = raw_bytes.decode(encoding, errors="replace")
            except Exception:
                raw_html = raw_bytes.decode("utf-8", errors="replace")

        # Strip unneeded structural and script tags
        cleaned = re.sub(
            r"<(script|style|nav|header|footer|svg|noscript|aside|form)[^>]*>.*?</\1>",
            " ",
            raw_html,
            flags=re.DOTALL | re.IGNORECASE,
        )
        # Convert structural tags to readable markdown formatting
        cleaned = re.sub(r"<h[1-3][^>]*>(.*?)</h[1-3]>", r"\n### \1\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<h[4-6][^>]*>(.*?)</h[4-6]>", r"\n#### \1\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<p[^>]*>", "\n\n", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"<br\s*/?>", "\n", cleaned, flags=re.IGNORECASE)

        # Strip remaining HTML tags
        cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        # Decode HTML entities
        cleaned = html.unescape(cleaned)
        # Normalize excessive whitespace but preserve linebreaks
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()

        if len(cleaned) < 120:
            return f"Note: Webpage at {clean_url} returned minimal text or requires JavaScript rendering. Please synthesize from the search results snippet."

        max_chars = 9000
        if len(cleaned) > max_chars:
            return f"Content of {clean_url} (first {max_chars} chars):\n{cleaned[:max_chars]}...\n[Truncated to {max_chars} characters]"
        return f"Content of {clean_url}:\n{cleaned}"
    except Exception as exc:
        return f"Failed to fetch webpage '{url}': {exc}"


@tool
def wikipedia_lookup(topic: str) -> str:
    """Look up a concise encyclopedic summary of a person, place, organization,
    or topic from Wikipedia. Supports English and Hindi queries."""
    try:
        import urllib.parse
        import urllib.request

        has_devanagari = any("\u0900" <= ch <= "\u097F" for ch in topic)
        lang_endpoints = ["hi", "en"] if has_devanagari else ["en", "hi"]

        for lang in lang_endpoints:
            title = urllib.parse.quote(topic.strip().replace(" ", "_"))
            url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}"
            req = urllib.request.Request(url, headers={"User-Agent": "CortexAgent/2.0"})
            try:
                with urllib.request.urlopen(req, timeout=8) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if "extract" in data and data["extract"].strip():
                    extract = data["extract"]
                    page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    return f"{extract}\n(Source: {page_url})" if page_url else extract
            except Exception:
                continue

        return f"No Wikipedia summary found for '{topic}'."
    except Exception as exc:
        return f"Wikipedia lookup failed: {exc}"


@tool
def weather_lookup(location: str) -> str:
    """Get the current weather and short forecast for a city or place name.
    Uses free Open-Meteo geocoding + weather APIs, no API key required."""
    try:
        import urllib.parse
        import urllib.request

        geo_url = (
            "https://geocoding-api.open-meteo.com/v1/search?"
            f"name={urllib.parse.quote(location)}&count=1"
        )
        with urllib.request.urlopen(geo_url, timeout=10) as resp:
            geo = json.loads(resp.read().decode("utf-8"))

        results = geo.get("results") or []
        if not results:
            return f"Could not find a location matching '{location}'."

        place = results[0]
        lat, lon = place["latitude"], place["longitude"]
        place_name = place.get("name", location)
        country = place.get("country", "")

        weather_url = (
            "https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code"
            "&daily=temperature_2m_max,temperature_2m_min,weather_code"
            "&timezone=auto&forecast_days=2"
        )
        with urllib.request.urlopen(weather_url, timeout=10) as resp:
            wx = json.loads(resp.read().decode("utf-8"))

        current = wx.get("current", {})
        daily = wx.get("daily", {})

        temp = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind = current.get("wind_speed_10m")

        today_max = daily.get("temperature_2m_max", [None])[0]
        today_min = daily.get("temperature_2m_min", [None])[0]

        return (
            f"Weather in {place_name}, {country}: currently {temp}°C, "
            f"humidity {humidity}%, wind {wind} km/h. "
            f"Today's range: {today_min}°C to {today_max}°C."
        )
    except Exception as exc:
        return f"Weather lookup failed: {exc}"


@tool
def remember(fact: str, category: str = "preference") -> str:
    """Remember a persistent fact, preference, technical stack, or directive about the user across future sessions.
    Use this when the user asks you to remember something (e.g. 'remember that I prefer Python', 'remember my name is Alex'),
    or when they state lasting preferences, project context, or workflow rules.
    Arguments:
      fact: The information or preference to remember in a clear, concise sentence.
      category: One of 'preference', 'tech', 'personal', 'project', or 'rule'.
    """
    clean_fact = (fact or "").strip()
    if not clean_fact:
        return "Error: Memory fact cannot be empty."
    user_id = _current_user_id_ctx.get()
    if not user_id:
        return "Notice: Memory not saved because user context is not available."
    try:
        mem = database.add_memory(user_id=user_id, content=clean_fact, category=category)
        return f"Successfully saved to memory: \"{clean_fact}\" [Category: {mem['category']}]."
    except Exception as exc:
        return f"Failed to save memory: {exc}"


TOOLS = [calculator, web_search, fetch_webpage, wikipedia_lookup, weather_lookup, current_datetime, remember]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}

MAX_TOOL_ROUNDS = 5

AVAILABLE_MODELS = [
    {"id": "nvidia/nemotron-3-super-120b-a12b", "name": "Cortex 5 (Super Agent)"},
    {"id": "nvidia/nemotron-3-ultra-550b-a55b", "name": "Cortex 5 Ultra (Master Agent)"},
    {"id": "openai/gpt-oss-20b", "name": "Cortex 4 (Deep Reasoning)"},
    {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "name": "Cortex 4 Omni (Vision & Reasoning)"},
    {"id": "nvidia/nemotron-3.5-lightning-30b-a3b", "name": "Cortex 3.5 Lightning (Ultra-Fast)"},
    {"id": "nvidia/nemotron-3.5-content-safety", "name": "Cortex Guard (Safety & Policy)"},
    {"id": "nvidia/nemotron-3-embed-1b", "name": "Cortex Embed (Vector & RAG)"},
]

MODEL_TOKEN_LIMITS = {
    "nvidia/nemotron-3-super-120b-a12b": 32768,            # Cortex 5 (Super Agent)
    "nvidia/nemotron-3-ultra-550b-a55b": 32768,            # Cortex 5 Ultra (Master Agent)
    "openai/gpt-oss-20b": 16384,                            # Cortex 4 (Deep Reasoning)
    "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": 16384, # Cortex 4 Omni (Vision & Reasoning)
    "nvidia/nemotron-3.5-lightning-30b-a3b": 16384,         # Cortex 3.5 Lightning (Ultra-Fast)
    "nvidia/nemotron-3.5-content-safety": 4096,             # Cortex Guard (Safety & Policy)
    "nvidia/nemotron-3-embed-1b": 2048,                     # Cortex Embed (Vector & RAG)
}


def get_model_max_tokens(model_id: str) -> int:
    return MODEL_TOKEN_LIMITS.get((model_id or "").strip(), MAX_OUTPUT_TOKENS)


def estimate_response_tokens(model_id: str, prompt: str, mode: str = "auto") -> int:
    """Dynamically determine maximum token budget based on model limits, query intent, and mode."""
    model_max = get_model_max_tokens(model_id)

    if (mode or "").lower() == "fast":
        return min(model_max, 16384)

    lower = (prompt or "").lower().strip()

    # Exhaustive technical requests, masterclasses, code implementations, or deep architecture:
    exhaustive_keywords = [
        "masterclass", "complete guide", "from scratch", "comprehensive",
        "in-depth", "deep dive", "step-by-step", "full implementation",
        "all chapters", "detailed breakdown", "entire architecture",
        "write complete", "detailed analysis", "complete roadmap"
    ]
    if any(k in lower for k in exhaustive_keywords) or len(lower) > 800:
        return model_max  # Up to 32,768 tokens!

    # Casual greetings or trivial queries:
    casual_keywords = [
        "hi", "hello", "hey", "who is", "what is", "kaisa hai", "kaise ho",
        "good morning", "good evening", "namaste"
    ]
    if len(lower.split()) <= 6 and any(k in lower for k in casual_keywords):
        return min(model_max, 1024)

    # Standard general-purpose response budget:
    return min(model_max, 16384)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

def make_llm(
    model_override: Optional[str] = None,
    streaming: bool = False,
    max_tokens: Optional[int] = None,
) -> ChatOpenAI:
    selected_model = (model_override or MODEL_NAME).strip()

    if not NVIDIA_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="NVIDIA_API_KEY is missing. Put your key in the .env file and restart the server.",
        )

    model_ceiling = get_model_max_tokens(selected_model)
    effective_max = min(max_tokens, model_ceiling) if max_tokens else model_ceiling

    return ChatOpenAI(
        model=selected_model,
        api_key=NVIDIA_API_KEY,
        base_url=NVIDIA_BASE_URL,
        temperature=0.2 if not streaming else 0.35,
        max_tokens=effective_max,
        timeout=120,
        max_retries=5,
        streaming=streaming,
    )


def _content_to_text(content) -> str:
    """Convert a full/final message's content into text. Strips leading and
    trailing whitespace — safe to use ONLY on a complete message, never on an
    individual streaming chunk (stripping a chunk can eat the exact space
    that separates it from the next chunk)."""
    return _chunk_to_text(content).strip()


def _chunk_to_text(content) -> str:
    """Convert a single streaming chunk's content into text WITHOUT
    stripping, so whitespace between chunks (spaces, newlines) is preserved
    exactly as the model produced it."""
    if isinstance(content, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        )
    if content is None:
        return ""
    return str(content)


TOOL_LABELS = {
    "calculator": "Calculator",
    "web_search": "Web search",
    "fetch_webpage": "Webpage reader",
    "wikipedia_lookup": "Wikipedia",
    "weather_lookup": "Weather",
    "current_datetime": "Date & time",
    "remember": "Memory Storage",
}


def run_tool_rounds(messages: list, model_override: Optional[str] = None) -> list[str]:
    """Run non-streaming tool-calling rounds until the model has no more tool
    calls to make. Mutates `messages` in place by appending AI/Tool messages.
    Returns the list of tool names that were used."""
    llm = make_llm(model_override=model_override, streaming=False, max_tokens=1024)
    llm_with_tools = llm.bind_tools(TOOLS)
    tools_used: list[str] = []

    for _ in range(MAX_TOOL_ROUNDS):
        ai_message = llm_with_tools.invoke(messages)
        tool_calls = getattr(ai_message, "tool_calls", None) or []

        if not tool_calls:
            return tools_used

        messages.append(ai_message)

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            tool_fn = TOOLS_BY_NAME.get(tool_name)

            if tool_fn is None:
                result_text = f"Error: unknown tool '{tool_name}'."
            else:
                try:
                    result_text = str(tool_fn.invoke(tool_args))
                except Exception as exc:
                    result_text = f"Error running tool '{tool_name}': {exc}"
                if tool_name not in tools_used:
                    tools_used.append(tool_name)

            messages.append(ToolMessage(content=result_text, tool_call_id=call["id"]))

    return tools_used


def run_tool_rounds_streaming(
    messages: list,
    model_override: Optional[str] = None,
    tools_subset: Optional[list] = None,
    max_rounds: Optional[int] = None,
):
    """Run tool-calling rounds and yield live progress events:
    - ("tool_start", {"name": tool_name, "label": label, "args": tool_args})
    - ("tool_end", {"name": tool_name, "label": label, "result": preview})
    - ("tools_used", tools_used)
    Mutates `messages` in place.
    """
    effective_tools = tools_subset if tools_subset is not None else TOOLS
    tools_by_name = {t.name: t for t in effective_tools}
    effective_rounds = max_rounds or MAX_TOOL_ROUNDS

    llm = make_llm(model_override=model_override, streaming=False, max_tokens=1024)
    llm_with_tools = llm.bind_tools(effective_tools)
    tools_used: list[str] = []

    for _ in range(effective_rounds):
        ai_message = None
        for attempt in range(3):
            try:
                ai_message = llm_with_tools.invoke(messages)
                break
            except Exception as e:
                err_str = str(e).lower()
                if ("overloaded" in err_str or "rate limit" in err_str or "503" in err_str) and attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                raise

        tool_calls = getattr(ai_message, "tool_calls", None) or []

        # Synthetic fallback: if the model formatted tool calls as raw JSON or pseudo-tags in text content
        if not tool_calls and ai_message and ai_message.content:
            text_content = _chunk_to_text(ai_message.content).strip()
            # 1. Check for JSON tool call
            if text_content.startswith("{") and ('"tool"' in text_content or '"name"' in text_content):
                try:
                    end_idx = text_content.rfind("}")
                    if end_idx != -1:
                        parsed = json.loads(text_content[:end_idx + 1])
                        t_name = parsed.get("tool") or parsed.get("name")
                        t_args = parsed.get("arguments") or parsed.get("args") or {}
                        if t_name in TOOLS_BY_NAME:
                            tool_calls = [{"name": t_name, "args": t_args, "id": f"call-syn-{int(time.time()*1000)}"}]
                except Exception:
                    pass

            # 2. Check for pseudo-tags e.g. <function=tool_name>... or =execute_pythoncode>
            if not tool_calls:
                fn_match = re.search(r"<\/?function=([a-zA-Z0-9_]+)>", text_content)
                if fn_match:
                    fn_name = fn_match.group(1)
                    payload = text_content[fn_match.end():].strip()
                    payload = re.sub(r"<\/(?:parameter|function|tool_call)>", "", payload).strip()
                    if fn_name in TOOLS_BY_NAME:
                        args = {}
                        if fn_name == "remember":
                            args = {"fact": payload}
                        else:
                            try:
                                args = json.loads(payload)
                            except Exception:
                                args = {"query": payload}
                        tool_calls = [{"name": fn_name, "args": args, "id": f"call-syn-{int(time.time()*1000)}"}]

        if not tool_calls:
            break

        messages.append(ai_message)

        for call in tool_calls:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            label = TOOL_LABELS.get(tool_name, tool_name)

            yield ("tool_start", {"name": tool_name, "label": label, "args": tool_args})

            tool_fn = TOOLS_BY_NAME.get(tool_name)
            if tool_fn is None:
                result_text = f"Error: unknown tool '{tool_name}'."
            else:
                try:
                    result_text = str(tool_fn.invoke(tool_args))
                except Exception as exc:
                    result_text = f"Error running tool '{tool_name}': {exc}"
                if tool_name not in tools_used:
                    tools_used.append(tool_name)

            preview = result_text[:400] + ("..." if len(result_text) > 400 else "")
            yield ("tool_end", {"name": tool_name, "label": label, "result": preview})
            messages.append(ToolMessage(content=result_text, tool_call_id=call["id"]))

    yield ("tools_used", tools_used)


def should_run_tools(raw_content: str, messages: list) -> bool:
    """Smart query classification for Auto Mode.
    Determines if tools (web_search, fetch_webpage, calculator, wikipedia, weather, datetime, remember)
    are genuinely required. For conceptual, coding, creative, architectural, or conversational
    queries, returns False so direct streaming begins in 1-5 seconds without delay."""
    if not raw_content:
        return False

    text = raw_content.strip()
    lower = text.lower()

    # 1. Direct Webpage Fetch: URLs present
    if re.search(r"https?://[^\s]+", text):
        return True

    # 2. Real-time Weather:
    if re.search(r"\b(weather|mausam|temperature in|forecast for|barish|raining in)\b", lower):
        return True

    # 3. Current Date & Time:
    if re.search(r"\b(current time|what time is it|what is today'?s date|current date|today'?s date|aaj ki date|aaj konsa din|aaj ka time|time in [a-z]+)\b", lower):
        return True

    # 4. Explicit Live Web Search & News:
    if re.search(r"\b(search (the )?web|search online|search for|google kar|latest news|today'?s news|breaking news|live score|stock price of|current price of|share price of|crypto price of|aaj ka bhav)\b", lower):
        return True

    # 5. Explicit Wikipedia / Entity Lookup:
    if re.search(r"\b(wikipedia of|wikipedia article on|who is currently|who is the current|recent updates on|what happened (in|at|yesterday)|kiske baare me)\b", lower):
        return True

    # 6. Specific Numeric / Scientific Calculation:
    if re.search(r"\b(calculate|sqrt\(|cbrt\(|sin\(|cos\(|tan\(|log10?\(|log2\()\b", lower):
        return True
    if re.search(r"\b\d+(\.\d+)?\s*[\+\-\*\/\^]\s*\d+(\.\d+)?\b", text):
        return True

    # 7. Explicit User Research / Fact-checking Instruction:
    if re.search(r"\b(browse the internet|research on web|verify sources|fact[- ]check)\b", lower):
        return True

    # 8. Memory & Preference Storing:
    if re.search(r"\b(remember that|remember this|yaad rakh|yaad rakhna|note down that|save to memory|store in memory|keep in mind that|remember my|mera naam|my name is)\b", lower):
        return True

    return False


def should_run_fast_tools(raw_content: str) -> bool:
    """Determine if Fast Mode should run local operational tools.
    Fast mode skips heavy multi-round web research, but executes fast local operations:
    - Persistent memory saving (remember)
    - Deterministic math expressions (calculator)
    """
    if not raw_content:
        return False
    lower = raw_content.lower().strip()
    # 1. Memory saving
    if re.search(r"\b(remember that|remember this|yaad rakh|yaad rakhna|note down that|save to memory|store in memory|keep in mind that)\b", lower):
        return True
    # 2. Exact calculations
    if re.search(r"\b(calculate|sqrt\(|cbrt\(|sin\(|cos\(|tan\(|log10?\(|log2\()\b", lower):
        return True
    if re.search(r"\b\d+(\.\d+)?\s*[\+\-\*\/\^]\s*\d+(\.\d+)?\b", raw_content):
        return True
    return False


VALID_MODEL_IDS = {m["id"] for m in AVAILABLE_MODELS}
ALLOWED_MODES = {"auto", "fast", "thinking"}


class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=500_000)
    tools_used: Optional[list[str]] = None


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None
    model: Optional[str] = None
    mode: Optional[str] = "auto"
    messages: list[ChatMessage] = Field(default_factory=list, min_length=1, max_length=100)


@app.get("/")
def home():
    return FileResponse(
        BASE_DIR / "static" / "index.html",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "provider": "NVIDIA",
        "model": MODEL_NAME,
        "api_key_configured": bool(NVIDIA_API_KEY),
        "tools": [t.name for t in TOOLS],
        "available_models": AVAILABLE_MODELS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "model_token_limits": MODEL_TOKEN_LIMITS,
    }


# ---------------------------------------------------------------------------
# File Upload Endpoint
# ---------------------------------------------------------------------------

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload a document/code file (.pdf, .csv, .txt, .md, .py, etc.) and extract text."""
    allowed, used, limit = database.check_daily_uploads(current_user["id"])
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Daily upload limit reached (10/10 files). You have uploaded the maximum allowed files and screenshots for today. Please continue chatting or clear attachments.",
        )

    filename = file.filename or "uploaded_file"
    ext = Path(filename).suffix.lower()

    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
    CHUNK_SIZE = 64 * 1024  # 64 KB

    chunks = []
    total_size = 0
    try:
        while True:
            chunk = await file.read(CHUNK_SIZE)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_UPLOAD_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="File too large. Maximum allowed size is 10 MB.",
                )
            chunks.append(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {exc}")

    raw_content = b"".join(chunks)

    # Validate file magic bytes for binary formats
    if not raw_content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty (0 bytes).")

    if ext == ".pdf":
        if not raw_content.startswith(b"%PDF-"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupt or invalid PDF: missing '%PDF-' header signature.")
    elif ext in (".docx", ".xlsx"):
        if not (raw_content.startswith(b"PK\x03\x04") or raw_content.startswith(b"PK\x05\x06") or raw_content.startswith(b"PK\x07\x08")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Corrupt or invalid {ext} file: missing valid OpenXML archive header.")
    elif ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"):
        if ext == ".png" and not raw_content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupt or invalid PNG file: missing PNG signature.")
        elif ext in (".jpg", ".jpeg") and not raw_content.startswith(b"\xff\xd8\xff"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupt or invalid JPEG file: missing JPEG signature.")
        elif ext == ".gif" and not (raw_content.startswith(b"GIF87a") or raw_content.startswith(b"GIF89a")):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupt or invalid GIF file: missing GIF signature.")
        elif ext == ".webp" and not (raw_content.startswith(b"RIFF") and len(raw_content) >= 12 and raw_content[8:12] == b"WEBP"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupt or invalid WEBP file: missing WEBP signature.")
        elif ext == ".bmp" and not raw_content.startswith(b"BM"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Corrupt or invalid BMP file: missing BMP signature.")

    database.increment_daily_uploads(current_user["id"], 1)

    extracted_text = ""

    if ext in (".xls", ".doc"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Legacy binary format '{ext}' is not supported for security and reliability reasons. Please convert to modern '{ext}x' or CSV before uploading.",
        )

    if ext == ".pdf":
        import io
        import pypdf

        try:
            reader = pypdf.PdfReader(io.BytesIO(raw_content))
            pages_text = []
            total_substantive_words = 0
            raw_page_count = len(reader.pages)
            pages_to_process = reader.pages[:50]  # Hard limit: maximum 50 pages

            total_extracted_chars = 0
            for i, page in enumerate(pages_to_process):
                page_content = page.extract_text() or ""
                clean_lines = []
                for line in page_content.splitlines():
                    trimmed = line.strip()
                    if not trimmed:
                        continue
                    # Ignore common website download watermarks that pollute scanned textbook PDFs
                    if re.search(r"downloaded\s+from\s+https?://", trimmed, re.IGNORECASE) or re.search(r"^\s*https?://www\.(studiestoday|learncbse|vedantu|byjus)\.com\s*$", trimmed, re.IGNORECASE):
                        continue
                    clean_lines.append(trimmed)

                clean_page = "\n".join(clean_lines).strip()
                if clean_page:
                    words = len(clean_page.split())
                    total_substantive_words += words
                    if total_extracted_chars + len(clean_page) > 500000:
                        remaining_budget = max(0, 500000 - total_extracted_chars)
                        pages_text.append(f"--- Page {i + 1} (Truncated) ---\n{clean_page[:remaining_budget]}")
                        pages_text.append("\n[Extraction reached maximum text limit of 500,000 characters]")
                        break
                    pages_text.append(f"--- Page {i + 1} ---\n{clean_page}")
                    total_extracted_chars += len(clean_page)

            if raw_page_count > 50:
                pages_text.append(f"\n[Note: Document has {raw_page_count} pages; processed first 50 pages]")

            is_scanned_or_low_text = (total_substantive_words < 60 and raw_page_count >= 2) or not pages_text

            if pages_text and not is_scanned_or_low_text:
                extracted_text = "\n\n".join(pages_text)
            elif pages_text and is_scanned_or_low_text:
                joined_frags = "\n\n".join(pages_text)
                extracted_text = (
                    f"[Document Notice: '{filename}' has {raw_page_count} pages, but appears to consist of SCANNED images/photocopies with only {total_substantive_words} words of extractable digital text.]\n\n"
                    f"{joined_frags}\n\n"
                    f"[Agent Instruction: The user uploaded a scanned PDF where pages are images with minimal selectable text. Politely clarify that the uploaded PDF consists of scanned page images, but DO NOT stop there. Actively provide the complete, authoritative, and comprehensive summary and concepts for the topic indicated by the filename/prompt ('{filename}') directly in clean, structured Markdown using your deep subject knowledge. DO NOT output any raw tool calls, function tags, or JSON.]"
                )
            else:
                extracted_text = (
                    f"[Document Notice: '{filename}' ({raw_page_count} pages) is a SCANNED image-only PDF with NO selectable text streams.]\n\n"
                    f"[Agent Instruction: Politely mention that the PDF is a scanned image document, but DO NOT refuse to answer. Provide the complete, detailed summary and solutions for the subject/topic indicated by the filename or prompt ('{filename}') directly from your deep knowledge base in clean, structured Markdown. DO NOT output any raw tool calls, function tags, or JSON.]"
                )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse PDF: {exc}")
    elif ext == ".xlsx":
        import io
        import openpyxl

        try:
            wb = openpyxl.load_workbook(io.BytesIO(raw_content), data_only=True, read_only=True)
            sheets_text = []
            for sheet_name in wb.sheetnames[:5]:  # limit to first 5 sheets
                sheet = wb[sheet_name]
                rows = []
                for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
                    if r_idx > 5000:
                        break
                    if r_idx > 60:
                        continue
                    row_vals = [str(cell if cell is not None else "") for cell in row]
                    if any(row_vals):
                        rows.append(row_vals)

                if rows:
                    header = rows[0]
                    col_count = len(header)
                    header_line = "| " + " | ".join(str(header[c] or f"Col{c+1}").replace("\n", " ") for c in range(col_count)) + " |"
                    sep_line = "| " + " | ".join(["---"] * col_count) + " |"
                    data_lines = []
                    for r in rows[1:35]:
                        data_row = [str(r[c] if c < len(r) else "").replace("\n", " ") for c in range(col_count)]
                        data_lines.append("| " + " | ".join(data_row) + " |")

                    sheet_summary = f"### Sheet: {sheet_name} ({len(rows)} rows, {col_count} columns)\n"
                    table_md = "\n".join([header_line, sep_line] + data_lines)
                    sheets_text.append(f"{sheet_summary}\n{table_md}")

            wb.close()
            extracted_text = (
                f"[Attached Spreadsheet: {filename}]\n\n" + "\n\n".join(sheets_text)
                if sheets_text
                else "(Spreadsheet appears to be empty or contains no data rows.)"
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse Excel spreadsheet: {exc}")
    elif ext == ".docx":
        import io
        import docx

        try:
            doc = docx.Document(io.BytesIO(raw_content))
            sections_text = []
            total_doc_chars = 0
            for p_idx, p in enumerate(doc.paragraphs):
                if p_idx > 2000 or total_doc_chars > 500000:
                    sections_text.append("\n[Document truncated to 500,000 characters / 2,000 paragraphs]")
                    break
                text_strip = p.text.strip()
                if not text_strip:
                    continue
                if p.style and p.style.name.startswith("Heading 1"):
                    formatted = f"\n# {text_strip}"
                elif p.style and p.style.name.startswith("Heading 2"):
                    formatted = f"\n## {text_strip}"
                elif p.style and p.style.name.startswith("Heading 3"):
                    formatted = f"\n### {text_strip}"
                else:
                    formatted = text_strip
                sections_text.append(formatted)
                total_doc_chars += len(formatted)

            for t_idx, table in enumerate(doc.tables[:5]):
                t_rows = []
                for row in table.rows[:30]:
                    t_rows.append([cell.text.strip().replace("\n", " ") for cell in row.cells])
                if t_rows:
                    col_count = len(t_rows[0])
                    header_line = "| " + " | ".join(t_rows[0]) + " |"
                    sep_line = "| " + " | ".join(["---"] * col_count) + " |"
                    data_lines = ["| " + " | ".join(r) + " |" for r in t_rows[1:]]
                    sections_text.append(f"\n[Document Table {t_idx + 1}]:\n" + "\n".join([header_line, sep_line] + data_lines))

            extracted_text = (
                f"[Attached Word Document: {filename}]\n\n" + "\n\n".join(sections_text)
                if sections_text
                else "(Document appears to be empty.)"
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Failed to parse Word document: {exc}")
    elif ext in [".csv", ".tsv"]:
        import csv
        import io

        try:
            raw_decoded = raw_content[:500000].decode("utf-8")
        except UnicodeDecodeError:
            raw_decoded = raw_content[:500000].decode("latin-1", errors="replace")

        delimiter = "\t" if ext == ".tsv" else ","
        try:
            reader = csv.reader(io.StringIO(raw_decoded), delimiter=delimiter)
            rows = []
            for r_idx, r in enumerate(reader):
                if r_idx > 5000:
                    break
                if r_idx > 60:
                    continue
                if any(c.strip() for c in r):
                    rows.append([c.strip() for c in r])

            if rows:
                header = rows[0]
                col_count = len(header)
                header_line = "| " + " | ".join(header) + " |"
                sep_line = "| " + " | ".join(["---"] * col_count) + " |"
                data_lines = []
                for r in rows[1:40]:
                    padded = [r[c] if c < len(r) else "" for c in range(col_count)]
                    data_lines.append("| " + " | ".join(padded) + " |")
                extracted_text = (
                    f"[Structured Tabular Data: {filename} ({len(rows)} rows, {col_count} columns)]\n\n"
                    + "\n".join([header_line, sep_line] + data_lines)
                )
            else:
                extracted_text = raw_decoded
        except Exception:
            extracted_text = raw_decoded
    elif ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp"]:
        import io
        from PIL import Image

        try:
            with Image.open(io.BytesIO(raw_content)) as img:
                width, height = img.size
                if width > 4096 or height > 4096:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Image dimensions {width}x{height} exceed maximum permitted size (4096 x 4096 px).",
                    )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid image file: {exc}")

        kb = max(1, len(raw_content) // 1024)
        mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else f"image/{ext.lstrip('.')}"
        b64_str = base64.b64encode(raw_content).decode("ascii")
        data_url = f"data:{mime};base64,{b64_str}"
        extracted_text = (
            f"[Attached Image: {filename} ({kb} KB, {width}x{height} px)]\n"
            f"(Visual Image Base64: {data_url})"
        )
    elif ext == ".svg":
        svg_text = raw_content[:100000].decode("utf-8", errors="replace")
        if re.search(r"<\s*script", svg_text, re.IGNORECASE):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="SVG file contains forbidden script elements.")
        kb = max(1, len(raw_content) // 1024)
        b64_str = base64.b64encode(raw_content).decode("ascii")
        data_url = f"data:image/svg+xml;base64,{b64_str}"
        extracted_text = (
            f"[Attached SVG Vector: {filename} ({kb} KB)]\n"
            f"(Visual Image Base64: {data_url})"
        )
    else:
        # Plain text, HTML, JSON, Markdown, Python, JS, etc.
        try:
            extracted_text = raw_content[:500000].decode("utf-8")
        except UnicodeDecodeError:
            extracted_text = raw_content[:500000].decode("latin-1", errors="replace")

    is_img = ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"]
    if is_img:
        preview_text = extracted_text
        is_truncated = False
    else:
        max_len = 14000
        is_truncated = len(extracted_text) > max_len
        if is_truncated:
            preview_text = (
                extracted_text[:max_len]
                + f"\n\n[Note: Document truncated to first {max_len} characters out of {len(extracted_text)}]"
            )
        else:
            preview_text = extracted_text

    return {
        "filename": filename,
        "size": len(raw_content),
        "text": preview_text,
        "char_count": len(extracted_text),
        "truncated": is_truncated,
        "is_image": is_img,
        "image_data_url": data_url if is_img else None,
    }


class UrlScrapePayload(BaseModel):
    url: str


@app.post("/api/scrape/url")
def scrape_url_endpoint(payload: UrlScrapePayload, current_user: dict = Depends(get_current_user)):
    """Fetch and scrape clean article/document text from a URL as a chat attachment."""
    url = payload.url.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    is_safe, sec_err = is_safe_url(url)
    if not is_safe:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"SSRF Security Violation: {sec_err}")

    content = fetch_webpage.func(url)
    if not content or content.startswith("Security Error (SSRF Guard):") or content.startswith("Cannot read URL:"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=content or "Failed to fetch webpage content.")

    max_len = 14000
    is_truncated = len(content) > max_len
    preview_text = (
        content[:max_len]
        + (f"\n\n[Note: Document truncated to first {max_len} characters out of {len(content)}]" if is_truncated else "")
    )

    return {
        "filename": url,
        "size": len(content.encode("utf-8")),
        "text": f"[Attached Webpage: {url}]\n\n{preview_text}",
        "char_count": len(content),
        "truncated": is_truncated,
        "is_image": False,
        "image_data_url": None,
    }


# ---------------------------------------------------------------------------
# Conversation REST endpoints (User Scoped)
# ---------------------------------------------------------------------------

@app.get("/api/conversations")
def list_conversations(
    project_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
):
    return database.get_conversations(user_id=current_user["id"], project_id=project_id)


class CreateConversationPayload(BaseModel):
    title: Optional[str] = "New Chat"
    project_id: Optional[str] = None


@app.post("/api/conversations")
def create_new_conversation(
    payload: Optional[CreateConversationPayload] = None,
    current_user: dict = Depends(get_current_user),
):
    title = payload.title if payload and payload.title else "New Chat"
    project_id = payload.project_id if payload else None
    if project_id:
        proj = database.get_project(project_id, user_id=current_user["id"])
        if not proj:
            raise HTTPException(status_code=404, detail="Project workspace not found or does not belong to your account.")
    return database.create_conversation(title=title, user_id=current_user["id"], project_id=project_id)


@app.get("/api/conversations/{conv_id}")
def get_conversation_history(conv_id: str, current_user: dict = Depends(get_current_user)):
    conv = database.get_conversation(conv_id, user_id=current_user["id"])
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = database.get_messages(conv_id)
    return {"conversation": conv, "messages": messages}


@app.delete("/api/conversations/{conv_id}")
def delete_conversation_session(conv_id: str, current_user: dict = Depends(get_current_user)):
    success = database.delete_conversation(conv_id, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


class UpdateTitleRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)


@app.patch("/api/conversations/{conv_id}")
def rename_conversation(
    conv_id: str,
    payload: UpdateTitleRequest,
    current_user: dict = Depends(get_current_user),
):
    success = database.update_conversation_title(conv_id, payload.title, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True, "title": payload.title}


class PinConversationPayload(BaseModel):
    is_pinned: Optional[bool] = None


@app.patch("/api/conversations/{conv_id}/pin")
def pin_conversation(
    conv_id: str,
    payload: Optional[PinConversationPayload] = None,
    current_user: dict = Depends(get_current_user),
):
    pinned_val = payload.is_pinned if payload else None
    result = database.toggle_pin_conversation(conv_id, is_pinned=pinned_val, user_id=current_user["id"])
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True, "is_pinned": result}


def _format_user_message(content: str) -> HumanMessage:
    """Parse user message content. If it contains a visual image base64 data URI,
    construct a multimodal LangChain HumanMessage with image_url content parts."""
    import re
    m = re.search(r"\(Visual Image Base64:\s*(data:image\/[^;]+;base64,[A-Za-z0-9+/=]+)\)", content)
    if m:
        data_url = m.group(1)
        clean_text = re.sub(r"\(Visual Image Base64:\s*data:image\/[^;]+;base64,[A-Za-z0-9+/=]+\)\n*", "", content).strip()
        return HumanMessage(
            content=[
                {"type": "text", "text": clean_text or "Please inspect and analyze this attached image."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]
        )
    return HumanMessage(content=content)


def _build_messages(request: ChatRequest, user_id: Optional[str] = None, conv_id: Optional[str] = None) -> tuple[list, ChatMessage]:
    """Build LangChain messages with smart sliding window context budgeting (max ~60,000 chars,
    last 30 turns) to preserve deep conversational memory, multimodal vision support,
    and persistent cross-session memories + custom personalization directives."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="Send at least one message.")

    *history, last = request.messages
    if last.role != "user":
        raise HTTPException(status_code=400, detail="The last message must be from the user.")

    # Smart sliding window: retain up to 30 historical messages and max 60,000 chars
    max_history_chars = 60000
    max_history_turns = 30

    trimmed_history = history[-max_history_turns:] if len(history) > max_history_turns else history

    included_history = []
    char_count = 0
    for msg in reversed(trimmed_history):
        # Calculate text length excluding massive base64 image data for budgeting
        raw_msg_content = msg.content or ""
        text_only_len = len(re.sub(r"\(Visual Image Base64:\s*data:image\/[^;]+;base64,[A-Za-z0-9+/=]+\)", "", raw_msg_content))
        if char_count + text_only_len > max_history_chars and included_history:
            break
        included_history.insert(0, msg)
        char_count += text_only_len

    messages = [SystemMessage(content=SYSTEM_PROMPT)]

    # Inject Persistent Memories and Custom Personalization Instructions
    if user_id:
        memory_blocks = []
        user_instructions = database.get_user_custom_instructions(user_id)
        if user_instructions and user_instructions.strip():
            memory_blocks.append(
                f"[USER CUSTOM INSTRUCTIONS & SYSTEM DIRECTIVES]\n{user_instructions.strip()}"
            )
        if conv_id:
            conv_instructions = database.get_conversation_custom_instructions(conv_id)
            if conv_instructions and conv_instructions.strip():
                memory_blocks.append(
                    f"[CONVERSATION DIRECTIVES]\n{conv_instructions.strip()}"
                )
            conv_meta = database.get_conversation(conv_id, user_id=user_id)
            if conv_meta and conv_meta.get("project_id"):
                proj = database.get_project(conv_meta["project_id"], user_id=user_id)
                if proj:
                    proj_parts = [f"[PROJECT WORKSPACE: {proj['name']}]"]
                    if proj.get("description"):
                        proj_parts.append(f"Description: {proj['description']}")
                    if proj.get("system_prompt"):
                        proj_parts.append(f"Project Directives & Guidelines:\n{proj['system_prompt'].strip()}")
                    memory_blocks.append("\n".join(proj_parts))
        memories = database.get_memories(user_id, limit=20)
        if memories:
            formatted_mems = "\n".join(
                f"- [{m.get('category', 'preference').upper()}] {m['content']}"
                for m in reversed(memories)
            )
            memory_blocks.append(
                f"[STORED USER MEMORIES & PAST CONTEXT]\n{formatted_mems}"
            )
        else:
            memory_blocks.append(
                "[STORED USER MEMORIES & PAST CONTEXT]\n"
                "No saved user memories found yet. If the user asks what you remember or asks about their project/preferences, "
                "answer politely that no details have been saved in memory yet and invite them to share. "
                "DO NOT attempt to call the 'remember' tool to query memories, and never emit raw JSON."
            )
        if memory_blocks:
            messages.append(SystemMessage(content="\n\n".join(memory_blocks)))

    if len(included_history) < len(history):
        omitted_count = len(history) - len(included_history)
        messages.append(
            SystemMessage(
                content=f"[Context Note: {omitted_count} earlier conversation messages omitted to preserve sharp reasoning context.]"
            )
        )

    for msg in included_history:
        if msg.role == "user":
            # For older turns in history, keep text summary but strip massive base64 payload to conserve context
            hist_clean = re.sub(
                r"\(Visual Image Base64:\s*data:image\/[^;]+;base64,[A-Za-z0-9+/=]+\)",
                "[Previous turn image attachment]",
                msg.content or "",
            )
            messages.append(HumanMessage(content=hist_clean))
        else:
            messages.append(AIMessage(content=msg.content))

    # Add the active user message (which preserves full visual image data URL for current reasoning!)
    messages.append(_format_user_message(last.content))
    return messages, last


def generate_smart_title(content: str) -> str:
    """Generate a concise, elegant, ChatGPT/Claude-style conversation title (2-5 words, Title Case)."""
    if not content or not content.strip():
        return "New Chat"

    import re
    text = content.strip()

    # 1. Document attachment detection
    doc_match = re.search(r"\[Attached Document:\s*([^\]]+)\]", text)
    if doc_match:
        doc_name = doc_match.group(1).strip()
        base_name = doc_name.rsplit(".", 1)[0]
        base_name = re.sub(r"[_\-]+", " ", base_name).strip()
        return base_name.title()

    # 2. URL / Wikipedia reader detection (before stripping underscores)
    wiki_match = re.search(r"wikipedia\.org\/wiki\/([^\s\/\?\#]+)", text, re.IGNORECASE)
    if wiki_match:
        wiki_topic = wiki_match.group(1).replace("_", " ").strip().title()
        return f"Wikipedia: {wiki_topic}"
    if re.search(r"https?:\/\/[^\s]+", text) and len(text.split()) <= 8:
        return "Webpage Summary"

    # Strip code blocks and markdown
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"\[Attached Document:[^\]]+\]", "", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[`#*_\~>]+", " ", text)
    text = " ".join(text.split())

    # Repeated char normalization (e.g. heelllllo -> hello, tuuu -> tu)
    norm_text = re.sub(r"(.)\1{2,}", r"\1\1", text.lower())

    # Detect casual greetings by collapsing repeated characters
    casual_words = {
        "hi", "hii", "hello", "helo", "hey", "heyy", "yo", "hola", "kaise", "kaisa", "hai", "ho", "tu", "tuu",
        "bro", "broo", "yr", "yrr", "yaar", "bhai", "sup", "how", "hows", "life", "namaste", "morning", "evening",
        "are", "you", "u", "doing", "good"
    }
    collapsed_tokens = [re.sub(r"(.)\1+", r"\1", w.strip(".,!?\"'")) for w in text.lower().split() if w.strip(".,!?\"'")]
    raw_tokens = [w.strip(".,!?\"'") for w in text.lower().split() if w.strip(".,!?\"'")]
    if (collapsed_tokens and all(w in casual_words for w in collapsed_tokens)) or (raw_tokens and all(w in casual_words for w in raw_tokens)):
        return "Casual Chat"

    if any(p in norm_text for p in ["how's life", "how is life", "kaisa hai", "kaise ho", "kya haal"]):
        if len(raw_tokens) <= 6:
            return "Casual Chat"

    if "capable to solve" in text.lower() or "what type of question" in text.lower():
        return "Cortex Capabilities"

    # Strip search and conversational prefixes
    text = re.sub(r"^(hi+|hello+|hey+|yo+|hola+|kaise ho|kaisa hai|bro+|bhai|yrr|yaar)[\s\.,!?]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(search the web for|search web for|search for|google for)[\s\.,;:]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(talk in english\/hinglish|talk in english|talk in hindi|talk in hinglish)[\s\.,;:]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(lets explore|let\'s explore|lets discuss|let\'s discuss)[\s\.,;:]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(i need quick answers\s*[\-–:]*|give me quick answers\s*[\-–:]*)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(act as an?|you are an?|pretend to be)[\s\w\.,;:]*?(architect|developer|expert|engineer|specialist|assistant)[\s\.,;:]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(provide a concise,? executive summary with all formulas and concepts of chapter|provide a concise,? executive summary with all formulas and concepts of|provide a concise,? executive summary of|provide a summary of|give me a summary of|give complete deep-dive of|give deep-dive of|summarize)[\s\.,;:]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(write a python code for|write a python script for|write python code for|write a python|write code for|write an?|create an?|build an?|generate an?|make an?|design an?)[\s\.,;:]*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(what is|what are|explain|how does|why do|why does|tell me about|can you explain|can you|give diff b\/w|difference between)[\s\.,;:]*", "", text, flags=re.IGNORECASE)

    text = " ".join(text.split()).strip(" ,.-;:!?")
    lower = text.lower()

    # Semantic subject overrides & pattern detection (Checked BEFORE generic math)
    if ("carrier" in lower or "career" in lower) and any(k in lower for k in ["trend", "india", "youth", "ai", "future", "job", "growth", "dead", "astra", "fable"]):
        return "Trending Careers in India"
    if "wtc" in lower or "world test championship" in lower or ("test cricket" in lower and "points" in lower):
        return "WTC Standings 2025–27"
    if "cricket" in lower:
        return "Cricket Analysis"
    if "rotational motion" in lower:
        return "Rotational Motion"
    if "work" in lower and ("energy" in lower or "power" in lower):
        return "Work, Energy & Power"
    if "rate limiter" in lower or "distributed rate" in lower:
        return "Distributed Rate Limiter"
    if "human exist" in lower or "why humans exist" in lower or "why human exist" in lower:
        return "Why Humans Exist"
    if "digestion" in lower or "human digestion" in lower:
        return "Human Digestion System"
    if "electromagnetic induction" in lower or lower.strip() == "emi in physics":
        return "Electromagnetic Induction"
    if "thermodynamics" in lower:
        return "Thermodynamics"
    if "pattern" in lower and ("java" in lower or "star" in lower or "pyramid" in lower):
        return "Java Pattern Matching"
    if "scrape" in lower and "news" in lower:
        return "Python News Scraper"
    if "compare sales" in lower or ("apple" in lower and "microsoft" in lower):
        return "Apple vs Microsoft Sales"
    if "ml" in lower and ("diff" in lower or "dl" in lower or "gen ai" in lower or "vs" in lower):
        return "ML vs DL vs GenAI"
    if "as a ai" in lower or "problem face" in lower or "ai life" in lower:
        return "AI Life & Challenges"
    if "neumorphic calculator" in lower:
        return "Neumorphic Calculator"
    if "fastapi" in lower:
        if "masterbook" in lower:
            return "FastAPI Masterbook"
        if "websocket" in lower:
            return "FastAPI WebSockets"
        return "FastAPI Service"
    if "minimal game" in lower or "pygame" in lower or "python game" in lower or lower.startswith("minimal game"):
        return "Python Minimal Game"
    if "attention mechanism" in lower or "transformer" in lower:
        return "Transformer Attention"

    # Math calculations (e.g. 5 plus 5) - must NOT trigger on year ranges (e.g. 2025-2027) or within long conversational prompts
    is_year_range = bool(re.search(r"\b(19\d\d|20\d\d)\s*[-/–]\s*(19\d\d|20\d\d|\d\d)\b", text))
    if not is_year_range:
        words_count = len(text.split())
        has_math_word = any(w in lower for w in ["calculate", "solve", "math", "plus", "minus", "times", "divided by", "sum of"])
        if words_count <= 6 or has_math_word:
            m = re.search(r"(\d+)\s*(plus|\+|\-|minus|\*|times|\/|divided by)\s*(\d+)", text, re.IGNORECASE)
            if m:
                n1, n2 = int(m.group(1)), int(m.group(3))
                if not (1900 <= n1 <= 2099 and 1900 <= n2 <= 2099):
                    op = m.group(2).lower()
                    symbol = "+" if op in ("plus", "+") else ("-" if op in ("minus", "-") else ("×" if op in ("times", "*") else "÷"))
                    return f"Math: {m.group(1)} {symbol} {m.group(3)}"

    if not text:
        return "Casual Chat"

    # Take first 3-4 core words, skipping stopwords
    words = [w for w in text.split() if w.lower() not in {"in", "the", "a", "an", "of", "for", "with", "and"}]
    if not words:
        words = text.split()

    clean = " ".join(words[:4]).strip(" ,.-;:!?")
    if len(clean) > 36 and " " in clean:
        clean = clean[:36].rsplit(" ", 1)[0]
    return clean.title()


# ---------------------------------------------------------------------------
# Memories & Custom Instructions Endpoints (User Scoped)
# ---------------------------------------------------------------------------

class AddMemoryPayload(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    category: Optional[str] = "preference"


@app.get("/api/memories")
def get_user_memories(current_user: dict = Depends(get_current_user)):
    """Fetch persistent memories for the logged in user."""
    return database.get_memories(user_id=current_user["id"])


@app.post("/api/memories")
def create_user_memory(payload: AddMemoryPayload, current_user: dict = Depends(get_current_user)):
    """Manually add a persistent memory for the user."""
    return database.add_memory(
        user_id=current_user["id"],
        content=payload.content,
        category=payload.category or "preference",
    )


@app.delete("/api/memories/{memory_id}")
def remove_user_memory(memory_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a specific memory."""
    success = database.delete_memory(memory_id=memory_id, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"ok": True}


@app.delete("/api/memories")
def clear_all_user_memories(current_user: dict = Depends(get_current_user)):
    """Clear all memories for the user."""
    database.clear_memories(user_id=current_user["id"])
    return {"ok": True}


class InstructionsPayload(BaseModel):
    instructions: str = Field(default="", max_length=10000)


@app.get("/api/user/instructions")
def get_user_instructions(current_user: dict = Depends(get_current_user)):
    """Fetch global custom instructions for the user."""
    instructions = database.get_user_custom_instructions(user_id=current_user["id"])
    return {"instructions": instructions}


@app.put("/api/user/instructions")
def update_user_instructions(payload: InstructionsPayload, current_user: dict = Depends(get_current_user)):
    """Update global custom instructions for the user."""
    database.update_user_custom_instructions(user_id=current_user["id"], instructions=payload.instructions)
    return {"ok": True, "instructions": payload.instructions}


@app.patch("/api/conversations/{conv_id}/instructions")
def update_conv_instructions(
    conv_id: str,
    payload: InstructionsPayload,
    current_user: dict = Depends(get_current_user),
):
    """Update custom instructions for a specific conversation."""
    existing = database.get_conversation(conv_id, user_id=current_user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Conversation not found")
    database.update_conversation_custom_instructions(conv_id=conv_id, instructions=payload.instructions)
    return {"ok": True, "instructions": payload.instructions}




# ---------------------------------------------------------------------------
# Message Feedback, Pruning & Conversation Branching / Forking (Phase 4)
# ---------------------------------------------------------------------------

class MessageFeedbackPayload(BaseModel):
    feedback: int = Field(ge=-1, le=1)


class ForkConversationPayload(BaseModel):
    message_id: Optional[str] = None
    up_to_message_id: Optional[str] = None
    title: Optional[str] = None
    new_title: Optional[str] = None

    @property
    def target_message_id(self) -> Optional[str]:
        return self.message_id or self.up_to_message_id

    @property
    def target_title(self) -> Optional[str]:
        return self.title or self.new_title


@app.patch("/api/messages/{message_id}/feedback")
def update_message_feedback_endpoint(
    message_id: str,
    payload: MessageFeedbackPayload,
    current_user: dict = Depends(get_current_user),
):
    """Update user rating/feedback on an assistant message: 1 (helpful), -1 (unhelpful), 0 (neutral)."""
    success = database.set_message_feedback(message_id, payload.feedback, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or unauthorized.")
    return {"ok": True, "message_id": message_id, "feedback": payload.feedback}


@app.delete("/api/conversations/{conv_id}/messages/{message_id}")
def delete_message_and_subsequent_endpoint(
    conv_id: str,
    message_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Prune/delete a message and all subsequent turns from SQLite (used for clean edits & retries)."""
    success = database.delete_messages_after(conv_id, message_id, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Message not found or unauthorized.")
    return {"ok": True, "deleted_from": message_id}


@app.post("/api/conversations/{conv_id}/fork")
def fork_conversation_endpoint(
    conv_id: str,
    payload: Optional[ForkConversationPayload] = None,
    current_user: dict = Depends(get_current_user),
):
    """Branch/fork an existing conversation from a specific turn into a new conversation thread."""
    target_msg_id = payload.target_message_id if payload else None
    target_title = payload.target_title if payload else None
    forked = database.fork_conversation(
        conv_id,
        up_to_message_id=target_msg_id,
        user_id=current_user["id"],
        new_title=target_title,
    )
    if not forked:
        raise HTTPException(status_code=404, detail="Conversation or message not found.")
    return forked


# ---------------------------------------------------------------------------
# Project Workspaces REST endpoints (User Scoped)
# ---------------------------------------------------------------------------

class ProjectCreatePayload(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: Optional[str] = ""
    system_prompt: Optional[str] = ""


class ProjectUpdatePayload(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None


class ConversationProjectPayload(BaseModel):
    project_id: Optional[str] = None


@app.get("/api/projects")
def list_projects_endpoint(current_user: dict = Depends(get_current_user)):
    """List all project workspaces belonging to the user."""
    return database.get_projects(user_id=current_user["id"])


@app.post("/api/projects")
def create_project_endpoint(payload: ProjectCreatePayload, current_user: dict = Depends(get_current_user)):
    """Create a new project workspace with custom knowledge and directives."""
    project = database.create_project(
        name=payload.name,
        description=payload.description or "",
        system_prompt=payload.system_prompt or "",
        user_id=current_user["id"],
    )
    return project


@app.get("/api/projects/{project_id}")
def get_project_endpoint(project_id: str, current_user: dict = Depends(get_current_user)):
    """Get details of a specific project workspace."""
    project = database.get_project(project_id, user_id=current_user["id"])
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@app.put("/api/projects/{project_id}")
def update_project_endpoint(project_id: str, payload: ProjectUpdatePayload, current_user: dict = Depends(get_current_user)):
    """Update project name, description, or system directives."""
    existing = database.get_project(project_id, user_id=current_user["id"])
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found.")

    name = payload.name if payload.name is not None else existing["name"]
    description = payload.description if payload.description is not None else existing["description"]
    system_prompt = payload.system_prompt if payload.system_prompt is not None else existing["system_prompt"]

    success = database.update_project(
        project_id,
        name=name,
        description=description,
        system_prompt=system_prompt,
        user_id=current_user["id"],
    )
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update project.")
    return database.get_project(project_id, user_id=current_user["id"])


@app.delete("/api/projects/{project_id}")
def delete_project_endpoint(project_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a project workspace and unlink all associated conversations."""
    success = database.delete_project(project_id, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Project not found.")
    return {"ok": True, "deleted_project_id": project_id}


@app.patch("/api/conversations/{conv_id}/project")
def set_conversation_project_endpoint(conv_id: str, payload: ConversationProjectPayload, current_user: dict = Depends(get_current_user)):
    """Assign or unassign a conversation to a project workspace."""
    success = database.set_conversation_project(conv_id, payload.project_id, user_id=current_user["id"])
    if not success:
        raise HTTPException(status_code=404, detail="Conversation or project not found.")
    return {"ok": True, "conversation_id": conv_id, "project_id": payload.project_id}


@app.get("/api/user/usage")
def get_user_usage_endpoint(current_user: dict = Depends(get_current_user)):
    """Return user's daily tokens and upload usage quota."""
    return database.get_daily_usage(current_user["id"])


@app.get("/api/artifacts")
def get_user_artifacts_endpoint(current_user: dict = Depends(get_current_user)):
    """Return all markdown documents, code files, and reports across user conversations."""
    artifacts = database.get_user_artifacts(current_user["id"])
    return {"artifacts": artifacts, "total": len(artifacts)}


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Server-Sent Events stream. Emits:
    - {"type": "init", "conversation_id": "...", "title": "...", "model": "..."}
    - {"type": "tool_start", "name": "...", "label": "...", "args": {...}}
    - {"type": "tool_end", "name": "...", "label": "...", "result": "..."}
    - {"type": "tools", "tools_used": [...]}
    - {"type": "token", "text": "..."}
    - {"type": "done", "conversation_id": "..."}
    - {"type": "error", "detail": "..."}
    """
    if not request.messages:
        raise HTTPException(status_code=400, detail="Send at least one message.")

    mode = (request.mode or "auto").lower().strip()
    if mode not in ALLOWED_MODES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid mode '{request.mode}'. Allowed modes are: auto, fast, thinking.",
        )

    req_model = (request.model or MODEL_NAME).strip()
    if req_model not in VALID_MODEL_IDS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid model '{request.model}'. Please choose an active model from the available models list.",
        )

    user_id = current_user["id"]
    if not acquire_user_stream(user_id):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many concurrent streaming requests. You already have 2 active requests in progress. Please wait for one to complete.",
        )

    try:
        conv_id = request.conversation_id
        raw_content = request.messages[-1].content

        if request.project_id:
            proj = database.get_project(request.project_id, user_id=current_user["id"])
            if not proj:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project workspace not found or does not belong to your account.",
                )

        if not conv_id:
            title = generate_smart_title(raw_content)
            conv = database.create_conversation(title=title, user_id=current_user["id"], project_id=request.project_id)
            conv_id = conv["id"]
        else:
            existing = database.get_conversation(conv_id, user_id=current_user["id"])
            if not existing:
                title = generate_smart_title(raw_content)
                database.create_conversation(title=title, conv_id=conv_id, user_id=current_user["id"], project_id=request.project_id)
            else:
                if request.project_id and not existing.get("project_id"):
                    database.set_conversation_project(conv_id, request.project_id, user_id=current_user["id"])
                existing_title = (existing.get("title") or "").strip()
                is_placeholder = (
                    not existing_title
                    or existing_title in ("New Chat", "Casual Chat", "Untitled", "Chat")
                    or any(g in existing_title.lower() for g in ["hi bro", "hello bro", "heelllllo", "kaisa hai", "kaise ho", "how are u", "how's life"])
                )
                if not is_placeholder:
                    title = existing_title
                else:
                    new_candidate = generate_smart_title(raw_content)
                    if new_candidate != "Casual Chat":
                        title = new_candidate
                        database.update_conversation_title(conv_id, title, user_id=current_user["id"])
                    else:
                        title = existing_title or "Casual Chat"

        messages, last_user = _build_messages(request, user_id=current_user["id"], conv_id=conv_id)

        # Save user message to persistent DB
        user_msg = database.add_message(conv_id, role="user", content=last_user.content, user_id=current_user["id"])
        user_msg_id = user_msg["id"]
    except Exception:
        release_user_stream(user_id)
        raise

    def event(data: dict) -> str:
        return f"data: {json.dumps(data)}\n\n"

    effective_model = req_model
    if has_image and effective_model != "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning":
        effective_model = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"

    def generate():
        ctx_token = _current_user_id_ctx.set(current_user["id"])
        plot_token = _current_harvested_plots_ctx.set([])
        full_text = ""
        tools_used = []
        quota_reserved = False
        estimated_tokens = 1500
        try:
            budget_tokens = estimate_response_tokens(effective_model, raw_content, mode=mode)
            estimated_tokens = min(budget_tokens, 4000)
            yield event({
                "type": "init",
                "conversation_id": conv_id,
                "title": title,
                "model": effective_model,
                "mode": mode,
                "budget_tokens": budget_tokens,
                "user_message_id": user_msg_id,
            })

            tokens_ok, used_tok, limit_tok = database.reserve_quota(current_user["id"], estimated_tokens=estimated_tokens)
            if not tokens_ok:
                err_msg = f"Daily token quota reached ({used_tok:,} / {limit_tok:,} tokens). Your quota resets at midnight UTC. Thank you for building with Cortex Agent!"
                yield event({"type": "token", "text": err_msg})
                yield event({
                    "type": "done",
                    "conversation_id": conv_id,
                    "user_message_id": user_msg_id,
                    "assistant_message_id": None,
                    "full_text": err_msg,
                    "usage": database.get_daily_usage(current_user["id"]),
                })
                return
            quota_reserved = True

            # Check if user explicitly asked to save a memory
            mem_match = re.search(
                r"\b(remember that|remember this|yaad rakh|yaad rakhna|note down that|save to memory|store in memory|keep in mind that)\b\s*:?\s*(.+)",
                raw_content,
                re.IGNORECASE | re.DOTALL,
            )
            raw_memory_fact = None
            raw_memory_cat = "preference"
            if mem_match:
                raw_memory_fact = mem_match.group(2).strip()
                raw_memory_fact = re.sub(
                    r"(?:for future reference|please|plz|across sessions|in future|okay\??|theek hai\??)[\.\s]*$",
                    "",
                    raw_memory_fact,
                    flags=re.IGNORECASE,
                ).strip()
                low_fact = raw_memory_fact.lower()
                if any(k in low_fact for k in ["project", "stack", "fastapi", "app", "payflow", "backend", "frontend"]):
                    raw_memory_cat = "project"
                elif any(k in low_fact for k in ["prefer", "like", "style", "functional", "typescript"]):
                    raw_memory_cat = "preference"
                elif any(k in low_fact for k in ["rule", "never", "always"]):
                    raw_memory_cat = "rule"
                else:
                    raw_memory_cat = "preference"

            # Determine whether tools should be executed based on mode:
            # - For visual screenshots: stream visual inspection directly without blocking on web tools
            # - "fast": single-round local tools (remember, calculator) when requested; skips heavy web browsing
            # - "thinking": full multi-round agentic tools & deep research
            tools_subset = None
            max_rounds = None

            if has_image and mode != "thinking":
                run_tools = False
            elif mode == "fast":
                run_tools = should_run_fast_tools(raw_content)
                if run_tools:
                    tools_subset = [remember, calculator]
                    max_rounds = 2
            elif mode == "thinking":
                run_tools = True
            else:
                run_tools = should_run_tools(raw_content, messages)

            if run_tools:
                for ev_type, payload in run_tool_rounds_streaming(messages, model_override=effective_model, tools_subset=tools_subset, max_rounds=max_rounds):
                    if ev_type == "tool_start":
                        yield event({"type": "tool_start", **payload})
                    elif ev_type == "tool_end":
                        yield event({"type": "tool_end", **payload})
                    elif ev_type == "tools_used":
                        tools_used = payload

            # Deterministic Memory Persistence:
            # Ensure the memory fact is actually stored in SQLite database:
            if raw_memory_fact:
                existing_mems = database.get_memories(current_user["id"])
                already_saved = any(
                    raw_memory_fact.lower() in (m.get("content", "")).lower()
                    or (m.get("content", "")).lower() in raw_memory_fact.lower()
                    for m in existing_mems
                )
                if not already_saved:
                    try:
                        database.add_memory(user_id=current_user["id"], content=raw_memory_fact, category=raw_memory_cat)
                        if "remember" not in tools_used:
                            tools_used.append("remember")
                            yield event({"type": "tool_start", "name": "remember", "label": "Memory Storage", "args": {"fact": raw_memory_fact, "category": raw_memory_cat}})
                            yield event({"type": "tool_end", "name": "remember", "label": "Memory Storage", "result": f"Saved to persistent memory: \"{raw_memory_fact}\""})
                    except Exception as mem_err:
                        print(f"Memory fallback error: {mem_err}")
                elif "remember" not in tools_used:
                    tools_used.append("remember")

                messages.append(
                    SystemMessage(
                        content=(
                            f"[PERSISTENT MEMORY CONFIRMATION: The fact '{raw_memory_fact}' has been successfully stored in persistent memory. "
                            "In your final response to the user, confirm this clearly and warmly. "
                            "DO NOT output any tool calls, function tags, or JSON objects.]"
                        )
                    )
                )

            yield event({"type": "tools", "tools_used": tools_used})

            # Transition directive after tool rounds to aggregate research data and instruct synthesis
            synthesis_messages = list(messages)
            if tools_used:
                research_snippets = []
                for m in messages:
                    if isinstance(m, ToolMessage) and getattr(m, "content", None):
                        c = str(m.content).strip()
                        if c:
                            research_snippets.append(c)

                research_context = "\n\n".join(research_snippets)
                directive_content = (
                    "### Verified Real-Time Research Facts:\n"
                    f"{research_context}\n\n"
                    if research_context else ""
                ) + (
                    "[SYNTHESIS DIRECTIVE: All research and tool executions are finished. "
                    "Synthesize the verified facts above with your deep knowledge into an exhaustive, "
                    "authoritative, and beautifully structured final response directly to the user in clean Markdown. "
                    "Include comparison tables, pros/cons, and actionable guidance where appropriate. "
                    "DO NOT output any tool calls, function tags, XML tags, search queries, or JSON objects. "
                    "Write the complete final response in Markdown now.]"
                )
                synthesis_messages.append(SystemMessage(content=directive_content))

            llm = make_llm(model_override=effective_model, streaming=True, max_tokens=budget_tokens)
            max_attempts = 3
            is_truncated = False
            last_finish_reason = None

            VALID_TOOL_NAMES = {
                "remember", "web_search", "fetch_webpage",
                "calculator", "weather_lookup", "current_datetime", "wikipedia_lookup"
            }

            for attempt in range(max_attempts):
                try:
                    stream_buffer = ""
                    is_tool_call_stream = None  # None = undecided, True = tool intercepted, False = normal text
                    intercepted_tool_info = None

                    for chunk in llm.stream(synthesis_messages):
                        meta = getattr(chunk, "response_metadata", {}) or {}
                        add_kw = getattr(chunk, "additional_kwargs", {}) or {}
                        fr = meta.get("finish_reason") or add_kw.get("finish_reason")
                        if fr:
                            last_finish_reason = fr

                        text = _chunk_to_text(chunk.content)
                        if not text:
                            continue

                        # If normal streaming has been established:
                        if is_tool_call_stream is False:
                            clean_chunk = re.sub(r"<\/?(?:tool_call|function|parameter|execute_pythoncode)[^>]*>", "", text)
                            clean_chunk = re.sub(r"=\s*<execute_pythoncode>", "", clean_chunk)
                            clean_chunk = re.sub(r"=\s*execute_pythoncode>", "", clean_chunk)
                            if clean_chunk:
                                full_text += clean_chunk
                                yield event({"type": "token", "text": clean_chunk})
                            continue

                        # Still evaluating or buffering initial tokens
                        stream_buffer += text
                        stripped_buf = stream_buffer.lstrip()

                        if not stripped_buf:
                            continue

                        # If undecided whether this stream is a tool call or normal text:
                        if is_tool_call_stream is None:
                            # If buffer is short, check if it could be start of tool call
                            if len(stripped_buf) < 35 and any(stripped_buf.startswith(prefix) for prefix in ["{", "<", "=", "</", "```"]):
                                continue  # wait for more tokens to clarify intent

                            # Check if stream starts with tool signature or markdown-wrapped tool JSON
                            if (
                                (stripped_buf.startswith("{") and ('"tool"' in stripped_buf or '"name"' in stripped_buf))
                                or re.search(r"^(?:=\s*<?execute_pythoncode>?|<\/?function=|<\/?tool_call>)", stripped_buf)
                                or (stripped_buf.startswith("```") and ('"tool"' in stripped_buf or '"execute_python"' in stripped_buf or '"remember"' in stripped_buf))
                            ):
                                is_tool_call_stream = True
                                continue
                            else:
                                is_tool_call_stream = False
                                full_text += stream_buffer
                                yield event({"type": "token", "text": stream_buffer})
                                stream_buffer = ""
                                continue

                        # If tool call stream is active, keep accumulating all tokens silently until stream ends
                        if is_tool_call_stream is True:
                            continue

                    # If stream ended and we still had buffered normal text:
                    if stream_buffer and is_tool_call_stream is not True:
                        clean_buf = re.sub(r"<\/?(?:tool_call|function|parameter|execute_pythoncode)[^>]*>", "", stream_buffer)
                        clean_buf = re.sub(r"=\s*<execute_pythoncode>", "", clean_buf)
                        clean_buf = re.sub(r"=\s*execute_pythoncode>", "", clean_buf)
                        if clean_buf:
                            full_text += clean_buf
                            yield event({"type": "token", "text": clean_buf})

                    # If a tool call was intercepted in the stream:
                    if is_tool_call_stream is True and stream_buffer:
                        # 1. Store Persistent Memory if requested
                        if "remember" in stream_buffer:
                            fact = None
                            if stream_buffer.lstrip().startswith("{"):
                                try:
                                    p = json.loads(stream_buffer.strip())
                                    args = p.get("arguments") or p.get("args") or {}
                                    fact = args.get("fact")
                                except Exception:
                                    pass
                            if not fact:
                                m_rem = re.search(r"(?:<\/?function=remember>|<\/?tool_call>\s*remember)", stream_buffer)
                                rem_content = stream_buffer[m_rem.end():].strip() if m_rem else stream_buffer
                                rem_content = re.sub(r"<\/?(?:parameter|function|tool_call)[^>]*>", "", rem_content).strip()
                                if rem_content:
                                    fact = rem_content

                            if fact:
                                database.add_memory(user_id=current_user["id"], content=fact, category="preference")
                                if "remember" not in tools_used:
                                    tools_used.append("remember")
                                yield event({"type": "tool_start", "name": "remember", "label": "Memory Storage", "args": {"fact": fact}})
                                yield event({"type": "tool_end", "name": "remember", "label": "Memory Storage", "result": f"Saved: {fact}"})
                                reply = f"I have saved this to your persistent memory: **\"{fact}\"**"
                            else:
                                reply = "I checked your stored memories, but I don't have any details saved for this yet. Feel free to share your preferences or project details!"
                            full_text = reply
                            yield event({"type": "token", "text": reply})
                            break

                        # 2. Stray tool call emitted during synthesis:
                        # CRITICAL: DO NOT yield the raw tool query/XML to the user!
                        print(f"Synthesis stream intercepted stray tool call: {stream_buffer[:80]}... Discarding tool call output.")
                        full_text = ""

                    if full_text.strip():
                        break
                    time.sleep(1.5)
                except Exception as stream_err:
                    print(f"Streaming attempt {attempt + 1} failed: {type(stream_err).__name__}: {stream_err}")
                    if attempt < max_attempts - 1 and len(full_text.strip()) < 120:
                        full_text = ""
                        time.sleep(1.5 * (attempt + 1))
                        continue
                    break

            if last_finish_reason == "length":
                is_truncated = True

            # Clean any broken/unresolved placeholder images
            full_text = re.sub(r"!\[(.*?)\]\(((?:attachment:\/\/|sandbox:\/)[^\)]*)\)", "", full_text)

            # Heal split/broken markdown image tags e.g. ![alt]\n(data:image...) or naked (data:image/png;base64...)
            full_text = re.sub(r"!\[([^\]]*)\]\s*\n+\s*\(((?:data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]+|https?:\/\/[^\)\s]+))\)", r"![\1](\2)", full_text)
            full_text = re.sub(r"(?:^|\n)\s*\(((data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]{60,}))\)", r"\n\n![Generated Plot](\1)\n\n", full_text)
            full_text = re.sub(r"(?:^|\n)\s*(data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]{60,})\s*(?:\n|$)", r"\n\n![Generated Plot](\1)\n\n", full_text)

            # Auto-heal unclosed code blocks if generation ended mid-block
            fence_count = len(re.findall(r"```", full_text))
            if fence_count % 2 != 0:
                repair_close = "\n```\n"
                full_text += repair_close
                yield event({"type": "token", "text": repair_close})
                is_truncated = True

            # Fallback if streaming failed, was aborted by 503, or produced no tokens, raw tool output, or unsubstantive snippet
            is_raw_tool_output = (
                full_text.strip().startswith("<tool_call")
                or bool(re.search(r'^\s*\{\s*"tool"\s*:', full_text.strip()))
                or bool(re.search(r'^\s*\[(?:web_search|execute_python|remember):', full_text.strip()))
                or bool(re.search(r'^\s*```(?:json)?\s*\{\s*"tool"\s*:', full_text.strip()))
                or bool(re.search(r'<\/?(?:function|tool_call|parameter)', full_text))
            )
            is_unsubstantive = len(full_text.strip()) < 120 and len(raw_content) > 30
            if not full_text.strip() or is_raw_tool_output or is_unsubstantive or last_finish_reason == "tool_calls":
                try:
                    print("Streaming produced empty, unsubstantive, or invalid response; attempting non-streaming fallback invoke...")
                    had_partial = bool(full_text.strip())
                    fallback_messages = list(synthesis_messages) + [
                        SystemMessage(content=(
                            "[SYNTHESIS DIRECTIVE: Provide the final response directly to the user in comprehensive, well-structured Markdown. "
                            "Do NOT output any tool calls, function tags, XML tags, search queries, or JSON objects. "
                            "Provide the complete, in-depth final answer now.]"
                        ))
                    ]
                    fallback_llm = make_llm(model_override=effective_model, streaming=False, max_tokens=budget_tokens)
                    res = fallback_llm.invoke(fallback_messages)
                    fallback_text = _chunk_to_text(res.content).strip()
                    if fallback_text:
                        clean_text = re.sub(r"<tool_call>[\s\S]*?</tool_call>", "", fallback_text).strip()
                        clean_text = re.sub(r"<\/?(?:function|parameter|tool_call)[^>]*>", "", clean_text).strip()
                        clean_text = re.sub(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"[^"]+"\s*:\s*[\s\S]*?\}', "", clean_text).strip()
                        final_text = clean_text if clean_text else fallback_text
                        if final_text:
                            full_text = final_text
                            if had_partial:
                                yield event({"type": "replace_text", "text": final_text})
                            else:
                                yield event({"type": "token", "text": final_text})
                except Exception as fb_err:
                    print(f"Fallback invoke failed: {fb_err}")

            # If still completely empty after streaming and fallback, provide a clean fallback message
            if not full_text.strip():
                fallback_msg = (
                    "I experienced a momentary connection interruption while processing this request. "
                    "Please try submitting your message again."
                )
                full_text = fallback_msg
                yield event({"type": "token", "text": fallback_msg})

            # Save completed assistant reply (cleaned of any raw tool tags or raw tool calls)
            asst_msg_id = None
            cleaned_db_text = full_text
            if full_text.strip():
                def _unwrap_code_block(m):
                    inner = m.group(1).strip()
                    if "{" in inner and ('"tool"' in inner or '"code"' in inner):
                        try:
                            start_b = inner.find("{")
                            end_b = inner.rfind("}")
                            if start_b != -1 and end_b != -1:
                                p = json.loads(inner[start_b:end_b+1])
                                args = p.get("arguments") or p.get("args") or {}
                                extracted = args.get("code") or p.get("code")
                                if extracted:
                                    return f"```python\n{extracted.strip()}\n```"
                        except Exception:
                            pass
                    return m.group(0)

                cleaned_db_text = re.sub(r"```(?:python|py|json|execute_python)?\s*([\s\S]*?)\s*```", _unwrap_code_block, full_text)
                cleaned_db_text = re.sub(r"```execute_python", "```python", cleaned_db_text)
                cleaned_db_text = re.sub(r"<tool_call>[\s\S]*?<\/tool_call>", "", cleaned_db_text)
                cleaned_db_text = re.sub(r"<\/?(?:tool_call|function|parameter|execute_pythoncode)[^>]*>", "", cleaned_db_text)
                cleaned_db_text = re.sub(r"=\s*<execute_pythoncode>", "", cleaned_db_text)
                cleaned_db_text = re.sub(r"=\s*execute_pythoncode>", "", cleaned_db_text)
                cleaned_db_text = re.sub(r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:\s*\{[\s\S]*?\}\s*\}', "", cleaned_db_text)
                cleaned_db_text = re.sub(r"!\[(.*?)\]\(((?:attachment:\/\/|sandbox:\/)[^\)]*)\)", "", cleaned_db_text)
                cleaned_db_text = re.sub(r"!\[([^\]]*)\]\s*\n+\s*\(((?:data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]+|https?:\/\/[^\)\s]+))\)", r"![\1](\2)", cleaned_db_text)
                cleaned_db_text = re.sub(r"(?:^|\n)\s*\(((data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]{60,}))\)", r"\n\n![Generated Plot](\1)\n\n", cleaned_db_text)
                cleaned_db_text = re.sub(r"(?:^|\n)\s*(data:image\/[a-zA-Z0-9+\-_]+;base64,[A-Za-z0-9+/=]{60,})\s*(?:\n|$)", r"\n\n![Generated Plot](\1)\n\n", cleaned_db_text)
                cleaned_db_text = cleaned_db_text.strip()
                asst_msg = database.add_message(conv_id, role="assistant", content=cleaned_db_text or full_text, tools_used=tools_used, user_id=current_user["id"])
                asst_msg_id = asst_msg["id"]

            if is_truncated:
                yield event({"type": "truncated", "reason": "length", "conversation_id": conv_id})

            # Calculate consumed tokens excluding massive base64 image data and increment daily token usage
            has_image_b64 = bool(re.search(r"\(Visual Image Base64:\s*data:image\/", raw_content))
            clean_raw_text = re.sub(r"\(Visual Image Base64:\s*data:image\/[^;]+;base64,[A-Za-z0-9+/=]+\)", "", raw_content).strip()
            # Standard multi-modal vision token budget (~800 tokens per image tile in modern vision LLMs)
            image_token_cost = 800 if has_image_b64 else 0
            consumed_tokens = max(1, (len(clean_raw_text) + len(full_text)) // 4 + image_token_cost)
            current_usage = database.release_quota(current_user["id"], estimated_tokens=estimated_tokens, actual_tokens=consumed_tokens)
            quota_reserved = False

            yield event({
                "type": "done",
                "conversation_id": conv_id,
                "user_message_id": user_msg_id,
                "assistant_message_id": asst_msg_id,
                "full_text": cleaned_db_text or full_text,
                "usage": current_usage,
            })
        except HTTPException as exc:
            yield event({"type": "error", "detail": exc.detail})
        except (GeneratorExit, asyncio.CancelledError):
            # Stream aborted by user or connection closed
            if full_text.strip():
                try:
                    database.add_message(conv_id, role="assistant", content=full_text, tools_used=tools_used, user_id=current_user["id"])
                except Exception:
                    pass
            raise
        except Exception as exc:
            print(f"Stream error: {type(exc).__name__}: {exc}")
            if full_text.strip():
                try:
                    database.add_message(conv_id, role="assistant", content=full_text, tools_used=tools_used, user_id=current_user["id"])
                except Exception:
                    pass
            err_msg = str(exc)
            req_model = (request.model or MODEL_NAME or "").strip()
            if "resource exhausted" in err_msg.lower() or "limit reached" in err_msg.lower() or "16/16" in err_msg or "32/32" in err_msg:
                detail = "NVIDIA NIM worker capacity is temporarily full for this model. Please retry in a few seconds or switch to another model."
            elif "overloaded" in err_msg.lower() or "503" in err_msg:
                detail = "NVIDIA servers are temporarily overloaded. Please wait 5-10 seconds and click Retry."
            elif "rate limit" in err_msg.lower() or "429" in err_msg:
                detail = "NVIDIA API rate limit reached. Please wait a moment and click Retry."
            elif "410" in err_msg or "gone" in err_msg.lower():
                detail = "This model has reached its End-of-Life on NVIDIA NIM. Please select an active model from the dropdown."
            elif "404" in err_msg or "not found" in err_msg.lower():
                if "function not found for account" in err_msg.lower():
                    detail = f"Your current API key does not have entitlement for '{req_model}'. Please generate a key for this model on build.nvidia.com or select a Nemotron model."
                else:
                    detail = f"Model endpoint not found on NVIDIA NIM: {err_msg[:120]}"
            else:
                detail = f"Request failed: {err_msg[:140]}"
            yield event({"type": "error", "detail": detail})
        finally:
            if quota_reserved:
                try:
                    partial_tokens = max(0, len(full_text) // 4) if full_text.strip() else 0
                    database.release_quota(current_user["id"], estimated_tokens=estimated_tokens, actual_tokens=partial_tokens)
                except Exception as rel_err:
                    print(f"Error releasing quota in finally: {rel_err}")
                quota_reserved = False
            try:
                _current_user_id_ctx.reset(ctx_token)
            except Exception:
                _current_user_id_ctx.set(None)
            try:
                _current_harvested_plots_ctx.reset(plot_token)
            except Exception:
                _current_harvested_plots_ctx.set([])
            release_user_stream(current_user["id"])

    return StreamingResponse(generate(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
