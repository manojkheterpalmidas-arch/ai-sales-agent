import streamlit as st
from openai import OpenAI
import requests
import json
import re
from datetime import datetime
from supabase import create_client, Client

# ── SUPABASE CLIENT ───────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = get_supabase()

# ── STORAGE FUNCTIONS ─────────────────────────────────────────────────────────
def load_history():
    try:
        res = supabase.table("midas_history").select("*").order("date", desc=True).execute()
        return res.data or []
    except:
        return []

def save_history(entry):
    try:
        supabase.table("midas_history").upsert({
            "domain":       entry["domain"],
            "company":      entry["company"],
            "score":        entry["score"],
            "date":         entry["date"],
            "pages_count":  entry["pages_count"],
            "company_data": entry["company_data"],
            "sales_data":   entry["sales_data"],
        }, on_conflict="domain").execute()
    except Exception as e:
        st.warning(f"Could not save history: {e}")

def find_in_history(domain):
    try:
        res = supabase.table("midas_history").select("*").eq("domain", domain).execute()
        return res.data[0] if res.data else None
    except:
        return None

def load_notes():
    try:
        res = supabase.table("midas_notes").select("*").execute()
        return {r["domain"]: {"text": r["note_text"], "updated": r["updated"]} for r in res.data}
    except:
        return {}

def save_note(domain, note):
    try:
        supabase.table("midas_notes").upsert({
            "domain":    domain,
            "note_text": note,
            "updated":   datetime.now().strftime("%d %b %Y %H:%M")
        }, on_conflict="domain").execute()
    except Exception as e:
        st.warning(f"Could not save note: {e}")

def get_note(domain):
    try:
        res = supabase.table("midas_notes").select("*").eq("domain", domain).execute()
        if res.data:
            r = res.data[0]
            return {"text": r["note_text"], "updated": r["updated"]}
    except:
        pass
    return {}

def days_ago(date_str):
    try:
        dt = datetime.strptime(date_str, "%d %b %Y %H:%M")
        diff = (datetime.now() - dt).days
        if diff == 0:
            return "today"
        elif diff == 1:
            return "yesterday"
        else:
            return f"{diff} days ago"
    except:
        return "recently"

def delete_from_history(domain):
    try:
        supabase.table("midas_history").delete().eq("domain", domain).execute()
    except Exception as e:
        st.warning(f"Could not delete: {e}")
# # ── AUTH ──────────────────────────────────────────────────────────────────────
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False

# PASSCODE = "5487"

# if not st.session_state.authenticated:
#     st.set_page_config(page_title="MIDAS Pre Sales Intel", page_icon="🔐", layout="centered")
#     st.markdown("""
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700&family=JetBrains+Mono:wght@400&display=swap');
#     html, body, [class*="css"] { background: #f7f6f2 !important; font-family: 'Syne', sans-serif; }
#     .stApp { background: #f7f6f2 !important; }
#     .stTextInput > div > div > input {
#         background: white !important; color: #111 !important;
#         border: 1.5px solid #ddd !important; border-radius: 6px !important;
#         font-family: 'JetBrains Mono', monospace !important;
#         font-size: 22px !important; letter-spacing: 0.4em !important;
#         text-align: center !important; padding: 14px !important;
#         caret-color: #c8471e !important;
#     }
#     .stTextInput > div > div > input:focus { border-color: #c8471e !important; box-shadow: 0 0 0 3px rgba(200,71,30,0.1) !important; }
#     .stButton > button {
#         background: #111 !important; color: white !important;
#         border: none !important; border-radius: 6px !important;
#         font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
#         font-size: 13px !important; letter-spacing: 0.1em !important;
#         text-transform: uppercase !important; padding: 11px 28px !important;
#     }
#     .stButton > button:hover { background: #c8471e !important; color: white !important; }
#     div[data-testid="stButton"] > button > div > p,
#     div[data-testid="stButton"] button p,
#     div[data-testid="stButton"] button span,
#     div[data-testid="stButton"] button * { color: white !important; font-family: 'Syne', sans-serif !important; font-weight: 700 !important; }
#     </style>
#     """, unsafe_allow_html=True)

