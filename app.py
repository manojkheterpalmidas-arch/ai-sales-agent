import streamlit as st
from openai import OpenAI
import requests
import json
import re
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta

def now_gmt2():
    return datetime.now(timezone.utc) + timedelta(hours=2)


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
            "updated":   now_gmt2().strftime("%d %b %Y %H:%M")
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
        now = now_gmt2().replace(tzinfo=None)
        diff = (now - dt).days
        if diff < 0:
            return "today"
        elif diff == 0:
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
#     html, body, [class*="css"] { background: #ffffff !important; font-family: 'Syne', sans-serif; }
#     .stApp { background: #ffffff !important; }
#     .stTextInput > div > div > input {
#         background: white !important; color: #111 !important;
#         border: 1.5px solid #ddd !important; border-radius: 6px !important;
#         font-family: 'JetBrains Mono', monospace !important;
#         font-size: 22px !important; letter-spacing: 0.4em !important;
#         text-align: center !important; padding: 14px !important;
#         caret-color: #1a1a1a !important;
#     }
#     .stTextInput > div > div > input:focus { border-color: #1a1a1a !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important; }
#     .stButton > button {
#         background: #111 !important; color: white !important;
#         border: none !important; border-radius: 6px !important;
#         font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
#         font-size: 13px !important; letter-spacing: 0.1em !important;
#         text-transform: uppercase !important; padding: 11px 28px !important;
#     }
#     .stButton > button:hover { background: #1a1a1a !important; color: white !important; }
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
#             <div style='font-family:Inter,sans-serif;font-size:11px;letter-spacing:0.3em;color:#1a1a1a;text-transform:uppercase;margin-bottom:6px;'>MIDAS IT</div>
#             <div style='font-family:Inter,sans-serif;font-size:32px;font-weight:700;color:#1a1a1a;'>Sales Intelligence</div>
#             <div style='width:32px;height:3px;background:#1a1a1a;margin:12px auto 0;'></div>
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; background: #ffffff !important; color: #1a1a1a !important; }
.stApp { background: #ffffff !important; }
.stApp, .stApp * { color: #1a1a1a !important; }
.stApp .stButton button,
.stApp .stButton button *,
.stApp div[data-testid="stButton"] button,
.stApp div[data-testid="stButton"] button * { color: white !important; }
.stMarkdown, .stMarkdown * { color: #1a1a1a !important; }
.stTabs [data-baseweb="tab-panel"], .stTabs [data-baseweb="tab-panel"] * { color: #1a1a1a !important; }
.streamlit-expanderContent, .streamlit-expanderContent * { color: #1a1a1a !important; }
[data-testid="column"], [data-testid="column"] * { color: #1a1a1a !important; }
[data-testid="stMetricValue"] { color: #1a1a1a !important; }
[data-testid="stMetricLabel"] { color: #6b7280 !important; }
.stAlert, .stAlert * { color: inherit !important; }
.stCaptionContainer, .stCaptionContainer * { color: #6b7280 !important; }
a { color: #2563eb !important; }
a:hover { color: #1d4ed8 !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1400px !important; }

.stButton > button {
    background: #1a1a1a !important; color: white !important; border: none !important;
    border-radius: 8px !important; font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 13px !important; letter-spacing: 0.02em !important;
    padding: 10px 24px !important; transition: all 0.15s ease !important;
}
.stButton > button:hover { background: #374151 !important; }

.stDownloadButton > button {
    background: transparent !important; color: #1a1a1a !important;
    border: 1px solid #e5e7eb !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important;
    font-size: 12px !important;
}
.stDownloadButton > button:hover { background: #f9fafb !important; border-color: #d1d5db !important; }

.stTextInput > div > div > input {
    background: #ffffff !important; color: #1a1a1a !important;
    border: 1px solid #e5e7eb !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
    padding: 11px 14px !important;
}
.stTextInput > div > div > input:focus { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important; }
.stTextInput > div > div > input::placeholder { color: #9ca3af !important; }

.stTextArea > div > div > textarea {
    background: #ffffff !important; color: #1a1a1a !important;
    border: 1px solid #e5e7eb !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important;
    padding: 11px 14px !important;
}
.stTextArea > div > div > textarea:focus { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important; }

[data-testid="metric-container"] {
    background: #ffffff !important; border: 1px solid #f3f4f6 !important;
    border-radius: 10px !important; padding: 16px 20px !important;
}
[data-testid="stMetricValue"] { font-family: 'Inter', sans-serif !important; font-size: 28px !important; font-weight: 700 !important; color: #1a1a1a !important; }
[data-testid="stMetricLabel"] { font-family: 'Inter', sans-serif !important; font-size: 11px !important; letter-spacing: 0.05em !important; color: #6b7280 !important; text-transform: uppercase !important; }

.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #f3f4f6 !important; gap: 0 !important; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important; font-size: 13px !important; font-weight: 500 !important;
    color: #9ca3af !important;
    padding: 10px 20px !important; background: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -1px !important;
}
.stTabs [aria-selected="true"] { color: #1a1a1a !important; border-bottom-color: #1a1a1a !important; }
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; }

.stProgress > div > div > div { background: #1a1a1a !important; border-radius: 2px !important; }
.stProgress > div > div { background: #f3f4f6 !important; border-radius: 2px !important; }

.streamlit-expanderHeader {
    background: #ffffff !important; border: 1px solid #f3f4f6 !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 13px !important; font-weight: 600 !important;
    color: #374151 !important;
}
.stSuccess, .stInfo, .stWarning, .stError { border-radius: 8px !important; font-family: 'Inter', sans-serif !important; font-size: 14px !important; }
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 2px; }

.sec-label {
    font-family: 'Inter', sans-serif; font-size: 11px; font-weight: 600;
    letter-spacing: 0.08em; text-transform: uppercase; color: #6b7280; margin-bottom: 12px;
    display: flex; align-items: center; gap: 10px;
}
.sec-label::after { content:''; flex:1; height:1px; background:#f3f4f6; }

.insight-card {
    background: #ffffff; border: 1px solid #f3f4f6; border-left: 3px solid #1a1a1a;
    border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
    font-size: 14px; line-height: 1.7; color: #374151;
}
.signal-card {
    background: #ffffff; border: 1px solid #f3f4f6; border-radius: 8px;
    padding: 12px 16px; margin-bottom: 8px; font-size: 13px; line-height: 1.6; color: #374151;
}
.av {
    width: 38px; height: 38px; border-radius: 50%; background: #1a1a1a; color: white;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Inter', sans-serif; font-size: 12px; font-weight: 600; flex-shrink: 0;
}
.pill-tag { display: inline-block; font-family: 'Inter', sans-serif; font-size: 11px; padding: 3px 10px; border: 1px solid #e5e7eb; border-radius: 20px; color: #6b7280; margin: 2px; }
.pill-red   { border-color: #fecaca; color: #dc2626; background: #fef2f2; }
.pill-amber { border-color: #fde68a; color: #d97706; background: #fffbeb; }
.score-hot  { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.score-warm { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.score-cold { background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; }
.score-badge {
    display: inline-block; font-family: 'Inter', sans-serif; font-weight: 600;
    font-size: 12px; letter-spacing: 0.02em; text-transform: uppercase; padding: 6px 16px; border-radius: 20px;
}

.stApp [data-testid="stFormSubmitButton"] button,
.stApp [data-testid="stFormSubmitButton"] button * {
    color: white !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
}
[data-testid="stFormSubmitButton"] button {
    background: #1a1a1a !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 24px !important;
}
[data-testid="stFormSubmitButton"] button:hover {
    background: #374151 !important;
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


def direct_fetch(url, max_subpages=14):
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

        # Find and prioritise subpages
        domain = urlparse(url).netloc
        visited = {url}
        priority_keywords = ["people","team","our-team","staff","leadership","directors","who-we-are",
                             "about","careers","jobs","vacancies","join","projects","services",
                             "what-we-do","contact","expertise","our-expertise","sectors","capabilities"]
        all_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(url, href)
            parsed = urlparse(full)
            if (parsed.netloc == domain and
                "#" not in full and
                full not in visited and
                not any(full.endswith(ext) for ext in [".pdf",".jpg",".png",".zip"])):
                all_links.append(full)
                visited.add(full)

        def priority_score(link):
            lower = link.lower()
            for i, kw in enumerate(priority_keywords):
                if kw in lower:
                    return i
            return 999

        sorted_links = sorted(set(all_links), key=priority_score)

        for link in sorted_links[:max_subpages]:
            try:
                sub = requests.get(link, headers=headers, timeout=10)
                sub_soup = BeautifulSoup(sub.text, "html.parser")
                for tag in sub_soup(["script", "style", "noscript", "iframe"]):
                    tag.decompose()
                sub_text = sub_soup.get_text(separator="\n", strip=True)
                if len(sub_text) > 200:
                    results.append({"url": link, "markdown": sub_text})
            except:
                pass
        return results
    except:
        return []

def fetch_google_cache(url):
    from bs4 import BeautifulSoup
    from urllib.parse import urlparse

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    results = []
    
    # Common team/people page paths to try
    base = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    urls_to_try = [
        url,
        f"{base}/our-team",
        f"{base}/team",
        f"{base}/people",
        f"{base}/about-us",
        f"{base}/about",
    ]

    for target_url in urls_to_try:
        try:
            cache_url = f"https://webcache.googleusercontent.com/search?q=cache:{target_url}&hl=en"
            resp = requests.get(cache_url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "noscript", "iframe"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            if len(text) > 500:
                results.append({"url": target_url, "markdown": text})
        except:
            continue

    return results if results else []


def scrape_with_scrapingbee(url):
    try:
        try:
            api_key = st.secrets["SCRAPINGBEE_KEY"]
        except:
            return []

        if not api_key:
            return []

        from bs4 import BeautifulSoup
        from urllib.parse import urljoin, urlparse

        headers_sb = {
            "api_key": api_key,
            "render_js": "true",
            "wait": "2000",
        }

        results = []
        visited = set()

        def sb_scrape(target_url):
            if target_url in visited:
                return None
            visited.add(target_url)
            try:
                resp = requests.get(
                    "https://app.scrapingbee.com/api/v1/",
                    params={**headers_sb, "url": target_url},
                    timeout=30
                )
                soup = BeautifulSoup(resp.text, "html.parser")
                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()
                text = soup.get_text(separator="\n", strip=True)
                if len(text) > 500:
                    return {"url": target_url, "markdown": text}, soup
            except:
                pass
            return None, None

        # Scrape homepage
        home_result, home_soup = sb_scrape(url)
        if not home_result:
            return []
        results.append(home_result)

        # Find and scrape priority subpages
        if home_soup:
            domain = urlparse(url).netloc
            priority_keywords = ["team","people","about","projects","services","careers","who-we-are","our-work"]
            links = []
            for a in home_soup.find_all("a", href=True):
                href = a["href"].strip()
                full = urljoin(url, href)
                parsed = urlparse(full)
                if (parsed.netloc == domain and
                    "#" not in full and
                    full != url and
                    full not in visited and
                    not any(full.endswith(ext) for ext in [".pdf",".jpg",".png",".zip"])):
                    links.append(full)

            # Sort by priority
            def priority_score(link):
                lower = link.lower()
                for i, kw in enumerate(priority_keywords):
                    if kw in lower:
                        return i
                return 999

            sorted_links = sorted(set(links), key=priority_score)

            # Scrape up to 5 priority subpages
            for link in sorted_links[:5]:
                result, _ = sb_scrape(link)
                if result:
                    results.append(result)

        return results

    except:
        return []


def search_people_via_google(company_name, domain):
    try:
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        all_text = ""

        # Search 1 — Site specific DuckDuckGo
        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q=site:{domain}+team+OR+engineers+OR+directors+OR+people+OR+staff+OR+bridge+OR+structural+OR+geotechnical+OR+principal+OR+associate+OR+consultant+OR+civil+OR+BIM+OR+FEA"
            resp = requests.get(ddg_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("a", class_="result__snippet")
            text = "\n".join([r.get_text() for r in results])
            if len(text) < 200:
                text = soup.get_text(separator="\n", strip=True)
            all_text += text
        except:
            pass

        # Search 2 — Site specific Google
        try:
            google_url = f"https://www.google.com/search?q=site:{domain}+team+OR+engineers+OR+directors+OR+people+OR+staff+OR+bridge+OR+structural+OR+geotechnical+OR+principal+OR+associate+OR+consultant+OR+civil+OR+BIM+OR+FEA"
            resp = requests.get(google_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            all_text += "\n\n" + text
        except:
            pass

        # Search 3 — LinkedIn via Google
        try:
            li_url = f"https://www.google.com/search?q=site:linkedin.com/in+\"{company_name}\"+engineer+OR+director+OR+structural+OR+bridge+OR+geotechnical+OR+principal+OR+associate+OR+consultant+OR+civil+OR+architect+OR+BIM+OR+FEA+OR+FEM"
            resp = requests.get(li_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            all_text += "\n\n" + text
        except:
            pass

        # Search 4 — LinkedIn via DuckDuckGo
        try:
            li_ddg = f"https://html.duckduckgo.com/html/?q=site:linkedin.com/in+\"{company_name}\"+engineer+OR+director+OR+structural+OR+bridge+OR+geotechnical+OR+principal+OR+associate+OR+consultant+OR+civil+OR+BIM+OR+FEA"
            resp = requests.get(li_ddg, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("a", class_="result__snippet")
            text = "\n".join([r.get_text() for r in results])
            all_text += "\n\n" + text
        except:
            pass

        # Search 5 — LinkedIn senior roles via Google
        try:
            li_url2 = f"https://www.google.com/search?q=site:linkedin.com/in+\"{company_name}\"+senior+OR+graduate+OR+technician+OR+founder+OR+owner+OR+manager+OR+director+OR+head+OR+lead+OR+chartered+OR+CEng+OR+MIStructE"
            resp = requests.get(li_url2, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            all_text += "\n\n" + text
        except:
            pass

        return all_text[:8000]
    except:
        return ""

def lookup_companies_house(company_name, locations=None):
    try:
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        # Detect country from locations
        uk_keywords = [
                    "london", "manchester", "birmingham", "leeds", "bristol", "edinburgh",
                    "glasgow", "liverpool", "sheffield", "cardiff", "belfast", "nottingham",
                    "uk", "england", "scotland", "wales", "northern ireland", "united kingdom", "britain"
                ]
        
        eu_keywords = [
                    # Western Europe
                    "germany", "berlin", "munich", "hamburg", "frankfurt", "cologne", "düsseldorf",
                    "france", "paris", "lyon", "marseille", "toulouse", "bordeaux",
                    "netherlands", "amsterdam", "rotterdam", "the hague", "eindhoven",
                    "belgium", "brussels", "antwerp", "ghent", "bruges",
                    "luxembourg",
                    "switzerland", "zurich", "geneva", "basel", "bern",
                    "austria", "vienna", "graz", "salzburg", "innsbruck",
                    "ireland", "dublin", "cork", "galway",
                    # Southern Europe
                    "spain", "madrid", "barcelona", "seville", "valencia", "bilbao",
                    "portugal", "lisbon", "porto",
                    "italy", "rome", "milan", "naples", "turin", "florence", "bologna",
                    "greece", "athens", "thessaloniki",
                    "malta", "valletta",
                    "cyprus", "nicosia",
                    # Northern Europe
                    "sweden", "stockholm", "gothenburg", "malmö",
                    "norway", "oslo", "bergen", "trondheim",
                    "denmark", "copenhagen", "aarhus",
                    "finland", "helsinki", "tampere", "espoo",
                    "iceland", "reykjavik",
                    # Eastern Europe
                    "poland", "warsaw", "krakow", "wroclaw", "gdansk", "poznan",
                    "czech", "prague", "brno", "ostrava",
                    "slovakia", "bratislava", "kosice",
                    "hungary", "budapest", "debrecen",
                    "romania", "bucharest", "cluj", "timisoara", "iasi",
                    "bulgaria", "sofia", "plovdiv", "varna",
                    "croatia", "zagreb", "split", "rijeka",
                    "slovenia", "ljubljana", "maribor",
                    "serbia", "belgrade", "novi sad",
                    "bosnia", "sarajevo", "banja luka",
                    "montenegro", "podgorica",
                    "north macedonia", "skopje",
                    "albania", "tirana",
                    "kosovo", "pristina",
                    # Baltic States
                    "estonia", "tallinn", "tartu",
                    "latvia", "riga", "daugavpils",
                    "lithuania", "vilnius", "kaunas",
                    # Other
                    "moldova", "chisinau",
                    "ukraine", "kyiv", "kharkiv", "lviv", "odessa",
                    "belarus", "minsk",
                    "turkey", "istanbul", "ankara", "izmir",
                    "georgia", "tbilisi",
                    "armenia", "yerevan",
                    "azerbaijan", "baku",
                    "israel", "tel aviv", "jerusalem",
                    "morocco", "casablanca", "rabat",
                    "tunisia", "tunis",
                    "egypt", "cairo", "alexandria",
                ]

        location_str = " ".join(locations or []).lower()
        is_uk = any(kw in location_str for kw in uk_keywords)
        is_eu = any(kw in location_str for kw in eu_keywords)

        all_text = ""
        director_count = 0

        # ── UK — Companies House API ──────────────────────────────────────
        if is_uk or (not is_uk and not is_eu):
            try:
                # Search via Companies House API
                search_resp = requests.get(
                    f"https://api.company-information.service.gov.uk/search/companies?q={company_name.replace(' ', '+')}",
                    auth=(st.secrets.get("COMPANIES_HOUSE_KEY", ""), ""),
                    timeout=10
                )
                results = search_resp.json().get("items", [])
                if results:
                    company_number = results[0].get("company_number", "")
                    # Get officers
                    officers_resp = requests.get(
                        f"https://api.company-information.service.gov.uk/company/{company_number}/officers",
                        auth=(st.secrets.get("COMPANIES_HOUSE_KEY", ""), ""),
                        timeout=10
                    )
                    officers = officers_resp.json().get("items", [])
                    officer_text = "\n".join([
                        f"{o.get('name', '')} — {o.get('officer_role', '')} (appointed {o.get('appointed_on', '')})"
                        for o in officers if o.get('resigned_on') is None
                    ])
                    company_info = results[0]
                    text = f"""Company: {company_info.get('title', '')}
Status: {company_info.get('company_status', '')}
Type: {company_info.get('company_type', '')}
Incorporated: {company_info.get('date_of_creation', '')}
Address: {company_info.get('registered_office_address', {}).get('address_line_1', '')}

Active Officers:
{officer_text}"""
                    director_count = len([o for o in officers if 'director' in o.get('officer_role','').lower()])
                    all_text += f"[Companies House UK]\n{text}"
            except:
                pass

        # ── EU — OpenCorporates ───────────────────────────────────────────
        if is_eu or (not is_uk and not is_eu):
            try:
                oc_url = f"https://opencorporates.com/companies?q={company_name.replace(' ', '+')}&utf8=✓"
                resp = requests.get(oc_url, headers=headers, timeout=10)
                soup = BeautifulSoup(resp.text, "html.parser")
                result = soup.find("a", class_="company_search_result")
                if result:
                    company_url = "https://opencorporates.com" + result["href"]
                    resp2 = requests.get(company_url, headers=headers, timeout=10)
                    soup2 = BeautifulSoup(resp2.text, "html.parser")
                    text = soup2.get_text(separator="\n", strip=True)
                    director_count += text.lower().count("director")
                    all_text += f"\n\n[OpenCorporates EU]\n{text[:3000]}"
            except:
                pass

        # ── EU Tenders — TED Europa ───────────────────────────────────────
        try:
            ted_url = f"https://ted.europa.eu/en/search?scope=NOTICE&query={company_name.replace(' ', '+')}&sortColumn=ND&sortOrder=DESC"
            resp = requests.get(ted_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            if len(text) > 200:
                all_text += f"\n\n[EU Tenders TED]\n{text[:2000]}"
        except:
            pass

        return all_text[:6000], director_count

    except:
        return "", 0



def lookup_linkedin_company(company_name):
    try:
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        # Search LinkedIn company via Google
        query = f'site:linkedin.com/company "{company_name}" engineers employees'
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        # Also try DuckDuckGo
        ddg_url = f"https://html.duckduckgo.com/html/?q=site:linkedin.com/company+\"{company_name}\""
        resp2 = requests.get(ddg_url, headers=headers, timeout=10)
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        results = soup2.find_all("a", class_="result__snippet")
        text += "\n" + "\n".join([r.get_text() for r in results])

        # Extract employee count signal
        employee_signal = 0
        import re
        matches = re.findall(r'(\d+[\,\d]*)\s*employees', text.lower())
        if matches:
            employee_signal = matches[0].replace(",", "")

        return text[:3000], employee_signal
    except:
        return "", 0


def lookup_glassdoor(company_name, domain):
    try:
        import time as _time
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        all_text = ""
        review_count = 0
        base_name = domain.replace("www.", "").split(".")[0]

        try:
            google_url = f"https://www.google.com/search?q=glassdoor+\"{company_name}\"+reviews+engineers+software+tools+employees"
            resp = requests.get(google_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            all_text += text
            review_count += text.lower().count("glassdoor")
        except:
            pass

        _time.sleep(0.5)

        try:
            ddg_url = f"https://html.duckduckgo.com/html/?q=glassdoor+{base_name}+engineers+reviews+software"
            resp = requests.get(ddg_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("a", class_="result__snippet")
            text = "\n".join([r.get_text() for r in results])
            all_text += "\n\n" + text
            review_count += len(results)
        except:
            pass

        _time.sleep(0.5)

        try:
            search_url = f"https://www.google.com/search?q=glassdoor.co.uk+{company_name}+reviews+employee+size+software"
            resp = requests.get(search_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            all_text += "\n\n" + text
        except:
            pass

        _time.sleep(0.5)

        try:
            indeed_url = f"https://html.duckduckgo.com/html/?q=indeed.com+\"{company_name}\"+reviews+engineer+software+tools"
            resp = requests.get(indeed_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            results = soup.find_all("a", class_="result__snippet")
            text = "\n".join([r.get_text() for r in results])
            all_text += "\n\n" + text
            review_count += len(results)
        except:
            pass

        _time.sleep(0.5)

        try:
            size_url = f"https://www.google.com/search?q=\"{company_name}\"+employees+size+headquarters+glassdoor+OR+linkedin+OR+indeed"
            resp = requests.get(size_url, headers=headers, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            all_text += "\n\n" + text
        except:
            pass

        return all_text[:5000], review_count
    except:
        return "", 0


def lookup_planning_portal(company_name):
    try:
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        # Search planning applications via Google
        query = f'"{company_name}" planning application structural engineer site:gov.uk OR site:planningportal.co.uk OR site:localplanning'
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        resp = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        # Also DuckDuckGo
        ddg_url = f"https://html.duckduckgo.com/html/?q=\"{company_name}\"+planning+application+structural"
        resp2 = requests.get(ddg_url, headers=headers, timeout=10)
        soup2 = BeautifulSoup(resp2.text, "html.parser")
        results = soup2.find_all("a", class_="result__snippet")
        text += "\n" + "\n".join([r.get_text() for r in results])

        project_count = text.lower().count("planning")

        return text[:3000], project_count
    except:
        return "", 0

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
                    for _ in range(40):
                        time.sleep(3)
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
    chunks = []
    for p in pages:
        md = p.get("markdown", "").strip()
        if not md:
            continue
        # Strip image tags to reduce noise
        md = _re.sub(r'!\[.*?\]\(.*?\)', '', md)
        md = _re.sub(r'\n{3,}', '\n\n', md)
        chunks.append(f"[PAGE: {p.get('url','')}]\n{md[:15000]}")
    return "\n\n---\n\n".join(chunks)[:40000]

# ── AI ────────────────────────────────────────────────────────────────────────
def ask_deepseek(system, user, max_tokens=2000, temperature=0.1, api_key=None):
    try:
        key = api_key or st.secrets["DEEPSEEK_API_KEY"]
        client = OpenAI(api_key=key, base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature, max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        st.error(f"DeepSeek API error: {str(e)}")
        return "{}"


def analyze_company(corpus):
    return ask_deepseek(
        "You are a B2B sales analyst for MIDAS IT (FEA/FEM software). Extract facts only. Respond in pure JSON, no markdown. CRITICAL: Translate ALL descriptive content (overviews, capabilities, project types, roles, descriptions) into English. However, NEVER translate or modify people's names — keep all person names exactly as written on the website, including Cyrillic, accented, or special characters. Do not transliterate names.",
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
For employee_count: check ALL sources including Glassdoor, LinkedIn, Companies House and the website. Glassdoor often shows ranges like "51-200 employees" — use this if the website doesn't state it explicitly.
For projects: extract ALL completed or ongoing projects mentioned anywhere on the site — project pages, case studies, portfolio sections, news. Include project name, type, location if stated, client if stated, and a one sentence description. Set fem_relevant to true if the project involved structural analysis, FEA, FEM, complex geometry, bridges, or heavy civil engineering.
Website content:
{corpus}""",
        max_tokens=8000        
    )


MIDAS_PRODUCTS = """
MIDAS NX PRODUCT SUITE — FULL SALES KNOWLEDGE BASE

════════════════════════════════════════════════
1. MIDAS CIVIL NX — Bridges & Civil Infrastructure
════════════════════════════════════════════════
WHAT IT IS: Next-generation structural analysis and design software specialised for bridges and civil infrastructure. Combines advanced FEA, automation, and integrated design workflows.

WHAT IT DOES:
- Structural modelling and analysis (static, dynamic, seismic, nonlinear, time-history)
- Construction stage simulation — analyse structures at every phase of build
- Moving load and traffic simulation — vehicles across bridges, stress/deflection/safety
- Design and code checking — international standards, automated compliance verification
- Automation and parametric workflows — Excel-based model generation, API, batch processing
- BIM interoperability and integration with other MIDAS tools

KEY CAPABILITIES:
- Linear and nonlinear analysis including large displacement and material nonlinearity
- Seismic and pushover analysis
- Pre-built templates for bridges, culverts, and infrastructure
- Auto-meshing, fast post-processing, detailed reporting
- Moving loads, construction loads, environmental loads (temperature, seismic)
- Excel integration and API/plugin ecosystem

TYPICAL USE CASES:
- Cable-stayed, suspension, PSC, and steel bridge design and validation
- Highway and railway bridges with traffic load simulation
- Construction stage analysis for segmental construction and temporary supports
- Earthquake response studies and time-dependent behaviour
- Water treatment facilities and underground/industrial structures
- Parametric design optimisation and bulk scenario analysis

VALUE PROPOSITION: High accuracy FEA + automation + specialised bridge focus = complete bridge design lifecycle in one platform.
POSITIONING: Best global analysis tool for bridge and infrastructure firms.

════════════════════════════════════════════════
2. MIDAS GEN NX — Buildings & General Structures
════════════════════════════════════════════════
WHAT IT IS: Next-generation structural analysis and design platform for buildings and general structures. Integrates modelling, analysis, design, and automation in one environment.

WHAT IT DOES:
- Models RC, steel, and composite structures
- Static, dynamic, seismic, and nonlinear analysis
- Building design and code compliance — international design codes, automated steel and RC design
- Integrated workflow: Modelling → Analysis → Design in one platform
- Automation via Excel, Grasshopper, and API for custom workflows
- AI-assisted workflow with built-in guidance and smart tools

KEY CAPABILITIES:
- 4K-ready modern UI with customisable toolbars
- Advanced FEA with fast solver
- Automated design optimisation for cost and material efficiency
- Pushover analysis and nonlinear time-history for seismic design
- Excel-driven parametric workflows and Grasshopper integration
- Auto-generated reports and calculations

TYPICAL USE CASES:
- High-rise, residential, and commercial building design
- Steel, RC, and composite structure engineering
- Earthquake-resistant seismic design
- Batch processing and parametric design optimisation
- Industrial structures — factories and plants

VALUE PROPOSITION: Efficiency through automation + accuracy through advanced analysis + modern usability = integrated building design workflow.
POSITIONING: Best global design tool for building and general structure firms.

════════════════════════════════════════════════
3. MIDAS FEA NX — Detailed Local & Nonlinear Analysis
════════════════════════════════════════════════
WHAT IT IS: High-end finite element analysis software designed for detailed, local, and nonlinear analysis of civil and structural systems. Used when global tools are not sufficient.

WHAT IT DOES:
- 2D and 3D element modelling (plates, solids) for complex geometry
- Advanced linear and nonlinear analysis — material nonlinearity, cracking, yielding, large deformation
- CAD-based modelling with import from AutoCAD, SolidWorks, STEP, IGES
- Automatic, mapped, and hybrid mesh generation
- Multi-physics analysis — structural, geotechnical, crack, fatigue, buckling, thermal
- Integrates with CIVIL NX and GEN NX for global-to-local workflows

KEY CAPABILITIES:
- Crack modelling, contact and interface behaviour, plasticity and failure simulation
- High-quality meshing for accurate geometry representation
- 3D solid and plate modelling for detailed joints, anchors, and connections
- Stress contours, crack visualisation, deformation plots
- Parallel computing for large models
- Modern UI for faster preprocessing and postprocessing

TYPICAL USE CASES:
- Steel connections, anchor zones, bridge joints
- Deep beams, shear walls, slabs
- Bridge local analysis — anchorage zones, bearings
- Geotechnical analysis — foundations, soil-structure interaction details
- Failure analysis — concrete cracking, fatigue
- Nonlinear problems — large deformation, contact problems

VALUE PROPOSITION: High accuracy for complex local analysis that global tools cannot handle. Seamless integration with CIVIL NX and GEN NX.
POSITIONING: Detailed local analysis tool — always pairs with CIVIL NX or GEN NX.

════════════════════════════════════════════════
4. MIDAS GTS NX — Geotechnical Analysis
════════════════════════════════════════════════
WHAT IT IS: Geotechnical analysis software for soil, rock, and underground engineering problems. Focuses on ground behaviour, soil-structure interaction, and construction processes.

WHAT IT DOES:
- 2D and 3D FEA of soil and rock behaviour — deformation, stress, stability
- Soil-structure interaction — foundations, retaining walls, tunnels
- Excavation and construction stage analysis — staged construction, deep excavation, tunnelling
- Groundwater and seepage analysis — water flow through soil, hydrostatic pressure
- Dynamic and seismic analysis — earthquake response, vibration
- CAD-based 2D/3D modelling with CAD import

KEY CAPABILITIES:
- Advanced material models — elastic and nonlinear soil behaviour
- High-quality automatic and hybrid mesh generation for geotechnical problems
- 3D terrain modelling from borehole data with layered soil modelling
- Static, nonlinear, dynamic, construction stage, and slope stability analysis
- Contours, deformation, vectors — full ground behaviour visualisation
- Automated result reports with Excel export

TYPICAL USE CASES:
- Foundation engineering — shallow and deep foundations, pile analysis
- Metro tunnels and underground caverns
- Deep excavation projects and retaining structures
- Slope stability — landslides and open pit mining
- Dam engineering and seepage analysis
- Soil-structure interaction for buildings and bridges

VALUE PROPOSITION: Accurate soil and rock modelling + advanced geotechnical capabilities + full ground engineering coverage.
POSITIONING: Essential for any firm doing geotechnical, tunnelling, underground, or foundation work.

════════════════════════════════════════════════
CROSS-SELL LOGIC — MATCH TO COMPANY TYPE
════════════════════════════════════════════════
- Bridge/infrastructure firm → CIVIL NX (primary) + FEA NX (local detailing)
- Building/structural firm → GEN NX (primary) + FEA NX (connection design)
- Geotechnical/ground firm → GTS NX (primary) + CIVIL NX (structure interaction)
- Mixed civil firm (bridges + buildings) → CIVIL NX + GEN NX + FEA NX
- Full service firm (all disciplines) → Full suite: CIVIL NX + GEN NX + FEA NX + GTS NX
- Metro/tunnelling firm → GTS NX + CIVIL NX
- Consulting/advisory firm → Start with CIVIL NX or GEN NX depending on focus

════════════════════════════════════════════════
COMPETITIVE POSITIONING
════════════════════════════════════════════════
- vs LUSAS/STAAD/SAP2000 → MIDAS offers better automation, modern UI, and construction stage analysis
- vs PLAXIS → GTS NX is directly competitive, with better BIM integration and CAD workflow
- vs ETABS → GEN NX offers more automation and parametric design capabilities
- vs ANSYS/ABAQUS → FEA NX is more accessible for civil engineers with civil-specific workflows
- No existing FEA software detected → Clean opportunity, position as first professional FEA platform

════════════════════════════════════════════════
ONE-LINE MASTER PITCH
════════════════════════════════════════════════
MIDAS NX Suite provides a complete structural and geotechnical engineering ecosystem — from global bridge and building design to detailed local analysis and ground engineering — all within one integrated, automated workflow.
"""


def analyze_sales(corpus, company_json):
    return ask_deepseek(
        f"You are a senior B2B sales strategist for MIDAS IT. Use the product knowledge below to make specific product recommendations. Be specific and actionable. Respond in pure JSON, no markdown. Always respond in English regardless of the language of the website content.\n\n{MIDAS_PRODUCTS}",
        f"""Return ONLY valid JSON:
{{
  "fem_opportunities": ["detailed specific use case 1 referencing their actual project types", "use case 2", "use case 3"],
  "pain_points": ["specific pain point based on their work", "pain 2", "pain 3"],
  "entry_point": "Specific person name and role to approach first, with detailed reasoning based on their seniority and relevance to FEA/FEM",
  "value_positioning": "Detailed 2-3 sentence positioning of MIDAS specifically for this company's project types and engineering focus",
  "likely_objections": ["specific objection based on their context", "objection 2", "objection 3"],
  "hiring_signals": ["specific signal from their job postings or growth", "signal 2"],
  "expansion_signals": ["specific expansion signal", "signal 2"],
  "pre_meeting_mention": ["specific thing to mention about their actual projects", "thing 2", "thing 3"],
  "smart_questions": ["specific question about their workflow or current tools", "question 2", "question 3"],
  "opening_line": "One strong personalised opening line referencing something specific about their work",
  "overall_score": "Hot|Warm|Cold",
  "score_reason": "2-3 sentence detailed reason for the score based on their specific context",
  "recommended_products": ["list the specific MIDAS products that fit this company from: CIVIL NX, GEN NX, FEA NX, GTS NX"],
  "product_reason": "3-4 sentence explanation of exactly why these specific MIDAS products fit this company based on their project types and engineering capabilities"
}}
Company data: {company_json}
Website excerpt: {corpus[:4000]}""",
        max_tokens=4000
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
        cleaned = re.sub(r"```json|```", "", text).strip()
        return json.loads(cleaned)
    except:
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
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

    INK      = colors.HexColor("#1a1a1a")
    ACCENT   = colors.HexColor("#1a1a1a")
    MUTED    = colors.HexColor("#6b7280")
    LIGHT_BG = colors.HexColor("#f9fafb")
    BORDER   = colors.HexColor("#e5e7eb")
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
    generated = now_gmt2().strftime("%d %b %Y %H:%M")

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
            ("BACKGROUND",    (0,0),(-1,0),  colors.HexColor("#f3f4f6")),
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
        <div style='font-family:Inter,sans-serif;font-size:20px;font-weight:700;color:#1a1a1a;letter-spacing:0.05em;'>
            MIDAS <span style='color:#1a1a1a;'> </span> PRESALES INTEL
        </div>
        <div style='font-family:"Inter",sans-serif;font-size:10px;color:#9ca3af;letter-spacing:0.1em;
             background:#f9fafb;border:1px solid #e5e7eb;padding:3px 10px;border-radius:20px;'>
            SALES INTELLIGENCE
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_user:
    credits = get_firecrawl_credits()
    credit_display = f"⚡ {credits} credits" if credits is not None else "⚡ —"
    st.markdown(f"""
    <div style='text-align:right;padding-top:4px;'>
        <div style='font-size:12px;color:#6b7280;font-family:"Inter",sans-serif;'>Manoj | MIDAS IT</div>
        <div style='font-size:11px;color:#1a1a1a;font-family:"Inter",sans-serif;margin-top:2px;'>{credit_display}</div>
    </div>
    """, unsafe_allow_html=True)
    
# ── FIRECRAWL KEY INPUT ───────────────────────────────────────────────────────
if not st.session_state.get("firecrawl_key"):
    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="sec-label">API Configuration</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style='background:white;border:1px solid #f3f4f6;border-radius:8px;padding:20px 24px;margin-bottom:16px;'>
        <div style='font-weight:600;font-size:15px;color:#1a1a1a;margin-bottom:6px;'>Firecrawl API Key Required</div>
        <div style='font-size:13px;color:#6b7280;'>Each team member uses their own key. Get yours free at
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
        st.markdown("<div style='font-size:12px;color:#9ca3af;font-family:Inter,sans-serif;padding:8px 0;'>No searches yet</div>", unsafe_allow_html=True)
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
                <div style='padding:8px 0;border-bottom:1px solid #f3f4f6;'>
                    <div style='font-size:13px;font-weight:600;color:#1a1a1a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{name}</div>
                    <div style='display:flex;align-items:center;gap:6px;margin-top:3px;flex-wrap:wrap;'>
                        <span class='score-badge {cls}' style='font-size:9px;padding:2px 8px;'>{emoji} {sc}</span>
                        <span style='font-size:10px;color:#9ca3af;font-family:Inter,sans-serif;'>{date}</span>
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
    st.markdown("<div style='font-family:Inter,sans-serif;font-size:9px;color:#ccc;'>Powered by Supabase</div>", unsafe_allow_html=True)

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
            <div style='background:#fffbeb;border:1px solid #fde68a;border-left:3px solid #1a1a1a;
                 border-radius:8px;padding:14px 18px;margin-bottom:12px;'>
                <div style='font-family:Inter,sans-serif;font-weight:700;font-size:13px;color:#1a1a1a;margin-bottom:4px;'>
                    ⚠ Already Researched
                </div>
                <div style='font-size:13px;color:#4b5563;'>
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
        
        # Use cached pages if previously fetched via Google Cache button
        if st.session_state.get("use_cache") and st.session_state.get("cache_pages"):
            pages = st.session_state["cache_pages"]
            st.session_state["use_cache"] = False
            st.session_state["cache_pages"] = None
            st.success("✅ Using Google Cache content")
        else:
            pages = firecrawl_crawl(website)
        
        # ── SMART FALLBACK: detect thin/failed crawls ────────────────────
        # Check if Firecrawl returned usable content or just cookie wall junk
        def is_thin_crawl(page_list):
            """Returns True if the crawl result is too thin to be useful."""
            if not page_list:
                return True
            # All pages under 500 chars = clearly failed
            if all(len(p.get("markdown", "")) < 500 for p in page_list):
                return True
            # Any real company site should yield 3+ pages with real content
            # If we got fewer, the crawl was likely blocked or hit a cookie wall
            real_pages = [p for p in page_list if len(p.get("markdown", "")) > 500]
            if len(real_pages) < 3:
                return True
            return False

        needs_fallback = is_thin_crawl(pages)

        if needs_fallback:
            st.warning("⚠ Limited content retrieved — site may use a cookie wall or block automated crawling. Trying alternative methods...")

            # Step 1 — Try ScrapingBee (real headless browser, best at cookie walls)
            stat.caption("🌐 Trying ScrapingBee browser renderer...")
            sb_pages = scrape_with_scrapingbee(website)
            if sb_pages and any(len(p.get("markdown", "")) > 500 for p in sb_pages):
                st.success(f"✅ ScrapingBee retrieved {len(sb_pages)} pages")
                pages = sb_pages
                needs_fallback = False

            # Step 2 — Try direct fetch with subpage discovery
            if needs_fallback:
                stat.caption("🔄 Trying direct fetch with link discovery...")
                direct_pages = direct_fetch(website)
                if direct_pages and any(len(p.get("markdown", "")) > 500 for p in direct_pages):
                    st.success(f"✅ Direct fetch retrieved {len(direct_pages)} pages")
                    pages = direct_pages
                    needs_fallback = False

            # Step 3 — Try Google Cache
            if needs_fallback:
                stat.caption("🔄 Trying Google Cache...")
                cache_pages = fetch_google_cache(website)
                if cache_pages and any(len(p.get("markdown","")) > 500 for p in cache_pages):
                    st.success(f"✅ Google Cache retrieved {len(cache_pages)} pages")
                    pages = cache_pages
                    needs_fallback = False

            # Step 4 — If we got SOME content from Firecrawl + SOME from fallbacks, merge
            if needs_fallback and pages and any(len(p.get("markdown", "")) > 300 for p in pages):
                # We have thin but non-zero Firecrawl content — try to supplement it
                stat.caption("🔄 Supplementing with direct subpage fetch...")
                from urllib.parse import urlparse
                base = f"{urlparse(website).scheme}://{urlparse(website).netloc}"
                priority_paths = ["/about", "/about-us", "/our-team", "/team", "/people",
                                  "/projects", "/our-projects", "/services", "/what-we-do",
                                  "/careers", "/expertise", "/our-expertise", "/sectors"]
                supplement_pages = []
                for path in priority_paths:
                    try:
                        sub_url = base + path
                        sub_pages = direct_fetch(sub_url)
                        if sub_pages:
                            for sp in sub_pages[:1]:  # just the target page, not its sublinks
                                if len(sp.get("markdown", "")) > 500:
                                    supplement_pages.append(sp)
                    except:
                        pass
                    if len(supplement_pages) >= 6:
                        break

                if supplement_pages:
                    st.success(f"✅ Supplemented with {len(supplement_pages)} additional subpages")
                    # Merge: keep original pages + add supplements (deduplicate by URL)
                    existing_urls = {p.get("url", "") for p in pages}
                    for sp in supplement_pages:
                        if sp.get("url", "") not in existing_urls:
                            pages.append(sp)
                    needs_fallback = False

            # Step 5 — Manual paste if everything truly failed
            if needs_fallback:
                st.markdown("""
                <div style='background:white;border:1px solid #f3f4f6;border-radius:8px;
                     padding:16px 20px;margin-bottom:12px;'>
                    <div style='font-weight:600;font-size:14px;color:#1a1a1a;margin-bottom:8px;'>
                        📋 Automatic fetch failed — paste manually:
                    </div>
                    <div style='font-size:13px;color:#4b5563;line-height:1.8;'>
                        1. Open the website in your browser<br>
                        2. Press <b>Ctrl+A</b> then <b>Ctrl+C</b><br>
                        3. Paste below and click Analyse →
                    </div>
                </div>
                """, unsafe_allow_html=True)

                gc1, gc2 = st.columns(2)
                with gc1:
                    if st.button("🔄 Retry Google Cache", use_container_width=True):
                        cache_pages = fetch_google_cache(website)
                        if cache_pages and any(len(p.get("markdown","")) > 500 for p in cache_pages):
                            st.session_state["cache_pages"] = cache_pages
                            st.session_state["use_cache"] = True
                            st.rerun()
                        else:
                            st.error("Google Cache not available for this site")

                manual_content = st.text_area(
                    "",
                    height=200,
                    placeholder="Paste website content here...",
                    label_visibility="collapsed"
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
        prog.progress(60)

        # ── ADDITIONAL SOURCE LOOKUPS (Option B — after company name known) ──
        company_name_known = company_data.get("company_name", "")
        domain_known       = extract_domain(website)
        extra_corpus       = ""
        source_summary     = []

        stat.caption("📋 Checking Companies House...")
        ch_text, ch_directors = lookup_companies_house(
            company_name_known,
            locations=company_data.get("locations", [])
        )
        if ch_text:
            extra_corpus += f"\n\n[SOURCE: Company Registry]\n{ch_text}"
            source_summary.append(f"📋 Company Registry — searched Companies House (UK), OpenCorporates (EU) and TED Tenders, {ch_directors} director entries found")

        stat.caption("💼 Checking LinkedIn...")
        li_text, li_employees = lookup_linkedin_company(company_name_known)
        if li_text:
            extra_corpus += f"\n\n[SOURCE: LinkedIn]\n{li_text}"
            source_summary.append(f"💼 LinkedIn — searched company page for employee count and signals ({li_employees} employees)" if li_employees else "💼 LinkedIn — searched company page, employee count not found publicly")

        stat.caption("⭐ Checking Glassdoor & Indeed...")
        gd_text, gd_reviews = lookup_glassdoor(company_name_known, domain_known)
        if gd_text:
            extra_corpus += f"\n\n[SOURCE: Glassdoor & Indeed Reviews]\n{gd_text}"
        source_summary.append(f"⭐ Glassdoor & Indeed — {gd_reviews} employee review snippets found, added to full analysis")

        stat.caption("🏗️ Checking planning applications...")
        pp_text, pp_projects = lookup_planning_portal(company_name_known)
        if pp_text:
            extra_corpus += f"\n\n[SOURCE: Planning Portal]\n{pp_text}"
            source_summary.append(f"🏗️ Planning Portal — {pp_projects} planning application mentions found, added to projects")

        # If no people found, try Google/LinkedIn people search
        if len(company_data.get("people", [])) == 0:
            stat.caption("👥 Searching for people via Google & LinkedIn...")
            google_text = search_people_via_google(company_name_known, domain_known)
            if google_text:
                extra_corpus += f"\n\n[SOURCE: People Search]\n{google_text}"
                source_summary.append(f"👥 People Search — searched LinkedIn profiles and Google for named engineers at this company")

        # Re-analyse with enriched corpus if extra data found
        if extra_corpus:
            enriched_corpus = corpus + extra_corpus[:20000]
            stat.caption("🧠 Re-analysing with additional sources...")
            company_raw2  = analyze_company(enriched_corpus)
            company_data2 = safe_json(company_raw2)
            # Merge — prefer enriched data but keep original if enriched is empty
            for key in ["people", "projects", "locations", "employee_count", "founded"]:
                if company_data2.get(key) and len(str(company_data2.get(key))) > len(str(company_data.get(key, ""))):
                    company_data[key] = company_data2[key]

        prog.progress(75)

        # Show source summary to rep
        if source_summary:
            st.markdown('<div class="sec-label" style="margin-top:8px;">Additional Sources Used</div>', unsafe_allow_html=True)
            for item in source_summary:
                st.markdown(f"""
                <div style='background:#f9fafb;border:1px solid #f3f4f6;border-radius:6px;
                     padding:6px 14px;margin-bottom:4px;font-family:Inter,sans-serif;
                     font-size:11px;color:#6b7280;'>
                    {item}
                </div>
                """, unsafe_allow_html=True)

        stat.caption("💡 Generating sales strategy...")
        sales_raw  = analyze_sales(corpus + extra_corpus[:5000], company_raw)
        sales_data = safe_json(sales_raw)
        prog.progress(100)

        stat.empty()
        prog.empty()
        st.markdown("<div style='height:0px'></div>", unsafe_allow_html=True)

        company_name = company_data.get("company_name", website)
        pages_count  = len(pages)

        entry = {
            "domain":       active_domain,
            "company":      company_name,
            "score":        sales_data.get("overall_score", "Cold"),
            "date":         now_gmt2().strftime("%d %b %Y %H:%M"),
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
                <span style='font-family:Inter,sans-serif;font-size:26px;font-weight:700;color:#1a1a1a;'>{company_name}</span>
                &nbsp;&nbsp;
                <span class='score-badge {score_cls(score)}'>{score_emoji(score)} {score} Lead</span>
            </div>
            <div style='font-family:"Inter",sans-serif;font-size:11px;color:#6b7280;margin-bottom:6px;'>📍 {locs}</div>
            <div style='font-family:"Inter",sans-serif;font-size:11px;color:#6b7280;margin-bottom:4px;'>
                👥 {emp} &nbsp;·&nbsp; Confidence: <b style='color:#1a1a1a;'>{conf}</b>
            </div>
            <div style='font-size:12px;color:#9ca3af;font-style:italic;margin-bottom:6px;'>{conf_reason}</div>
            <div style='font-size:14px;color:#4b5563;'>{score_reason}</div>
            """, unsafe_allow_html=True)
        with hc2:
            st.markdown(f"<div style='text-align:right;font-family:\"Inter\",sans-serif;font-size:11px;color:#9ca3af;padding-top:8px;'>{now_gmt2().strftime('%d %b %Y %H:%M')}</div>", unsafe_allow_html=True)
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
                    st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid #f3f4f6;font-size:14px;color:#374151;'>◆ {b}</div>", unsafe_allow_html=True)
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
                            st.markdown(f"<div style='font-size:12px;color:#6b7280;font-family:\"Inter\",sans-serif;'>{role}</div>", unsafe_allow_html=True)
                        with pc3:
                            safe_name = name.replace("'", "%27")
                            st.markdown(f'<a href="{li_url(safe_name)}" target="_blank" style="font-family:Inter,sans-serif;font-size:11px;color:#1a1a1a;text-decoration:none;border:1px solid rgba(200,71,30,0.4);padding:5px 12px;border-radius:4px;white-space:nowrap;">LinkedIn ↗</a>', unsafe_allow_html=True)
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
                    name        = (proj.get("name") or "Unknown Project").replace('"', '').replace("'", "")
                    ptype       = (proj.get("type") or "Other").replace('"', '').replace("'", "")
                    location    = (proj.get("location") or "").replace('"', '').replace("'", "")
                    client      = (proj.get("client") or "").replace('"', '').replace("'", "")
                    description = (proj.get("description") or "").replace('"', '').replace("'", "")
                    fem         = proj.get("fem_relevant", False)
        
                    fem_html = ""
                    if fem:
                        fem_html = '<span style="font-family:Inter,sans-serif;font-size:10px;color:#1a1a1a;background:rgba(26,26,26,0.06);border:1px solid #fecaca;padding:3px 9px;border-radius:20px;white-space:nowrap;margin-left:8px;">FEM RELEVANT</span>'
        
                    type_colors = {
                        "Bridge":         ("rgba(26,26,26,0.04)",  "rgba(26,26,26,0.2)",   "#1a1a1a"),
                        "Metro":          ("rgba(0,100,200,0.05)",  "rgba(0,100,200,0.4)",  "#0055cc"),
                        "Building":       ("rgba(0,168,90,0.05)",   "rgba(0,168,90,0.4)",   "#00784a"),
                        "Infrastructure": ("rgba(200,140,0,0.05)",  "rgba(200,140,0,0.4)",  "#8a5e00"),
                        "Residential":    ("rgba(120,80,200,0.05)", "rgba(120,80,200,0.4)", "#6040aa"),
                        "Industrial":     ("rgba(80,80,80,0.05)",   "rgba(80,80,80,0.3)",   "#444444"),
                        "Rail":           ("rgba(0,80,160,0.05)",   "rgba(0,80,160,0.4)",   "#005099"),
                        "Justice":        ("rgba(160,0,80,0.05)",   "rgba(160,0,80,0.4)",   "#a00050"),
                        "Defence":        ("rgba(60,80,60,0.05)",   "rgba(60,80,60,0.4)",   "#3c503c"),
                        "Education":      ("rgba(0,140,140,0.05)",  "rgba(0,140,140,0.4)",  "#008080"),
                        "Healthcare":     ("rgba(0,160,100,0.05)",  "rgba(0,160,100,0.4)",  "#00a064"),
                        "Transport":      ("rgba(0,100,180,0.05)",  "rgba(0,100,180,0.4)",  "#0064b4"),
                        "Energy":         ("rgba(200,120,0,0.05)",  "rgba(200,120,0,0.4)",  "#c87800"),
                        "Mixed Use":      ("rgba(100,60,160,0.05)", "rgba(100,60,160,0.4)", "#643ca0"),
                        "Other":          ("rgba(80,80,80,0.05)",   "rgba(80,80,80,0.3)",   "#555555"),
                    }
                    bg, border, color = type_colors.get(ptype, ("rgba(80,80,80,0.05)", "rgba(80,80,80,0.3)", "#555"))
        
                    meta_parts = []
                    if location:
                        meta_parts.append(f"📍 {location}")
                    if client:
                        meta_parts.append(f"👤 {client}")
                    meta_html = "&nbsp;&nbsp;·&nbsp;&nbsp;".join(meta_parts)
        
                    card = (
                        '<div style="background:white;border:1px solid #f3f4f6;border-radius:8px;padding:16px 20px;margin-bottom:10px;">'
                        '<div style="display:flex;align-items:center;margin-bottom:8px;flex-wrap:wrap;gap:6px;">'
                        f'<div style="font-weight:600;font-size:15px;color:#1a1a1a;">{name}</div>'
                        + fem_html +
                        f'<span style="font-family:Inter,sans-serif;font-size:10px;padding:3px 10px;'
                        f'background:{bg};border:1px solid {border};border-radius:20px;color:{color};">'
                        f'{ptype}</span>'
                        '</div>'
                        f'<div style="font-size:12px;color:#9ca3af;font-family:Inter,sans-serif;margin-bottom:6px;">{meta_html}</div>'
                        f'<div style="font-size:13px;color:#4b5563;line-height:1.6;">{description}</div>'
                        '</div>'
                    )
                    st.markdown(card, unsafe_allow_html=True)
            else:
                st.info("No projects found. The site may not have a public portfolio or case studies section.")


        # TAB 4 ── FEM OPPS
        with t4:
            fa, fb = st.columns([3, 2])
            with fa:
                st.markdown('<div class="sec-label">FEM / FEA Opportunities</div>', unsafe_allow_html=True)
                for i, opp in enumerate(sales_data.get("fem_opportunities", ["None identified"]), 1):
                    st.markdown(f'<div class="insight-card"><span style=\'font-family:"Inter",sans-serif;font-size:10px;color:#1a1a1a;\'>0{i}</span><br>{opp}</div>', unsafe_allow_html=True)
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
                    st.markdown(f'<div class="insight-card" style="border-left-color:#d97706;">⚠ {obj}</div>', unsafe_allow_html=True)
                    
                st.markdown('<div class="sec-label" style="margin-top:16px;">Recommended MIDAS Products</div>', unsafe_allow_html=True)
                products = sales_data.get("recommended_products", [])
                product_reason = sales_data.get("product_reason", "")
                if products:
                    pills = " ".join(f'<span class="pill-tag pill-red">{p}</span>' for p in products)
                    st.markdown(f"<div style='margin-bottom:8px;'>{pills}</div>", unsafe_allow_html=True)
                if product_reason:
                    st.markdown(f"<div style='font-size:13px;color:#4b5563;'>{product_reason}</div>", unsafe_allow_html=True)
                    
            with sb:
                st.markdown('<div class="sec-label">Pre-Meeting Cheat Sheet</div>', unsafe_allow_html=True)
                st.markdown("<div style='font-size:11px;color:#6b7280;font-family:\"Inter\",sans-serif;letter-spacing:0.1em;margin-bottom:8px;'>3 THINGS TO MENTION</div>", unsafe_allow_html=True)
                for m in sales_data.get("pre_meeting_mention", []):
                    st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid #f3f4f6;font-size:14px;'>✓ {m}</div>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:11px;color:#6b7280;font-family:\"Inter\",sans-serif;letter-spacing:0.1em;margin:20px 0 8px;'>3 SMART QUESTIONS</div>", unsafe_allow_html=True)
                for q in sales_data.get("smart_questions", []):
                    st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid #f3f4f6;font-size:14px;'>? {q}</div>", unsafe_allow_html=True)
                st.markdown('<div class="sec-label" style="margin-top:24px;">Opening Line</div>', unsafe_allow_html=True)
                opening = sales_data.get("opening_line", "")
                if opening:
                    st.markdown(f'''<div style="background:white;border:1px solid #f3f4f6;border-left:3px solid #1a1a1a;border-radius:8px;padding:24px 28px;font-size:15px;line-height:1.8;font-style:italic;position:relative;">
                        <span style="font-family:Inter,sans-serif;font-size:64px;font-weight:700;color:rgba(26,26,26,0.15);position:absolute;top:-8px;left:14px;line-height:1;">"</span>
                        <span style="color:#374151;display:block;padding-left:20px;">{opening}</span>
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
                    fem_html  = '<span style="font-family:Inter,sans-serif;font-size:10px;color:#1a1a1a;background:rgba(26,26,26,0.06);border:1px solid #fecaca;padding:3px 9px;border-radius:20px;white-space:nowrap;">FEM MENTIONED</span>' if fem else ""
                    pills_html = "".join(f'<span style="font-family:Inter,sans-serif;font-size:10px;padding:3px 10px;border:1px solid #e5e7eb;border-radius:20px;color:#6b7280;background:#fafafa;margin:2px;display:inline-block;">{s}</span>' for s in skills) if skills else '<span style="font-size:12px;color:#9ca3af;">No skills listed</span>'
                    st.markdown(
                        f'<div style="background:white;border:1px solid #f3f4f6;border-radius:8px;padding:16px 20px;margin-bottom:10px;">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">'
                        f'<div style="font-weight:600;font-size:15px;color:#1a1a1a;">{title}</div>{fem_html}</div>'
                        f'<div style="display:flex;flex-wrap:wrap;gap:6px;">{pills_html}</div></div>',
                        unsafe_allow_html=True
                    )
            else:
                st.info("No relevant vacancies found on this website.")

        # TAB 7 ── EMAIL
        with t7:
            st.markdown('<div class="sec-label">Cold Outreach Email</div>', unsafe_allow_html=True)
            st.markdown("<div style='background:white;border:1px solid #f3f4f6;border-radius:8px;padding:16px 20px;margin-bottom:16px;font-size:13px;color:#6b7280;'>Generate a personalised cold email based on the company intelligence. Edit before sending.</div>", unsafe_allow_html=True)

            current_domain = active_domain
            if st.session_state.get("email_domain") != current_domain:
                st.session_state["generated_email"] = ""
                st.session_state["email_domain"] = current_domain

            if st.button("✉ Generate Email Draft", key="gen_email_btn"):
                st.session_state["generated_email"] = generate_email(company_data, sales_data)
                st.rerun()

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
                    st.markdown("<div style='font-family:Inter,sans-serif;font-size:11px;color:#6b7280;margin-bottom:4px;letter-spacing:0.1em;'>SUBJECT LINE</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='background:white;border:1px solid #f3f4f6;border-radius:6px;padding:10px 14px;font-size:14px;font-weight:600;color:#1a1a1a;margin-bottom:16px;'>{subject}</div>", unsafe_allow_html=True)

                st.markdown("<div style='font-family:Inter,sans-serif;font-size:11px;color:#6b7280;margin-bottom:4px;letter-spacing:0.1em;'>EMAIL BODY — edit below before copying</div>", unsafe_allow_html=True)
                edited_email = st.text_area("", value=body, height=320, label_visibility="collapsed")
                full_copy = f"Subject: {subject}\n\n{edited_email}" if subject else edited_email
                st.download_button("📋 Download as .txt", data=full_copy, file_name=f"MIDAS_Email_{company_name.replace(' ','_')}.txt", mime="text/plain")

        # TAB 8 ── EXPORT & NOTES
        with t8:
            ea, eb = st.columns([1, 1])
            with ea:
                st.markdown('<div class="sec-label">PDF Export</div>', unsafe_allow_html=True)
                st.markdown("<div style='background:white;border:1px solid #f3f4f6;border-radius:8px;padding:20px 24px;margin-bottom:16px;'><div style='font-weight:600;font-size:15px;color:#1a1a1a;margin-bottom:6px;'>PDF Sales Dossier</div><div style='font-size:13px;color:#6b7280;'>Ready to print or share before a meeting.</div></div>", unsafe_allow_html=True)
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
