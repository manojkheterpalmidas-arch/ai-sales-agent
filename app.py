import streamlit as st
from openai import OpenAI
import requests
import json
import re
from datetime import datetime

# ── AUTH ──────────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

PASSCODE = "5487"

if not st.session_state.authenticated:
    st.set_page_config(page_title="MIDAS Pre Sales Intel", page_icon="🔐", layout="centered")
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700&family=JetBrains+Mono:wght@400&display=swap');
    html, body, [class*="css"] { background: #f7f6f2 !important; font-family: 'Syne', sans-serif; }
    .stApp { background: #f7f6f2 !important; }
    .stTextInput > div > div > input {
        background: white !important; color: #111 !important;
        border: 1.5px solid #ddd !important; border-radius: 6px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 22px !important; letter-spacing: 0.4em !important;
        text-align: center !important; padding: 14px !important;
        caret-color: #c8471e !important;
    }
    .stTextInput > div > div > input:focus { border-color: #c8471e !important; box-shadow: 0 0 0 3px rgba(200,71,30,0.1) !important; }
.stButton > button {
    background: #111 !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 11px 28px !important;
}
.stButton > button:hover {
    background: #c8471e !important;
    color: white !important;
}
/* Target the inner p tag Streamlit injects */
div[data-testid="stButton"] > button > div > p,
div[data-testid="stButton"] button p,
div[data-testid="stButton"] button span,
div[data-testid="stButton"] button * {
    color: white !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
}
.stButton > button:hover { background: #c8471e !important; }
.stButton > button:hover p,
.stButton > button:hover span,
.stButton > button:hover div {
    color: white !important;
}
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:60px'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("""
        <div style='text-align:center;margin-bottom:32px;'>
            <div style='font-family:Syne,sans-serif;font-size:11px;letter-spacing:0.3em;color:#c8471e;text-transform:uppercase;margin-bottom:6px;'>MIDAS IT</div>
            <div style='font-family:Syne,sans-serif;font-size:32px;font-weight:700;color:#111;'>Sales Intelligence</div>
            <div style='width:32px;height:3px;background:#c8471e;margin:12px auto 0;'></div>
        </div>
        """, unsafe_allow_html=True)
        code = st.text_input("", type="password", placeholder="· · · ·", label_visibility="collapsed")
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        if st.button("UNLOCK"):
            if code == PASSCODE:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect passcode")
    st.stop()

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MIDAS Pre Sales Intelligence", layout="wide", page_icon="🚀")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700&family=JetBrains+Mono:wght@400;500&family=Barlow:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Barlow', sans-serif !important;
    background: #f7f6f2 !important;
    color: #111 !important;
}
.stApp { background: #f7f6f2 !important; }

/* Force text colour in all Streamlit containers */
.stApp, .stApp * {
    color: #111 !important;
}
/* Exempt buttons from global dark text override */
.stApp .stButton button,
.stApp .stButton button *,
.stApp div[data-testid="stButton"] button,
.stApp div[data-testid="stButton"] button * {
    color: white !important;
}
.stMarkdown, .stMarkdown * { color: #111 !important; }
.stText { color: #111 !important; }

/* Tab panel content */
.stTabs [data-baseweb="tab-panel"],
.stTabs [data-baseweb="tab-panel"] * { color: #111 !important; }

/* Expander content */
.streamlit-expanderContent,
.streamlit-expanderContent * { color: #111 !important; }

/* Column containers */
[data-testid="column"],
[data-testid="column"] * { color: #111 !important; }

/* Metric label and value */
[data-testid="stMetricValue"] { color: #c8471e !important; }
[data-testid="stMetricLabel"] { color: #888 !important; }
[data-testid="stMetricDelta"] { color: #555 !important; }

/* Info / success / warning boxes — keep their own text colours */
.stAlert, .stAlert * { color: inherit !important; }

/* Captions */
.stCaptionContainer, .stCaptionContainer * { color: #888 !important; }

/* Links must stay visible */
a { color: #c8471e !important; }
a:hover { color: #a03518 !important; 
}
.stApp { background: #f7f6f2 !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2rem 2rem 4rem !important; max-width: 1200px !important; }

/* Buttons */
.stButton > button {
    background: #111 !important; color: white !important;
    border: none !important; border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 13px !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important; padding: 11px 28px !important;
}
.stButton > button:hover { background: #c8471e !important; }

/* Download button */
.stDownloadButton > button {
    background: transparent !important; color: #c8471e !important;
    border: 1.5px solid #c8471e !important; border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important; font-weight: 700 !important;
    font-size: 12px !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
.stDownloadButton > button:hover { background: rgba(200,71,30,0.06) !important; }

/* Input */
.stTextInput > div > div > input {
    background: white !important; color: #111 !important;
    border: 1.5px solid #e0ddd5 !important; border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 14px !important;
    padding: 11px 14px !important; caret-color: #c8471e !important;
}
.stTextInput > div > div > input:focus {
    border-color: #c8471e !important;
    box-shadow: 0 0 0 3px rgba(200,71,30,0.1) !important;
}
.stTextInput > div > div > input::placeholder { color: #bbb !important; }

/* Metric overrides */
[data-testid="metric-container"] {
    background: white !important;
    border: 1px solid #e8e4dc !important;
    border-radius: 8px !important;
    padding: 16px 20px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 28px !important; font-weight: 700 !important;
    color: #c8471e !important;
}
[data-testid="stMetricLabel"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 10px !important; letter-spacing: 0.1em !important;
    color: #888 !important; text-transform: uppercase !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #e8e4dc !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Syne', sans-serif !important;
    font-size: 12px !important; font-weight: 700 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    color: #999 !important; padding: 10px 20px !important;
    background: transparent !important; border: none !important;
    border-bottom: 2px solid transparent !important; margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
    color: #c8471e !important;
    border-bottom-color: #c8471e !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 24px !important; }

/* Progress */
.stProgress > div > div > div { background: #c8471e !important; border-radius: 2px !important; }
.stProgress > div > div { background: #e8e4dc !important; border-radius: 2px !important; }

/* Expander */
.streamlit-expanderHeader {
    background: white !important;
    border: 1px solid #e8e4dc !important;
    border-radius: 6px !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 12px !important; font-weight: 700 !important;
    letter-spacing: 0.08em !important; text-transform: uppercase !important;
    color: #555 !important;
}

/* Alerts */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 6px !important;
    font-family: 'Barlow', sans-serif !important;
    font-size: 14px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #ddd; border-radius: 2px; }

/* Section label utility */
.sec-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; font-weight: 500;
    letter-spacing: 0.2em; text-transform: uppercase;
    color: #c8471e; margin-bottom: 12px;
    display: flex; align-items: center; gap: 10px;
}
.sec-label::after { content:''; flex:1; height:1px; background:#e8e4dc; }

/* Cards */
.insight-card {
    background: white;
    border: 1px solid #e8e4dc;
    border-left: 3px solid #c8471e;
    border-radius: 6px;
    padding: 14px 18px;
    margin-bottom: 10px;
    font-size: 14px; line-height: 1.7;
    color: #222;
}
.signal-card {
    background: white;
    border: 1px solid #e8e4dc;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 13px; line-height: 1.6; color: #333;
}
.person-card {
    background: white;
    border: 1px solid #e8e4dc;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 8px;
    display: flex; align-items: center; gap: 12px;
}
.av {
    width: 38px; height: 38px; border-radius: 50%;
    background: #111; color: white;
    display: inline-flex; align-items: center; justify-content: center;
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700;
    flex-shrink: 0;
}
.pill-tag {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; padding: 3px 9px;
    border: 1px solid #e0ddd5; border-radius: 20px;
    color: #888; margin: 2px;
}
.pill-red    { border-color: rgba(200,71,30,0.4); color: #c8471e; background: rgba(200,71,30,0.05); }
.pill-green  { border-color: rgba(0,168,90,0.4);  color: #00784a; background: rgba(0,168,90,0.05); }
.pill-amber  { border-color: rgba(200,140,0,0.4); color: #8a5e00; background: rgba(200,140,0,0.05); }
.vac-card {
    background: white; border: 1px solid #e8e4dc;
    border-radius: 8px; padding: 16px 20px; margin-bottom: 10px;
}
.opening-box {
    background: #111; color: #f0ede6 !important;
    border-radius: 8px; padding: 24px 28px;
    font-size: 15px; line-height: 1.8;
    font-style: italic; position: relative;
}
.opening-box, .opening-box * { color: #f0ede6 !important; }
.opening-box::before {
    content: '"'; font-family: 'Syne', sans-serif;
    font-size: 72px; font-weight: 700;
    color: rgba(200,71,30,0.4) !important;
    position: absolute; top: -10px; left: 16px; line-height: 1;
}
.score-hot  { background: #fef0ed; color: #c8471e; border: 1px solid rgba(200,71,30,0.3); }
.score-warm { background: #fffbf0; color: #996600; border: 1px solid rgba(200,140,0,0.3); }
.score-cold { background: #f5f5f5; color: #666;    border: 1px solid #ddd; }
.score-badge {
    display: inline-block;
    font-family: 'Syne', sans-serif; font-weight: 700;
    font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase;
    padding: 6px 16px; border-radius: 20px;
}
</style>
""", unsafe_allow_html=True)

# ── CLIENTS ───────────────────────────────────────────────────────────────────
deepseek = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
FIRECRAWL_KEY = st.secrets["FIRECRAWL_API_KEY"]

# ── FIRECRAWL ─────────────────────────────────────────────────────────────────

def firecrawl_scrape_single(url):
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"]},
            timeout=20
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
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}",
                         "Content-Type": "application/json"},
                json={"url": url, "formats": ["markdown"]},
                timeout=20
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

        priority_keywords = [
            "team", "people", "our-team", "about", "staff",
            "leadership", "directors", "who-we-are",
            "careers", "jobs", "vacancies", "join",
            "projects", "services", "what-we-do", "contact"
        ]

        all_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(base_url, href)
            parsed = urlparse(full)
            if (parsed.netloc == domain and
                not any(full.endswith(ext) for ext in [".pdf",".jpg",".png",".zip"]) and
                "#" not in full and
                full != base_url and
                full not in visited):
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


def firecrawl_crawl(url, max_pages=15):
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
            json={"url": url, "limit": max_pages, "scrapeOptions": {"formats": ["markdown"]}},
            timeout=30
        )
        job_id = resp.json().get("id")
        if not job_id:
            return firecrawl_multi_scrape(url)

        import time
        for _ in range(25):
            time.sleep(4)
            poll = requests.get(
                f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                timeout=15
            ).json()

            status = poll.get("status")
            pages  = poll.get("data", [])

            if status == "completed" or (status == "scraping" and len(pages) >= 5):
                results = [
                    {"url": p.get("metadata", {}).get("sourceURL", url),
                     "markdown": p.get("markdown", "")}
                    for p in pages if p.get("markdown", "").strip()
                ]
                if results:
                    return results

            if status == "failed":
                break

        return firecrawl_multi_scrape(url)

    except:
        return firecrawl_multi_scrape(url)