#     st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
#     c1, c2, c3 = st.columns([1, 2, 1])
#     with c2:
#         st.markdown("""
#         <div style='text-align:center;margin-bottom:32px;'>
#             <div style='font-family:Syne,sans-serif;font-size:11px;letter-spacing:0.3em;color:#c8471e;text-transform:uppercase;margin-bottom:6px;'>MIDAS IT</div>
#             <div style='font-family:Syne,sans-serif;font-size:32px;font-weight:700;color:#111;'>Sales Intelligence</div>
#             <div style='width:32px;height:3px;background:#c8471e;margin:12px auto 0;'></div>
#         </div>
#         """, unsafe_allow_html=True)
#         code = st.text_input("", type="password", placeholder="· · · ·", label_visibility="collapsed")
#         st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
#         if st.button("UNLOCK"):
#             if code == PASSCODE:
#                 st.session_state.authenticated = True
#                 st.rerun()
#             else:
#                 st.error("Incorrect passcode")
#     st.stop()

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MIDAS Pre Sales Intelligence", layout="wide", page_icon="🚀")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=JetBrains+Mono:wght@400;500&family=Barlow:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Barlow', sans-serif !important; background: #f7f6f2 !important; color: #111 !important; }
.stApp { background: #f7f6f2 !important; }
.stApp, .stApp * { color: #111 !important; }
.stApp .stButton button,
.stApp .stButton button *,
.stApp div[data-testid="stButton"] button,
.stApp div[data-testid="stButton"] button * { color: white !important; }
.stMarkdown, .stMarkdown * { color: #111 !important; }
.stTabs [data-baseweb="tab-panel"], .stTabs [data-baseweb="tab-panel"] * { color: #111 !important; }
.streamlit-expanderContent, .streamlit-expanderContent * { color: #111 !important; }
[data-testid="column"], [data-testid="column"] * { color: #111 !important; }
[data-testid="stMetricValue"] { color: #c8471e !important; }
[data-testid="stMetricLabel"] { color: #888 !important; }
.stAlert, .stAlert * { color: inherit !important; }
.stCaptionContainer, .stCaptionContainer * { color: #888 !important; }
a { color: #c8471e !important; }
a:hover { color: #a03518 !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem !important; max-width: 1400px !important; }

.stButton > button {
    background: #111 !important; color: white !important; border: none !important;
    border-radius: 6px !important; font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important; font-size: 13px !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important; padding: 11px 28px !important;
}
.stButton > button:hover { background: #c8471e !important; }

.stDownloadButton > button {
    background: transparent !important; color: #c8471e !important;
    border: 1.5px solid #c8471e !important; border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 12px !important; letter-spacing: 0.1em !important; text-transform: uppercase !important;
}
.stDownloadButton > button:hover { background: rgba(200,71,30,0.06) !important; }

.stTextInput > div > div > input {
    background: white !important; color: #111 !important;
    border: 1.5px solid #e0ddd5 !important; border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important;
    padding: 11px 14px !important; caret-color: #c8471e !important;
}
.stTextInput > div > div > input:focus { border-color: #c8471e !important; box-shadow: 0 0 0 3px rgba(200,71,30,0.1) !important; }
.stTextInput > div > div > input::placeholder { color: #bbb !important; }

.stTextArea > div > div > textarea {
    background: white !important; color: #111 !important;
    border: 1.5px solid #e0ddd5 !important; border-radius: 8px !important;
    font-family: 'Barlow', sans-serif !important; font-size: 14px !important;
    padding: 11px 14px !important; caret-color: #c8471e !important;
}
.stTextArea > div > div > textarea:focus { border-color: #c8471e !important; box-shadow: 0 0 0 3px rgba(200,71,30,0.1) !important; }

[data-testid="metric-container"] {
    background: white !important; border: 1px solid #e8e4dc !important;
    border-radius: 8px !important; padding: 16px 20px !important;
}
[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif !important; font-size: 28px !important; font-weight: 700 !important; color: #c8471e !important; }
[data-testid="stMetricLabel"] { font-family: 'JetBrains Mono', monospace !important; font-size: 10px !important; letter-spacing: 0.1em !important; color: #888 !important; text-transform: uppercase !important; }

.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 2px solid #e8e4dc !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif !important; font-size: 12px !important; font-weight: 700 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important; color: #999 !important;
    padding: 10px 20px !important; background: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] { color: #c8471e !important; border-bottom-color: #c8471e !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; }

.stProgress > div > div > div { background: #c8471e !important; border-radius: 2px !important; }
.stProgress > div > div { background: #e8e4dc !important; border-radius: 2px !important; }

.streamlit-expanderHeader {
    background: white !important; border: 1px solid #e8e4dc !important; border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important; font-size: 12px !important; font-weight: 700 !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important; color: #555 !important;
}
.stSuccess, .stInfo, .stWarning, .stError { border-radius: 6px !important; font-family: 'Barlow', sans-serif !important; font-size: 14px !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }

.sec-label {
    font-family: 'JetBrains Mono', monospace; font-size: 10px; font-weight: 500;
    letter-spacing: 0.2em; text-transform: uppercase; color: #c8471e; margin-bottom: 12px;
    display: flex; align-items: center; gap: 10px;
}
.sec-label::after { content:''; flex:1; height:1px; background:#e8e4dc; }

.insight-card {
    background: white; border: 1px solid #e8e4dc; border-left: 3px solid #c8471e;
    border-radius: 6px; padding: 14px 18px; margin-bottom: 10px;
    font-size: 14px; line-height: 1.7; color: #222;
}
.signal-card {
    background: white; border: 1px solid #e8e4dc; border-radius: 6px;
    padding: 12px 16px; margin-bottom: 8px; font-size: 13px; line-height: 1.6; color: #333;
}
.av {
    width: 38px; height: 38px; border-radius: 50%; background: #111; color: white;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.pill-tag { display: inline-block; font-family: 'JetBrains Mono', monospace; font-size: 10px; padding: 3px 9px; border: 1px solid #e0ddd5; border-radius: 20px; color: #888; margin: 2px; }
.pill-red   { border-color: rgba(200,71,30,0.4); color: #c8471e; background: rgba(200,71,30,0.05); }
.pill-amber { border-color: rgba(200,140,0,0.4); color: #8a5e00; background: rgba(200,140,0,0.05); }
.score-hot  { background: #fef0ed; color: #c8471e; border: 1px solid rgba(200,71,30,0.3); }
.score-warm { background: #fffbf0; color: #996600; border: 1px solid rgba(200,140,0,0.3); }
.score-cold { background: #f5f5f5; color: #666; border: 1px solid #ddd; }
.score-badge {
    display: inline-block; font-family: 'Syne', sans-serif; font-weight: 700;
    font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; padding: 6px 16px; border-radius: 20px;
}

</style>
""", unsafe_allow_html=True)

# ── CLIENTS ───────────────────────────────────────────────────────────────────
deepseek = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")

# ── FIRECRAWL FUNCTIONS ───────────────────────────────────────────────────────
def firecrawl_scrape_single(url):
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/credits",
            headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"]}, timeout=20
        )
        md = resp.json().get("data", {}).get("markdown", "")
        return [{"url": url, "markdown": md}] if md else []
    except:
        return []


def firecrawl_multi_scrape(base_url):
    from urllib.parse import urljoin, urlparse
    from bs4 import BeautifulSoup
    results = []
    visited = set()

    def scrape_one(url):
        if url in visited:
            return None
        visited.add(url)
        try:
            resp = requests.post(
                "https://api.firecrawl.dev/v1/scrape",
                headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}", "Content-Type": "application/json"},
                json={"url": url, "formats": ["markdown"]}, timeout=20
            )
            md = resp.json().get("data", {}).get("markdown", "")
            if md.strip():
                return {"url": url, "markdown": md}
        except:
            pass
        return None

    home = scrape_one(base_url)
    if not home:
        return []
    results.append(home)

    try:
        html_resp = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        soup = BeautifulSoup(html_resp.text, "html.parser")
        domain = urlparse(base_url).netloc
        priority_keywords = ["people","team","our-team","staff","leadership","directors","who-we-are","about","careers","jobs","vacancies","join","projects","services","what-we-do","contact"]
        all_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            if (parsed.netloc == domain and
                not any(full.endswith(ext) for ext in [".pdf",".jpg",".png",".zip"]) and
                "#" not in full and full != base_url and full not in visited):
                all_links.append(full)

        def priority_score(link):
            lower = link.lower()
            for i, kw in enumerate(priority_keywords):
                if kw in lower:
                    return i
            return 999

        sorted_links = sorted(set(all_links), key=priority_score)
    except:
        sorted_links = []

    for link in sorted_links[:14]:
        page = scrape_one(link)
        if page:
            results.append(page)
    return results


def direct_fetch(url):
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-GB,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cookie": "cookielawinfo-checkbox-necessary=yes; cookielawinfo-checkbox-analytics=yes; cookielawinfo-checkbox-functional=yes; cookielawinfo-checkbox-performance=yes; cookielawinfo-checkbox-advertisement=yes; viewed_cookie_policy=yes; cookie_consent=accepted; wordpress_gdpr_cookies_allowed=all; gdpr=1; euconsent=1"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        # Only add homepage if it has real content
        if len(text) > 500:
            results = [{"url": url, "markdown": text}]
        else:
            results = []

        # Also try to find and fetch subpages
        domain = urlparse(url).netloc
        visited = {url}
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(url, href)
            parsed = urlparse(full)
            if (parsed.netloc == domain and
                "#" not in full and
                full not in visited and
                not any(full.endswith(ext) for ext in [".pdf",".jpg",".png",".zip"])):
                visited.add(full)
                try:
                    sub = requests.get(full, headers=headers, timeout=10)
                    sub_soup = BeautifulSoup(sub.text, "html.parser")
                    for tag in sub_soup(["script", "style", "noscript", "iframe"]):
                        tag.decompose()
                    sub_text = sub_soup.get_text(separator="\n", strip=True)
                    if len(sub_text) > 200:
                        results.append({"url": full, "markdown": sub_text})
                except:
                    pass
        return results
    except:
        return []


def firecrawl_crawl(url, max_pages=30):
    try:
        # First try scraping with actions to handle cookie popups
        action_resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}", "Content-Type": "application/json"},
            json={
                "url": url,
                "formats": ["markdown"],
                "actions": [
                    {"type": "wait", "milliseconds": 2000},
                    {"type": "click", "selector": "button[class*='accept'], button[id*='accept'], button[class*='agree'], button[class*='consent'], .cookie-accept, #cookie-accept, .accept-cookies"},
                    {"type": "wait", "milliseconds": 1000}
                ]
            },
            timeout=30
        )
        action_data = action_resp.json()
        homepage_md = action_data.get("data", {}).get("markdown", "")

        if homepage_md and len(homepage_md) > 500:
            # Got homepage, now crawl the rest
            results = [{"url": url, "markdown": homepage_md}]
            try:
                resp = requests.post(
                    "https://api.firecrawl.dev/v1/crawl",
                    headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}", "Content-Type": "application/json"},
                    json={"url": url, "limit": max_pages, "scrapeOptions": {"formats": ["markdown"]}}, timeout=30
                )
                job_id = resp.json().get("id")
                if job_id:
                    import time
                    for _ in range(36):
                        time.sleep(5)
                        poll = requests.get(
                            f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                            headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}"},
                            timeout=15
                        ).json()
                        status = poll.get("status")
                        pages  = poll.get("data", [])
                        if status == "completed" or (status == "scraping" and len(pages) >= max_pages - 2):
                            extra = [
                                {"url": p.get("metadata", {}).get("sourceURL", url), "markdown": p.get("markdown", "")}
                                for p in pages if p.get("markdown", "").strip() and len(p.get("markdown","")) > 500
                            ]
                            results.extend(extra)
                            break
                        if status == "failed":
                            break
            except:
                pass
            return results

        # Action scrape didn't work, try normal crawl
        resp = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}", "Content-Type": "application/json"},
            json={"url": url, "limit": max_pages, "scrapeOptions": {"formats": ["markdown"]}}, timeout=30
        )
        job_id = resp.json().get("id")
        if not job_id:
            return firecrawl_multi_scrape(url)

        import time
        for _ in range(36):
            time.sleep(5)
            poll = requests.get(
                f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}"},
                timeout=15
            ).json()
            status = poll.get("status")
            pages  = poll.get("data", [])
            if status == "completed" or (status == "scraping" and len(pages) >= max_pages - 2):
                results = [
                    {"url": p.get("metadata", {}).get("sourceURL", url), "markdown": p.get("markdown", "")}
                    for p in pages if p.get("markdown", "").strip() and len(p.get("markdown","")) > 500
                ]
                if results:
                    return results
                return firecrawl_multi_scrape(url)
            if status == "failed":
                break

        return firecrawl_multi_scrape(url)
    except:
        return firecrawl_multi_scrape(url)

def get_firecrawl_credits():
    try:
        resp = requests.get(
            "https://api.firecrawl.dev/v1/team/credits",
            headers={"Authorization": f"Bearer {st.session_state['firecrawl_key']}"},
            timeout=10
        )
        data = resp.json()
        return data.get("credits", None)
    except:
        return None
# ── TEXT PREP ─────────────────────────────────────────────────────────────────
def build_corpus(pages):
    import re as _re
    per_page_limit = 30000 if len(pages) == 1 else 15000
    chunks = []
    for p in pages:
        md = p.get("markdown", "").strip()
        if not md:
            continue
        # Strip image tags to reduce noise
        md = _re.sub(r'!\[.*?\]\(.*?\)', '', md)
        # Strip empty lines
        md = _re.sub(r'\n{3,}', '\n\n', md)
        chunks.append(f"[PAGE: {p.get('url','')}]\n{md[:per_page_limit]}")
    total_limit = 60000 if len(pages) == 1 else 40000
    return "\n\n---\n\n".join(chunks)[:total_limit]

# ── AI ────────────────────────────────────────────────────────────────────────
def ask_deepseek(system, user, max_tokens=2000, temperature=0.1):
    resp = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=temperature, max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()


def analyze_company(corpus):
    return ask_deepseek(
        "You are a B2B sales analyst for MIDAS IT (FEA/FEM software). Extract facts only. Respond in pure JSON, no markdown.",
        f"""Return ONLY valid JSON:
{{
  "company_name": "string",
  "tagline": "string or null",
  "locations": ["ONLY cities explicitly stated as offices — empty array if none found"],
  "founded": "year or null",
  "employee_count": "string or null",
  "overview": ["bullet 1", "bullet 2", "bullet 3"],
  "engineering_capabilities": ["bullet 1"],
  "project_types": ["bridge"],
  "software_mentioned": ["any FEA/CAD/BIM tools"],
  "people": [{{"name": "Full Name", "role": "Job Title", "tier": "Owner|Founder|Director|Principal|Senior|Engineer|Graduate|Technician|Other"}}],
  "open_roles": [{{"title": "Job title", "skills": ["skill1"], "fem_mentioned": true}}],
  "projects": [{{"name": "Project name", "type": "Bridge|Building|Metro|Infrastructure|Residential|Industrial|Other", "location": "City or null", "client": "Client name or null", "description": "One sentence summary", "fem_relevant": true}}],
  "confidence": "High|Medium|Low",
  "confidence": "High|Medium|Low",
  "confidence_reason": "One sentence explaining why confidence is High, Medium or Low based on data quality and completeness of the website"
}}
Extract ALL people. For locations: ONLY explicitly stated office cities.
Extract ONLY engineering and technical staff — directors, engineers, technicians, consultants.
EXCLUDE: blog authors, contributing authors, lead authors, writers, journalists, or anyone whose role relates to writing/publishing rather than engineering.
Only include people who work AT the company as engineers or technical staff.
For locations: ONLY explicitly stated office cities.
For projects: extract ALL completed or ongoing projects mentioned anywhere on the site — project pages, case studies, portfolio sections, news. Include project name, type, location if stated, client if stated, and a one sentence description. Set fem_relevant to true if the project involved structural analysis, FEA, FEM, complex geometry, bridges, or heavy civil engineering.
Website content:
{corpus}"""
    )


def analyze_sales(corpus, company_json):
    return ask_deepseek(
        "You are a senior B2B sales strategist for MIDAS IT (MIDAS Civil, Gen, FEA NX). Be specific and actionable. Respond in pure JSON, no markdown.",
        f"""Return ONLY valid JSON:
{{
  "fem_opportunities": ["specific use case 1"],
  "pain_points": ["pain 1"],
  "entry_point": "Who to approach first and why",
  "value_positioning": "How to position MIDAS for this company",
  "likely_objections": ["objection 1"],
  "hiring_signals": ["signal 1"],
  "expansion_signals": ["signal 1"],
  "pre_meeting_mention": ["thing 1", "thing 2", "thing 3"],
  "smart_questions": ["question 1", "question 2", "question 3"],
  "opening_line": "One strong opening line for the first call",
  "overall_score": "Hot|Warm|Cold",
  "score_reason": "1-sentence reason"
}}
Company data: {company_json}
Website excerpt: {corpus[:8000]}"""
    )


def generate_email(company_data, sales_data):
    return ask_deepseek(
        "You are a B2B sales expert writing cold outreach emails for MIDAS IT (FEA/FEM structural analysis software). Write natural, human-sounding emails — not corporate fluff.",
        f"""Write a cold outreach email to a key contact at this engineering company.

Company: {company_data.get('company_name', '')}
Entry point: {sales_data.get('entry_point', '')}
Opening line: {sales_data.get('opening_line', '')}
Value positioning: {sales_data.get('value_positioning', '')}
FEM opportunities: {', '.join(sales_data.get('fem_opportunities', [])[:2])}
Pre-meeting mentions: {', '.join(sales_data.get('pre_meeting_mention', [])[:2])}

Requirements:
- Subject line first (prefix with "Subject: ")
- 4-5 short paragraphs
- Mention something specific about their work
- One clear call to action (15-min call)
- Professional but conversational tone
- No generic opener like "I hope this email finds you well"
- Sign off as the MIDAS IT team

Return plain text only.""",
        max_tokens=800,
        temperature=0.4
    )


# ── HELPERS ───────────────────────────────────────────────────────────────────
def safe_json(text):
    try:
        return json.loads(re.sub(r"```json|```", "", text).strip())
    except:
        return {}

def ini(name):
    return "".join(p[0] for p in name.split()[:2]).upper()

def li_url(name):
    return f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ','%20')}"

def score_cls(s):
    return {"Hot": "score-hot", "Warm": "score-warm", "Cold": "score-cold"}.get(s, "score-cold")

def score_emoji(s):
    return {"Hot": "🔥", "Warm": "⚡", "Cold": "❄️"}.get(s, "")

def extract_domain(url):
    from urllib.parse import urlparse
    return urlparse(url).netloc.replace("www.", "")

def export_pdf(company, cd, sd):
    import io
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib.enums import TA_CENTER

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=20*mm, rightMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)

    INK      = colors.HexColor("#111111")
    ACCENT   = colors.HexColor("#c8471e")
    MUTED    = colors.HexColor("#888888")
    LIGHT_BG = colors.HexColor("#faf9f6")
    BORDER   = colors.HexColor("#e8e4dc")
    WHITE    = colors.white

    def style(name, **kw):
        base = dict(fontName="Helvetica", fontSize=10, textColor=INK, leading=16, spaceAfter=2)
        base.update(kw)
        return ParagraphStyle(name, **base)

    S_TITLE   = style("title",   fontName="Helvetica-Bold", fontSize=22, textColor=INK, spaceAfter=4)
    S_SCORE   = style("score",   fontName="Helvetica-Bold", fontSize=11, textColor=ACCENT)
    S_META    = style("meta",    fontSize=9, textColor=MUTED, spaceAfter=8)
    S_SECTION = style("section", fontName="Helvetica-Bold", fontSize=9, textColor=ACCENT, spaceBefore=14, spaceAfter=6, letterSpacing=1.5)
    S_BODY    = style("body",    fontSize=10, textColor=INK, leading=15, spaceAfter=4)
    S_BULLET  = style("bullet",  fontSize=10, textColor=INK, leading=15, leftIndent=12, spaceAfter=3)
    S_LABEL   = style("label",   fontName="Helvetica-Bold", fontSize=9, textColor=MUTED, spaceAfter=2)
    S_ITALIC  = style("italic",  fontSize=10, textColor=INK, leading=15, italics=True, leftIndent=12)

    story = []

    def section(title):
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph(title.upper(), S_SECTION))
        story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceAfter=4))

    def bullets(items):
        for item in items:
            story.append(Paragraph(f"→  {item}", S_BULLET))

    def label_value(label, value):
        story.append(Paragraph(label.upper(), S_LABEL))
        story.append(Paragraph(value, S_BODY))
        story.append(Spacer(1, 2*mm))

    score     = sd.get("overall_score", "Warm")
    locs      = ", ".join(cd.get("locations", [])) or "—"
    emp       = cd.get("employee_count") or "—"
    conf      = cd.get("confidence", "—")
    generated = datetime.now().strftime("%d %b %Y %H:%M")

    story.append(Paragraph(company, S_TITLE))
    story.append(Paragraph(f"{score.upper()} LEAD", S_SCORE))
    story.append(Paragraph(f"Offices: {locs}  |  Employees: {emp}  |  Confidence: {conf}  |  Generated: {generated}", S_META))
    story.append(Paragraph(sd.get("score_reason", ""), S_BODY))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=6))

    section("Company Overview");          bullets(cd.get("overview", []))
    section("Engineering Capabilities");  bullets(cd.get("engineering_capabilities", []))

    # ── PROJECTS ──
    projects = cd.get("projects", [])
    if projects:
        section("Delivered Projects")
        for proj in projects:
            name        = proj.get("name", "Unknown")
            ptype       = proj.get("type", "")
            location    = proj.get("location", "")
            client      = proj.get("client", "")
            description = proj.get("description", "")
            fem         = proj.get("fem_relevant", False)
    
            meta_parts = []
            if ptype:
                meta_parts.append(ptype)
            if location:
                meta_parts.append(location)
            if client:
                meta_parts.append(f"Client: {client}")
            if fem:
                meta_parts.append("FEM RELEVANT")
            meta_line = "  ·  ".join(meta_parts)
    
            story.append(Paragraph(f"<b>{name}</b>", S_BODY))
            if meta_line:
                story.append(Paragraph(meta_line, S_META))
            if description:
                story.append(Paragraph(description, S_BULLET))
            story.append(Spacer(1, 2*mm))

    pts = cd.get("project_types", [])
    if pts:
        section("Project Types")
        story.append(Paragraph("  ·  ".join(pts), S_BODY))

    sw = cd.get("software_mentioned", [])
    if sw:
        section("Software & Tools Detected")
        story.append(Paragraph("  ·  ".join(sw), S_BODY))
    else:
        section("Software & Tools")
        story.append(Paragraph("No competing software detected — clean FEA opportunity.", S_BODY))

    people = cd.get("people", [])
    if people:
        section("Key People")
        table_data = [["Name", "Role", "Tier"]]
        for p in people:
            table_data.append([p.get("name",""), p.get("role",""), p.get("tier","")])
        t = Table(table_data, colWidths=[55*mm, 80*mm, 30*mm])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#f0ede6")),
            ("TEXTCOLOR",     (0,0),(-1,0),  INK),
            ("FONTNAME",      (0,0),(-1,0),  "Helvetica-Bold"),
            ("FONTSIZE",      (0,0),(-1,0),  8),
            ("FONTSIZE",      (0,1),(-1,-1), 9),
            ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT_BG]),
            ("GRID",          (0,0),(-1,-1), 0.3, BORDER),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 6),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        story.append(t)

    section("FEM / FEA Opportunities");   bullets(sd.get("fem_opportunities", []))
    section("Key Sales Signals")
    for sig in sd.get("hiring_signals", []) + sd.get("expansion_signals", []):
        story.append(Paragraph(f"▲  {sig}", S_BULLET))

    section("Sales Strategy")
    label_value("Entry Point", sd.get("entry_point", "—"))
    label_value("Value Positioning", sd.get("value_positioning", "—"))

    objs = sd.get("likely_objections", [])
    if objs:
        story.append(Paragraph("LIKELY OBJECTIONS", S_LABEL))
        bullets(objs)
        story.append(Spacer(1, 2*mm))

    section("Pre-Meeting Cheat Sheet")
    story.append(Paragraph("3 THINGS TO MENTION", S_LABEL))
    for m in sd.get("pre_meeting_mention", []):
        story.append(Paragraph(f"✓  {m}", S_BULLET))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("3 SMART QUESTIONS TO ASK", S_LABEL))
    for q in sd.get("smart_questions", []):
        story.append(Paragraph(f"?  {q}", S_BULLET))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("OPENING LINE", S_LABEL))
    story.append(Paragraph(sd.get("opening_line", "—"), S_ITALIC))

    roles = cd.get("open_roles", [])
    if roles:
        section("Open Vacancies")
        for role in roles:
            title  = role.get("title", "Unknown")
            skills = ", ".join(role.get("skills", [])) or "—"
            fem    = " · FEM MENTIONED" if role.get("fem_mentioned") else ""
            story.append(Paragraph(f"<b>{title}</b>{fem}", S_BODY))
            story.append(Paragraph(f"Skills: {skills}", S_META))
            story.append(Spacer(1, 1*mm))

    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER))
    story.append(Paragraph(
        f"Generated by MIDAS Sales Intelligence  |  {generated}  |  Confidential",
        style("footer", fontSize=8, textColor=MUTED, alignment=TA_CENTER)
    ))
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


# ── TOP BAR ───────────────────────────────────────────────────────────────────
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
col_logo, col_user = st.columns([6, 1])
with col_logo:
    st.markdown("""
    <div style='display:flex;align-items:center;gap:12px;padding:4px 0 20px;'>
        <div style='font-family:Syne,sans-serif;font-size:20px;font-weight:700;color:#111;letter-spacing:0.05em;'>
            MIDAS <span style='color:#c8471e;'> </span> PRESALES INTEL
        </div>
        <div style='font-family:"JetBrains Mono",monospace;font-size:10px;color:#bbb;letter-spacing:0.1em;
             background:#f0ede6;border:1px solid #e0ddd5;padding:3px 10px;border-radius:20px;'>
            SALES INTELLIGENCE
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_user:
    credits = get_firecrawl_credits()
    credit_display = f"⚡ {credits} credits" if credits is not None else "⚡ —"
    st.markdown(f"""
    <div style='text-align:right;padding-top:4px;'>
        <div style='font-size:12px;color:#888;font-family:"JetBrains Mono",monospace;'>Manoj | MIDAS IT</div>
        <div style='font-size:11px;color:#c8471e;font-family:"JetBrains Mono",monospace;margin-top:2px;'>{credit_display}</div>
    </div>
    """, unsafe_allow_html=True)
    
# ── FIRECRAWL KEY INPUT ───────────────────────────────────────────────────────
if not st.session_state.get("firecrawl_key"):
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">API Configuration</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='background:white;border:1px solid #e8e4dc;border-radius:8px;padding:20px 24px;margin-bottom:16px;'>
        <div style='font-weight:600;font-size:15px;color:#111;margin-bottom:6px;'>Firecrawl API Key Required</div>
        <div style='font-size:13px;color:#888;'>Each team member uses their own key. Get yours free at
            <a href='https://www.firecrawl.dev/app/api-keys' target='_blank'>firecrawl.dev/app/api-keys ↗</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
    fk_col1, fk_col2 = st.columns([5, 1])
    with fk_col1:
        fk_input = st.text_input("", placeholder="Enter your Firecrawl API key (fc-...)", type="password", label_visibility="collapsed")
    with fk_col2:
        if st.button("Save Key →", use_container_width=True):
            if fk_input and fk_input.startswith("fc-"):
                st.session_state["firecrawl_key"] = fk_input
                st.rerun()
            elif fk_input:
                st.error("Key must start with fc-")
            else:
                st.error("Please enter a key")
    st.stop()
else:
    with st.expander("🔑 Firecrawl key active", expanded=False):
        st.caption(f"Key ending in ...{st.session_state['firecrawl_key'][-6:]}")
        if st.button("Clear key / Switch key"):
            del st.session_state["firecrawl_key"]
            st.rerun()

# ── LAYOUT ────────────────────────────────────────────────────────────────────
sidebar, main = st.columns([1, 4])

# ── SIDEBAR: HISTORY ──────────────────────────────────────────────────────────
with sidebar:
    st.markdown('<div class="sec-label">Recent Searches</div>', unsafe_allow_html=True)
    history = load_history()

    search_query = st.text_input("", placeholder="🔍 Search companies...", label_visibility="collapsed")
    if search_query:
        history = [h for h in history if search_query.lower() in h.get("company", "").lower() or search_query.lower() in h.get("domain", "").lower()]

    if not history:
        st.markdown("<div style='font-size:12px;color:#aaa;font-family:JetBrains Mono,monospace;padding:8px 0;'>No searches yet</div>", unsafe_allow_html=True)
    else:
        for i, h in enumerate(history):
            sc    = h.get("score", "Cold")
            name  = h.get("company", h.get("domain", "Unknown"))
            date  = days_ago(h.get("date", ""))
            emoji = score_emoji(sc)
            cls   = score_cls(sc)

            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
                <div style='padding:8px 0;border-bottom:1px solid #f0ede6;'>
                    <div style='font-size:13px;font-weight:600;color:#111;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{name}</div>
                    <div style='display:flex;align-items:center;gap:6px;margin-top:3px;flex-wrap:wrap;'>
                        <span class='score-badge {cls}' style='font-size:9px;padding:2px 8px;'>{emoji} {sc}</span>
                        <span style='font-size:10px;color:#aaa;font-family:JetBrains Mono,monospace;'>{date}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            with col_btn:
                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("↗", key=f"load_{i}", help=f"Load {name}"):
                        st.session_state["loaded_report"] = h
                        st.session_state["active_domain"] = h.get("domain", "")
                        st.rerun()
                with btn2:
                    if st.button("🗑", key=f"del_{i}", help=f"Delete {name}"):
                        st.session_state["confirm_delete"] = h.get("domain", "")

if st.session_state.get("confirm_delete"):
    domain_to_delete = st.session_state["confirm_delete"]
    match = next((h for h in history if h.get("domain") == domain_to_delete), None)
    company_to_delete = match.get("company", domain_to_delete) if match else domain_to_delete
    st.warning(f"⚠ Delete **{company_to_delete}** from history? This cannot be undone.")
    cd1, cd2 = st.columns(2)
    with cd1:
        if st.button("✅ Yes, Delete", use_container_width=True):
            delete_from_history(domain_to_delete)
            if st.session_state.get("active_domain") == domain_to_delete:
                if "loaded_report" in st.session_state:
                    del st.session_state["loaded_report"]
                st.session_state["active_domain"] = ""
            del st.session_state["confirm_delete"]
            st.rerun()
    with cd2:
        if st.button("❌ Cancel", use_container_width=True):
            del st.session_state["confirm_delete"]
            st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:JetBrains Mono,monospace;font-size:9px;color:#ccc;'>Powered by Supabase</div>", unsafe_allow_html=True)

# ── MAIN ──────────────────────────────────────────────────────────────────────
with main:
    run = False
    c1, c2 = st.columns([5, 1])
    with c1:
        default_url = ""
        if "loaded_report" in st.session_state and not run:
            default_url = st.session_state["loaded_report"].get("domain", "")
            if default_url:
                default_url = "https://" + default_url

        website = st.text_input("", value=default_url, placeholder="https://target-engineering-company.com", label_visibility="collapsed")
    with c2:
        run = st.button("Analyse →", use_container_width=True)

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── ALREADY RESEARCHED WARNING ─────────────────────────────────────────────
    if website and not run:
        domain = extract_domain(website if website.startswith("http") else "https://" + website)
        existing = find_in_history(domain)
        if existing:
            sc   = existing.get("score", "Cold")
            date = days_ago(existing.get("date", ""))
            st.markdown(f"""
            <div style='background:#fffbf0;border:1px solid rgba(200,140,0,0.3);border-left:3px solid #c8471e;
                 border-radius:8px;padding:14px 18px;margin-bottom:12px;'>
                <div style='font-family:Syne,sans-serif;font-weight:700;font-size:13px;color:#111;margin-bottom:4px;'>
                    ⚠ Already Researched
                </div>
                <div style='font-size:13px;color:#555;'>
                    <b>{existing.get('company', domain)}</b> was last analysed <b>{date}</b> — scored as <b>{score_emoji(sc)} {sc}</b>.
                </div>
            </div>
            """, unsafe_allow_html=True)
            wb1, wb2 = st.columns([1, 1])
            with wb1:
                if st.button("📂 View Saved Report", use_container_width=True):
                    st.session_state["loaded_report"] = existing
                    st.session_state["active_domain"] = domain
                    st.rerun()
            with wb2:
                if st.button("🔄 Re-crawl Fresh", use_container_width=True):
                    run = True

    st.divider()

    # ── STATE ─────────────────────────────────────────────────────────────────
    show_report   = False
    company_data  = {}
    sales_data    = {}
    pages_count   = 0
    company_name  = ""
    active_domain = st.session_state.get("active_domain", "")

    if "loaded_report" in st.session_state and not run:
        rep          = st.session_state["loaded_report"]
        company_data = rep.get("company_data", {})
        sales_data   = rep.get("sales_data", {})
        pages_count  = rep.get("pages_count", 0)
        company_name = rep.get("company", rep.get("domain", "Unknown"))
        active_domain = rep.get("domain", "")
        st.info(f"📂 Showing saved report from {days_ago(rep.get('date',''))}. Hit Analyse → to refresh.")
        show_report = True

    elif run:
        if not website:
            st.warning("Please enter a website URL.")
            st.stop()
        if not website.startswith("http"):
            website = "https://" + website

        active_domain = extract_domain(website)

        prog = st.progress(0)
        stat = st.empty()

        stat.caption("🔍 Crawling website with Firecrawl...")
        pages = firecrawl_crawl(website)
        if not pages or all(len(p.get("markdown", "")) < 500 for p in pages):
            pages = direct_fetch(website)
        if not pages or all(len(p.get("markdown", "")) < 500 for p in pages):
            st.warning("⚠ This site uses a JavaScript cookie wall that blocks automated crawling.")
            manual_content = st.text_area(
                "Paste the page content manually (copy all text from the website):",
                height=200,
                placeholder="Open the website, select all text (Ctrl+A), copy (Ctrl+C) and paste here..."
            )
            if manual_content:
                pages = [{"url": website, "markdown": manual_content}]
            else:
                st.stop()

        

        prog.progress(30)

        if not pages:
            st.error("Could not extract content. Check the URL and try again.")
            st.stop()

        stat.caption("📄 Building content corpus...")
        corpus = build_corpus(pages)
        prog.progress(50)

        stat.caption("🧠 Extracting company profile...")
        company_raw  = analyze_company(corpus)
        company_data = safe_json(company_raw)
        prog.progress(75)

        stat.caption("💡 Generating sales strategy...")
        sales_raw  = analyze_sales(corpus, company_raw)
        sales_data = safe_json(sales_raw)
        prog.progress(100)

        stat.empty()
        prog.empty()

        company_name = company_data.get("company_name", website)
        pages_count  = len(pages)

        entry = {
            "domain":       active_domain,
            "company":      company_name,
            "score":        sales_data.get("overall_score", "Cold"),
            "date":         datetime.now().strftime("%d %b %Y %H:%M"),
            "pages_count":  pages_count,
            "company_data": company_data,
            "sales_data":   sales_data,
        }
        save_history(entry)
        st.session_state["loaded_report"] = entry
        st.session_state["active_domain"] = active_domain
        show_report = True

    # ── REPORT ────────────────────────────────────────────────────────────────
    if show_report:
        score        = sales_data.get("overall_score", "Warm")
        score_reason = sales_data.get("score_reason", "")
        locs_list    = company_data.get("locations", [])
        locs         = " · ".join(locs_list) if locs_list else "—"
        emp          = company_data.get("employee_count") or "—"
        conf         = company_data.get("confidence", "Medium")
        conf_reason  = company_data.get("confidence_reason", "")

        hc1, hc2 = st.columns([4, 1])
        with hc1:
            st.markdown(f"""
            <div style='margin-bottom:6px;'>
                <span style='font-family:Syne,sans-serif;font-size:26px;font-weight:700;color:#111;'>{company_name}</span>
                &nbsp;&nbsp;
                <span class='score-badge {score_cls(score)}'>{score_emoji(score)} {score} Lead</span>
            </div>
            <div style='font-family:"JetBrains Mono",monospace;font-size:11px;color:#888;margin-bottom:6px;'>📍 {locs}</div>
            <div style='font-family:"JetBrains Mono",monospace;font-size:11px;color:#888;margin-bottom:4px;'>
                👥 {emp} &nbsp;·&nbsp; Confidence: <b style='color:#c8471e;'>{conf}</b>
            </div>
            <div style='font-size:12px;color:#aaa;font-style:italic;margin-bottom:6px;'>{conf_reason}</div>
            <div style='font-size:14px;color:#555;'>{score_reason}</div>
            """, unsafe_allow_html=True)
        with hc2:
            st.markdown(f"<div style='text-align:right;font-family:\"JetBrains Mono\",monospace;font-size:11px;color:#bbb;padding-top:8px;'>{datetime.now().strftime('%d %b %Y %H:%M')}</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("People Identified", len(company_data.get("people", [])))
        m2.metric("Projects Found",    len(company_data.get("projects", [])))
        m3.metric("FEM Opportunities", len(sales_data.get("fem_opportunities", [])))
        m4.metric("Open Roles",        len(company_data.get("open_roles", [])))
        m5.metric("Pages Crawled",     pages_count)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.divider()

        t1, t2, t3, t4, t5, t6, t7, t8 = st.tabs([
            "🏢  Company", "👥  People", "📐  Projects", "💡  FEM Opps",
            "🎯  Strategy", "📋  Vacancies", "📧  Email", "📤  Export & Notes"
        ])

        # TAB 1 ── COMPANY
        with t1:
            ca, cb = st.columns([3, 2])
            with ca:
                st.markdown('<div class="sec-label">Overview</div>', unsafe_allow_html=True)
                for b in company_data.get("overview", ["No data found"]):
                    st.markdown(f'<div class="insight-card">→ {b}</div>', unsafe_allow_html=True)
                st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
                st.markdown('<div class="sec-label">Engineering Capabilities</div>', unsafe_allow_html=True)
                for b in company_data.get("engineering_capabilities", ["Not found"]):
                    st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid #f0ede6;font-size:14px;color:#333;'>◆ {b}</div>", unsafe_allow_html=True)
            with cb:
                st.markdown('<div class="sec-label">Project Types</div>', unsafe_allow_html=True)
                pts = company_data.get("project_types", [])
                if pts:
                    st.markdown(" ".join(f'<span class="pill-tag pill-red">{p}</span>' for p in pts), unsafe_allow_html=True)
                else:
                    st.caption("None detected")
                st.markdown('<div class="sec-label" style="margin-top:16px;">Software & Tools Detected</div>', unsafe_allow_html=True)
                sw = company_data.get("software_mentioned", [])
                if sw:
                    st.markdown(" ".join(f'<span class="pill-tag pill-amber">{s}</span>' for s in sw), unsafe_allow_html=True)
                    st.caption("Existing tools — position MIDAS alongside or against these")
                else:
                    st.success("No competing software detected — clean opportunity to introduce MIDAS as first FEA tool")

        # TAB 2 ── PEOPLE
        with t2:
            people = company_data.get("people", [])
            if people:
                tier_order = ["Owner","Founder","Director","Principal","Senior","Engineer","Graduate","Technician","Other"]
                grouped = {}
                for p in people:
                    grouped.setdefault(p.get("tier","Other"), []).append(p)
                tier_icons = {"Owner":"★","Founder":"★","Director":"◈","Principal":"◈","Senior":"◆","Engineer":"◇","Graduate":"◇","Technician":"◇","Other":"·"}
                for tier in tier_order:
                    tier_ppl = grouped.get(tier, [])
                    if not tier_ppl:
                        continue
                    st.markdown(f'<div class="sec-label">{tier_icons.get(tier,"·")} {tier}s</div>', unsafe_allow_html=True)
                    for p in tier_ppl:
                        name = p.get("name", "")
                        role = p.get("role", "")
                        pc1, pc2, pc3 = st.columns([1, 6, 2])
                        with pc1:
                            st.markdown(f'<div class="av">{ini(name)}</div>', unsafe_allow_html=True)
                        with pc2:
                            st.markdown(f"<div style='font-weight:600;font-size:14px;padding-top:4px;'>{name}</div>", unsafe_allow_html=True)
                            st.markdown(f"<div style='font-size:12px;color:#888;font-family:\"JetBrains Mono\",monospace;'>{role}</div>", unsafe_allow_html=True)
                        with pc3:
                            st.markdown(f"<a href='{li_url(name)}' target='_blank' style='font-family:\"JetBrains Mono\",monospace;font-size:11px;color:#c8471e;text-decoration:none;border:1px solid rgba(200,71,30,0.4);padding:5px 12px;border-radius:4px;white-space:nowrap;'>LinkedIn ↗</a>", unsafe_allow_html=True)
                    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
            else:
                st.info("No people identified. The site may not have a public team page.")


        # TAB 3 ── PROJECTS
        with t3:
            projects = company_data.get("projects", [])
            if projects:
                fem_proj = sum(1 for p in projects if p.get("fem_relevant"))
                if fem_proj:
                    st.success(f"🎯 {fem_proj} project(s) involved FEM/FEA level structural analysis — strong indicator of software need")
        
                st.markdown('<div class="sec-label">Delivered Projects</div>', unsafe_allow_html=True)
        
                for proj in projects:
                    name        = proj.get("name", "Unknown Project")
                    ptype       = proj.get("type", "Other")
                    location    = proj.get("location", "")
                    client      = proj.get("client", "")
                    description = proj.get("description", "")
                    fem         = proj.get("fem_relevant", False)
        
                    fem_html = ""
                    if fem:
                        fem_html = '<span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#c8471e;background:rgba(200,71,30,0.08);border:1px solid rgba(200,71,30,0.3);padding:3px 9px;border-radius:20px;white-space:nowrap;margin-left:8px;">FEM RELEVANT</span>'
        
                    type_colors = {
                        "Bridge":         ("rgba(200,71,30,0.05)",  "rgba(200,71,30,0.4)",  "#c8471e"),
                        "Metro":          ("rgba(0,100,200,0.05)",  "rgba(0,100,200,0.4)",  "#0055cc"),
                        "Building":       ("rgba(0,168,90,0.05)",   "rgba(0,168,90,0.4)",   "#00784a"),
                        "Infrastructure": ("rgba(200,140,0,0.05)",  "rgba(200,140,0,0.4)",  "#8a5e00"),
                        "Residential":    ("rgba(120,80,200,0.05)", "rgba(120,80,200,0.4)", "#6040aa"),
                        "Industrial":     ("rgba(80,80,80,0.05)",   "rgba(80,80,80,0.4)",   "#444444"),
                    }
                    bg, border, color = type_colors.get(ptype, ("rgba(80,80,80,0.05)", "rgba(80,80,80,0.3)", "#555"))
        
                    meta_parts = []
                    if location:
                        meta_parts.append(f"📍 {location}")
                    if client:
                        meta_parts.append(f"👤 {client}")
                    meta_html = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(meta_parts)
        
                    st.markdown(f"""
                    <div style="background:white;border:1px solid #e8e4dc;border-radius:8px;padding:16px 20px;margin-bottom:10px;">
                        <div style="display:flex;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">
                            <div style="font-weight:600;font-size:15px;color:#111;">{name}</div>
                            {fem_html}
                            <span style="font-family:JetBrains Mono,monospace;font-size:10px;padding:3px 10px;
                                 background:{bg};border:1px solid {border};border-radius:20px;color:{color};">
                                {ptype}
                            </span>
                        </div>
                        <div style="font-size:12px;color:#aaa;font-family:JetBrains Mono,monospace;margin-bottom:6px;">{meta_html}</div>
                        <div style="font-size:13px;color:#555;line-height:1.6;">{description}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No projects found. The site may not have a public portfolio or case studies section.")


        # TAB 4 ── FEM OPPS
        with t4:
            fa, fb = st.columns([3, 2])
            with fa:
                st.markdown('<div class="sec-label">FEM / FEA Opportunities</div>', unsafe_allow_html=True)
                for i, opp in enumerate(sales_data.get("fem_opportunities", ["None identified"]), 1):
                    st.markdown(f'<div class="insight-card"><span style=\'font-family:"JetBrains Mono",monospace;font-size:10px;color:#c8471e;\'>0{i}</span><br>{opp}</div>', unsafe_allow_html=True)
            with fb:
                st.markdown('<div class="sec-label">Hiring Signals</div>', unsafe_allow_html=True)
                for s in sales_data.get("hiring_signals", []):
                    st.markdown(f'<div class="signal-card">▲ {s}</div>', unsafe_allow_html=True)
                st.markdown('<div class="sec-label" style="margin-top:16px;">Expansion Signals</div>', unsafe_allow_html=True)
                for s in sales_data.get("expansion_signals", []):
                    st.markdown(f'<div class="signal-card">◆ {s}</div>', unsafe_allow_html=True)

        # TAB 5 ── STRATEGY
        with t5:
            sa, sb = st.columns(2)
            with sa:
                st.markdown('<div class="sec-label">Entry Point</div>', unsafe_allow_html=True)
                st.info(sales_data.get("entry_point", "Not determined"))
                st.markdown('<div class="sec-label" style="margin-top:16px;">Value Positioning</div>', unsafe_allow_html=True)
                st.success(sales_data.get("value_positioning", "Not determined"))
                st.markdown('<div class="sec-label" style="margin-top:16px;">Likely Objections</div>', unsafe_allow_html=True)
                for obj in sales_data.get("likely_objections", []):
                    st.markdown(f'<div class="insight-card" style="border-left-color:#e05c2a;">⚠ {obj}</div>', unsafe_allow_html=True)
            with sb:
                st.markdown('<div class="sec-label">Pre-Meeting Cheat Sheet</div>', unsafe_allow_html=True)
                st.markdown("<div style='font-size:11px;color:#888;font-family:\"JetBrains Mono\",monospace;letter-spacing:0.1em;margin-bottom:8px;'>3 THINGS TO MENTION</div>", unsafe_allow_html=True)
                for m in sales_data.get("pre_meeting_mention", []):
                    st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid #f0ede6;font-size:14px;'>✓ {m}</div>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:11px;color:#888;font-family:\"JetBrains Mono\",monospace;letter-spacing:0.1em;margin:20px 0 8px;'>3 SMART QUESTIONS</div>", unsafe_allow_html=True)
                for q in sales_data.get("smart_questions", []):
                    st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid #f0ede6;font-size:14px;'>? {q}</div>", unsafe_allow_html=True)
                st.markdown('<div class="sec-label" style="margin-top:24px;">Opening Line</div>', unsafe_allow_html=True)
                opening = sales_data.get("opening_line", "")
                if opening:
                    st.markdown(f'''<div style="background:white;border:1px solid #e8e4dc;border-left:3px solid #c8471e;border-radius:8px;padding:24px 28px;font-size:15px;line-height:1.8;font-style:italic;position:relative;">
                        <span style="font-family:Syne,sans-serif;font-size:64px;font-weight:700;color:rgba(200,71,30,0.25);position:absolute;top:-8px;left:14px;line-height:1;">"</span>
                        <span style="color:#333;display:block;padding-left:20px;">{opening}</span>
                    </div>''', unsafe_allow_html=True)

        # TAB 6 ── VACANCIES
        with t6:
            roles = company_data.get("open_roles", [])
            if roles:
                fem_n = sum(1 for r in roles if r.get("fem_mentioned"))
                if fem_n:
                    st.success(f"🎯 {fem_n} role(s) explicitly mention FEM/FEA — strong buying signal")
                st.markdown('<div class="sec-label">Open Roles</div>', unsafe_allow_html=True)
                for role in roles:
                    title     = role.get("title", "Unknown role")
                    skills    = role.get("skills", [])
                    fem       = role.get("fem_mentioned", False)
                    fem_html  = '<span style="font-family:JetBrains Mono,monospace;font-size:10px;color:#c8471e;background:rgba(200,71,30,0.08);border:1px solid rgba(200,71,30,0.3);padding:3px 9px;border-radius:20px;white-space:nowrap;">FEM MENTIONED</span>' if fem else ""
                    pills_html = "".join(f'<span style="font-family:JetBrains Mono,monospace;font-size:10px;padding:3px 10px;border:1px solid #e0ddd5;border-radius:20px;color:#666;background:#faf9f6;margin:2px;display:inline-block;">{s}</span>' for s in skills) if skills else '<span style="font-size:12px;color:#aaa;">No skills listed</span>'
                    st.markdown(
                        f'<div style="background:white;border:1px solid #e8e4dc;border-radius:8px;padding:16px 20px;margin-bottom:10px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
                        f'<div style="font-weight:600;font-size:15px;color:#111;">{title}</div>{fem_html}</div>'
                        f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{pills_html}</div></div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No relevant vacancies found on this website.")

        # TAB 7 ── EMAIL
        with t7:
            st.markdown('<div class="sec-label">Cold Outreach Email</div>', unsafe_allow_html=True)
            st.markdown("<div style='background:white;border:1px solid #e8e4dc;border-radius:8px;padding:16px 20px;margin-bottom:16px;font-size:13px;color:#888;'>Generate a personalised cold email based on the company intelligence. Edit before sending.</div>", unsafe_allow_html=True)

            current_domain = active_domain
            if st.session_state.get("email_domain") != current_domain:
                st.session_state["generated_email"] = ""
                st.session_state["email_domain"] = current_domain

            if st.button("✉ Generate Email Draft"):
                with st.spinner("Writing email..."):
                    st.session_state["generated_email"] = generate_email(company_data, sales_data)

            if st.session_state["generated_email"]:
                lines = st.session_state["generated_email"].strip().split("\n")
                subject = ""
                body_lines = []
                for line in lines:
                    if line.startswith("Subject:"):
                        subject = line.replace("Subject:", "").strip()
                    else:
                        body_lines.append(line)
                body = "\n".join(body_lines).strip()

                if subject:
                    st.markdown("<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#888;margin-bottom:4px;letter-spacing:0.1em;'>SUBJECT LINE</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='background:white;border:1px solid #e8e4dc;border-radius:6px;padding:10px 14px;font-size:14px;font-weight:600;color:#111;margin-bottom:16px;'>{subject}</div>", unsafe_allow_html=True)

                st.markdown("<div style='font-family:JetBrains Mono,monospace;font-size:11px;color:#888;margin-bottom:4px;letter-spacing:0.1em;'>EMAIL BODY — edit below before copying</div>", unsafe_allow_html=True)
                edited_email = st.text_area("", value=body, height=320, label_visibility="collapsed")
                full_copy = f"Subject: {subject}\n\n{edited_email}" if subject else edited_email
                st.download_button("📋 Download as .txt", data=full_copy, file_name=f"MIDAS_Email_{company_name.replace(' ','_')}.txt", mime="text/plain")

        # TAB 8 ── EXPORT & NOTES
        with t8:
            ea, eb = st.columns([1, 1])
            with ea:
                st.markdown('<div class="sec-label">PDF Export</div>', unsafe_allow_html=True)
                st.markdown("<div style='background:white;border:1px solid #e8e4dc;border-radius:8px;padding:20px 24px;margin-bottom:16px;'><div style='font-weight:600;font-size:15px;color:#111;margin-bottom:6px;'>PDF Sales Dossier</div><div style='font-size:13px;color:#888;'>Ready to print or share before a meeting.</div></div>", unsafe_allow_html=True)
                pdf_bytes = export_pdf(company_name, company_data, sales_data)
                fname = f"MIDAS_Intel_{company_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
                st.download_button("📥  Download PDF", data=pdf_bytes, file_name=fname, mime="application/pdf")

            with eb:
                st.markdown('<div class="sec-label">Rep Notes</div>', unsafe_allow_html=True)
                existing_note = get_note(active_domain)
                note_text     = existing_note.get("text", "")
                note_updated  = existing_note.get("updated", "")

                if note_updated:
                    st.caption(f"Last saved: {note_updated}")

                new_note = st.text_area(
                    "",
                    value=note_text,
                    placeholder="Add your notes — call outcome, follow-up date, key contacts spoken to...",
                    height=200,
                    label_visibility="collapsed"
                )
                if st.button("💾 Save Notes", use_container_width=True):
                    save_note(active_domain, new_note)
                    st.success("✓ Saved to Supabase")