# ── TEXT PREP ─────────────────────────────────────────────────────────────────

def build_corpus(pages):
    chunks = [
        f"[PAGE: {p.get('url','')}]\n{p.get('markdown','').strip()[:5000]}"
        for p in pages if p.get("markdown", "").strip()
    ]
    return "\n\n---\n\n".join(chunks)[:40000]

# ── AI ────────────────────────────────────────────────────────────────────────
def ask_deepseek(system, user, max_tokens=2000):
    resp = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1, max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()


def analyze_company(corpus):
    return ask_deepseek(
        "You are a B2B sales analyst for MIDAS IT (FEA/FEM software). Extract facts only. Respond in pure JSON, no markdown.",
        f"""Return ONLY valid JSON:
{{
  "company_name": "string",
  "tagline": "string or null",
   "locations": ["city1", "city2", "city3"],
  "founded": "year or null",
  "employee_count": "string or null",
  "overview": ["bullet 1", "bullet 2", "bullet 3"],
  "engineering_capabilities": ["bullet 1"],
  "project_types": ["bridge"],
  "software_mentioned": ["any FEA/CAD/BIM tools"],
    "people": [{{"name": "Full Name", "role": "Job Title", "tier": "Owner|Founder|Director|Principal|Senior|Engineer|Graduate|Tec
  "open_roles": [{{"title": "Job title", "skills": ["skill1"], "fem_mentioned": true}}],
  "confidence": "High|Medium|Low"
}}
Extract ALL people mentioned anywhere on the site — team pages, about pages, project pages, news, 
contact pages. Include owners, founders, directors, engineers at all levels, technicians, and 
graduate engineers. Do NOT limit to senior staff only. If a name appears with any role or title, 
include them.

For locations: extract EVERY office location mentioned anywhere on the site — contact pages, 
footer, about pages, office listings. Return ONLY city names (e.g. "Manchester" not 
"123 High Street, Manchester M1 1AA"). Include ALL cities, do not stop at one.

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

def export_md(company, cd, sd):
    lines = [f"# MIDAS Sales Intel: {company}", f"*{datetime.now().strftime('%d %b %Y %H:%M')}*\n"]
    lines += ["## Overview"] + [f"- {b}" for b in cd.get("overview", [])]
    lines += ["\n## Capabilities"] + [f"- {b}" for b in cd.get("engineering_capabilities", [])]
    lines += ["\n## People"] + [f"- **{p['name']}** — {p.get('role','')}" for p in cd.get("people", [])]
    lines += ["\n## FEM Opportunities"] + [f"- {o}" for o in sd.get("fem_opportunities", [])]
    lines += [f"\n## Strategy\n**Entry:** {sd.get('entry_point','')}\n**Value:** {sd.get('value_positioning','')}\n**Opening:** {sd.get('opening_line','')}"]
    lines += ["\n## Questions"] + [f"- {q}" for q in sd.get("smart_questions", [])]
    return "\n".join(lines)


# ── TOP BAR ───────────────────────────────────────────────────────────────────
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
col_logo, col_user = st.columns([6, 1])
with col_logo:
    st.markdown("""
    <div style='display:flex;align-items:center;gap:12px;padding:4px 0 20px;'>
        <div style='font-family:Syne,sans-serif;font-size:20px;font-weight:700;color:#111;letter-spacing:0.05em;'>
            MIDAS <span style='color:#c8471e;'>·</span> INTEL
        </div>
        <div style='font-family:"JetBrains Mono",monospace;font-size:10px;color:#bbb;letter-spacing:0.1em;
             background:#f0ede6;border:1px solid #e0ddd5;padding:3px 10px;border-radius:20px;'>
            SALES INTELLIGENCE
        </div>
    </div>
    """, unsafe_allow_html=True)
with col_user:
    st.markdown("<div style='text-align:right;font-size:12px;color:#888;padding-top:8px;font-family:\"JetBrains Mono\",monospace;'>Manoj | MIDAS IT</div>", unsafe_allow_html=True)

# ── SEARCH ────────────────────────────────────────────────────────────────────
c1, c2 = st.columns([5, 1])
with c1:
    website = st.text_input("", placeholder="https://target-engineering-company.com", label_visibility="collapsed")
with c2:
    run = st.button("Analyse →", use_container_width=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
st.divider()

# ── ANALYSIS ──────────────────────────────────────────────────────────────────
if run:
    if not website:
        st.warning("Please enter a website URL.")
        st.stop()
    if not website.startswith("http"):
        website = "https://" + website

    prog = st.progress(0)
    stat = st.empty()

    stat.caption("🔍 Crawling website with Firecrawl...")
    pages = firecrawl_crawl(website)
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

    # ── HEADER ────────────────────────────────────────────────────────────
    company_name = company_data.get("company_name", website)
    score        = sales_data.get("overall_score", "Warm")
    score_reason = sales_data.get("score_reason", "")
    locs_list = company_data.get("locations", [])
    locs = " · ".join(locs_list) if locs_list else "—"
    emp          = company_data.get("employee_count") or "—"
    conf         = company_data.get("confidence", "Medium")

    hc1, hc2 = st.columns([4, 1])
    with hc1:
        st.markdown(f"""
        <div style='margin-bottom:6px;'>
            <span style='font-family:Syne,sans-serif;font-size:26px;font-weight:700;color:#111;'>{company_name}</span>
            &nbsp;&nbsp;
            <span class='score-badge {score_cls(score)}'>{score} Lead</span>
        </div>
        <div style='font-family:"JetBrains Mono",monospace;font-size:11px;color:#888;margin-bottom:6px;'>
            📍 {locs}
        </div>
        <div style='font-family:"JetBrains Mono",monospace;font-size:11px;color:#888;margin-bottom:6px;'>
            👥 {emp} &nbsp;·&nbsp; Confidence: <b style='color:#c8471e;'>{conf}</b>
        </div>
        <div style='font-size:14px;color:#555;'>{score_reason}</div>
        """, unsafe_allow_html=True)
    with hc2:
        st.markdown(f"<div style='text-align:right;font-family:\"JetBrains Mono\",monospace;font-size:11px;color:#bbb;padding-top:8px;'>{datetime.now().strftime('%d %b %Y %H:%M')}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # ── METRICS — native st.metric, no raw HTML ───────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("People Identified",  len(company_data.get("people", [])))
    m2.metric("FEM Opportunities",  len(sales_data.get("fem_opportunities", [])))
    m3.metric("Open Roles",         len(company_data.get("open_roles", [])))
    m4.metric("Pages Crawled",      len(pages))

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.divider()

    # ── TABS ──────────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5, t6 = st.tabs(["🏢  Company", "👥  People", "💡  FEM Opps", "🎯  Strategy", "📋  Vacancies", "📤  Export"])

    # TAB 1 ── COMPANY ─────────────────────────────────────────────────────
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
                pills = " ".join(f'<span class="pill-tag pill-red">{p}</span>' for p in pts)
                st.markdown(f"<div style='margin-bottom:16px;'>{pills}</div>", unsafe_allow_html=True)
            else:
                st.caption("None detected")

            st.markdown('<div class="sec-label">Software & Tools Detected</div>', unsafe_allow_html=True)
            sw = company_data.get("software_mentioned", [])
            if sw:
                pills = " ".join(f'<span class="pill-tag pill-amber">{s}</span>' for s in sw)
                st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)
                st.caption("Existing tools — position MIDAS alongside or against these")
            else:
                st.success("No competing software detected — clean opportunity to introduce MIDAS as first FEA tool")

  # TAB 2 ── PEOPLE ──────────────────────────────────────────────────────
    with t2:
        people = company_data.get("people", [])
        if people:
            tier_order = ["Owner", "Founder", "Director", "Principal", "Senior", "Engineer", "Graduate", "Technician", "Other"]
            # Group by tier, preserve order
            grouped = {}
            for p in people:
                tier = p.get("tier", "Other")
                if tier not in grouped:
                    grouped[tier] = []
                grouped[tier].append(p)

            tier_icons = {
                "Owner": "★", "Founder": "★",
                "Director": "◈", "Principal": "◈",
                "Senior": "◆", "Engineer": "◇",
                "Graduate": "◇", "Technician": "◇", "Other": "·"
            }

            for tier in tier_order:
                tier_ppl = grouped.get(tier, [])
                if not tier_ppl:
                    continue
                icon = tier_icons.get(tier, "·")
                st.markdown(f'<div class="sec-label">{icon} {tier}s</div>', unsafe_allow_html=True)
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

            # Show unmatched tier people too — catch-all so nobody is dropped
            all_shown_tiers = set(tier_order)
            leftover = [p for p in people if p.get("tier", "Other") not in all_shown_tiers]
            if leftover:
                st.markdown('<div class="sec-label">· Other</div>', unsafe_allow_html=True)
                for p in leftover:
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
        else:
            st.info("No people identified. The site may not have a public team page.")

    # TAB 3 ── FEM OPPS ────────────────────────────────────────────────────
    with t3:
        fa, fb = st.columns([3, 2])
        with fa:
            st.markdown('<div class="sec-label">FEM / FEA Opportunities</div>', unsafe_allow_html=True)
            for i, opp in enumerate(sales_data.get("fem_opportunities", ["None identified"]), 1):
                st.markdown(f"""
                <div class="insight-card">
                    <span style='font-family:"JetBrains Mono",monospace;font-size:10px;color:#c8471e;'>0{i}</span><br>
                    {opp}
                </div>""", unsafe_allow_html=True)
        with fb:
            st.markdown('<div class="sec-label">Hiring Signals</div>', unsafe_allow_html=True)
            for s in sales_data.get("hiring_signals", []):
                st.markdown(f'<div class="signal-card">▲ {s}</div>', unsafe_allow_html=True)
            st.markdown('<div class="sec-label" style="margin-top:16px;">Expansion Signals</div>', unsafe_allow_html=True)
            for s in sales_data.get("expansion_signals", []):
                st.markdown(f'<div class="signal-card">◆ {s}</div>', unsafe_allow_html=True)

    # TAB 4 ── STRATEGY ────────────────────────────────────────────────────
    with t4:
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
                st.markdown(f'''
                <div style="background:#111;border-radius:8px;padding:24px 28px;
                     font-size:15px;line-height:1.8;font-style:italic;position:relative;">
                    <span style="font-family:Syne,sans-serif;font-size:72px;font-weight:700;
                         color:rgba(200,71,30,0.4);position:absolute;top:-10px;left:16px;
                         line-height:1;">"</span>
                    <span style="color:#f0ede6 !important;display:block;padding-left:20px;">
                        {opening}
                    </span>
                </div>''', unsafe_allow_html=True)

    # TAB 5 ── VACANCIES ───────────────────────────────────────────────────
    with t5:
        roles = company_data.get("open_roles", [])
        if roles:
            fem_n = sum(1 for r in roles if r.get("fem_mentioned"))
            if fem_n:
                st.success(f"🎯 {fem_n} role(s) explicitly mention FEM/FEA — strong buying signal")
            st.markdown('<div class="sec-label">Open Roles</div>', unsafe_allow_html=True)
            for role in roles:
                fem_flag = "<span class='pill-tag pill-red'>FEM MENTIONED</span>" if role.get("fem_mentioned") else ""
                skills   = " ".join(f'<span class="pill-tag">{s}</span>' for s in role.get("skills", []))
                st.markdown(f"""
                <div class="vac-card">
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;'>
                        <div style='font-weight:600;font-size:15px;'>{role.get('title','Unknown role')}</div>
                        {fem_flag}
                    </div>
                    <div>{skills}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("No relevant vacancies found on this website.")

    # TAB 6 ── EXPORT ──────────────────────────────────────────────────────
    with t6:
        st.markdown('<div class="sec-label">Export Dossier</div>', unsafe_allow_html=True)
        md_out = export_md(company_name, company_data, sales_data)
        fname  = f"MIDAS_Intel_{company_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.md"
        st.download_button("📥 Download as Markdown", data=md_out, file_name=fname, mime="text/markdown")
        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-label">Raw JSON</div>', unsafe_allow_html=True)
        with st.expander("Company data"):
            st.json(company_data)
        with st.expander("Sales strategy"):
            st.json(sales_data)
