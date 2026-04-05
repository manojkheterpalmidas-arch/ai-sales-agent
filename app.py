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
    st.set_page_config(page_title="MIDAS Intel", page_icon="🔐", layout="centered")
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
    html, body, [class*="css"] { background: #080c10 !important; color: #e2e8f0 !important; font-family: 'Rajdhani', sans-serif; }
    .stApp { background: #080c10 !important; }
    .stTextInput > div > div > input {
        background: #0f1923 !important; color: #e2e8f0 !important;
        border: 1px solid #1e3a5f !important; border-radius: 4px !important;
        font-family: 'JetBrains Mono', monospace !important; font-size: 18px !important;
        letter-spacing: 0.3em !important; text-align: center !important;
        caret-color: #00d4ff !important; padding: 14px !important;
    }
    .stTextInput > div > div > input:focus { border-color: #00d4ff !important; box-shadow: 0 0 20px rgba(0,212,255,0.2) !important; }
    .stButton > button {
        background: transparent !important; color: #00d4ff !important;
        border: 1px solid #00d4ff !important; border-radius: 2px !important;
        font-family: 'Rajdhani', sans-serif !important; font-weight: 700 !important;
        font-size: 13px !important; letter-spacing: 0.15em !important;
        text-transform: uppercase !important; padding: 10px 32px !important; width: 100% !important;
    }
    .stButton > button:hover { background: rgba(0,212,255,0.08) !important; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 60px 0 40px;">
        <div style="font-family:'Rajdhani',sans-serif; font-size:11px; letter-spacing:0.3em;
             color:#00d4ff; text-transform:uppercase; margin-bottom:8px;">MIDAS IT</div>
        <div style="font-family:'Rajdhani',sans-serif; font-size:36px; font-weight:700;
             color:#e2e8f0; letter-spacing:0.05em;">SALES INTELLIGENCE</div>
        <div style="width:40px; height:2px; background:#00d4ff; margin:16px auto 40px;"></div>
        <div style="font-family:'JetBrains Mono',monospace; font-size:12px; color:#4a6080;
             letter-spacing:0.1em; margin-bottom:32px;">ENTER ACCESS CODE</div>
    </div>
    """, unsafe_allow_html=True)

    code = st.text_input("", type="password", placeholder="• • • •", label_visibility="collapsed")
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    if st.button("AUTHENTICATE"):
        if code == PASSCODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.markdown("<div style='text-align:center;color:#ff4560;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:12px;'>ACCESS DENIED</div>", unsafe_allow_html=True)
    st.stop()

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MIDAS Sales Intelligence", layout="wide", page_icon="🚀")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;500;600;700&family=JetBrains+Mono:wght@300;400;500&family=Barlow:wght@300;400;500;600&display=swap');

:root {
    --bg:        #080c10;
    --bg2:       #0d1520;
    --bg3:       #111d2e;
    --border:    #1a2f4a;
    --border2:   #1e3a5f;
    --accent:    #00d4ff;
    --accent2:   #0097b8;
    --green:     #00e676;
    --amber:     #ffab40;
    --red:       #ff4560;
    --text:      #e2e8f0;
    --muted:     #607d99;
    --dim:       #2d4a66;
}

html, body, [class*="css"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Barlow', sans-serif;
}

.stApp { background: var(--bg) !important; }

/* Hide streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── TOP NAV ── */
.top-nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 32px;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
    position: sticky; top: 0; z-index: 100;
}
.nav-logo {
    font-family: 'Rajdhani', sans-serif;
    font-size: 18px; font-weight: 700; letter-spacing: 0.12em;
    color: var(--text);
}
.nav-logo span { color: var(--accent); }
.nav-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.15em;
    color: var(--accent); background: rgba(0,212,255,0.08);
    border: 1px solid rgba(0,212,255,0.25);
    padding: 4px 12px; border-radius: 2px;
    text-transform: uppercase;
}

/* ── SEARCH BAR ── */
.search-wrap {
    padding: 28px 32px 20px;
    border-bottom: 1px solid var(--border);
    background: var(--bg);
    display: flex; align-items: center; gap: 16px;
}

.stTextInput > div > div > input {
    background: var(--bg2) !important;
    color: var(--text) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 3px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    caret-color: var(--accent) !important;
    letter-spacing: 0.02em !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
}
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(0,212,255,0.12) !important;
    outline: none !important;
}
.stTextInput > div > div > input::placeholder { color: var(--dim) !important; }

/* ── BUTTON ── */
.stButton > button {
    background: var(--accent) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 3px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important;
    font-size: 13px !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 12px 28px !important;
    transition: background 0.15s !important;
    white-space: nowrap !important;
}
.stButton > button:hover { background: #33deff !important; }
.stButton > button:active { transform: scale(0.98) !important; }

/* ── PROGRESS ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, var(--accent2), var(--accent)) !important;
    border-radius: 2px !important;
}
.stProgress > div > div {
    background: var(--bg3) !important;
    border-radius: 2px !important;
}

/* ── TABS ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
    padding: 0 32px !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 13px !important; font-weight: 600 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    color: var(--muted) !important;
    padding: 12px 20px !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    transition: color 0.15s !important;
}
.stTabs [data-baseweb="tab"]:hover { color: var(--text) !important; }
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* ── SECTION HEADINGS ── */
.sec-head {
    font-family: 'Rajdhani', sans-serif;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.25em; text-transform: uppercase;
    color: var(--accent); margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px;
}
.sec-head::after {
    content: ''; flex: 1; height: 1px;
    background: var(--border);
}

/* ── CARDS ── */
.card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 18px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.card:hover { border-color: var(--border2); }

.card-accent {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 4px;
    padding: 16px 20px;
    margin-bottom: 10px;
}

.card-green  { border-left-color: var(--green) !important; }
.card-amber  { border-left-color: var(--amber) !important; }
.card-red    { border-left-color: var(--red) !important; }

/* ── METRIC ROW ── */
.metric-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1px;
    background: var(--border);
    border: 1px solid var(--border);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 24px;
}
.metric-cell {
    background: var(--bg2);
    padding: 20px 24px;
    text-align: center;
}
.metric-val {
    font-family: 'Rajdhani', sans-serif;
    font-size: 36px; font-weight: 700;
    color: var(--accent); line-height: 1;
    margin-bottom: 4px;
}
.metric-lbl {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.12em;
    color: var(--muted); text-transform: uppercase;
}

/* ── SCORE BADGE ── */
.score-hot    { color: var(--red);   background: rgba(255,69,96,0.12);  border: 1px solid rgba(255,69,96,0.3);  }
.score-warm   { color: var(--amber); background: rgba(255,171,64,0.12); border: 1px solid rgba(255,171,64,0.3); }
.score-cold   { color: var(--muted); background: rgba(96,125,153,0.12); border: 1px solid rgba(96,125,153,0.3); }
.score-badge  {
    font-family: 'Rajdhani', sans-serif;
    font-size: 12px; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
    padding: 5px 14px; border-radius: 2px;
    display: inline-block;
}

/* ── TAGS / PILLS ── */
.pill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.06em;
    padding: 3px 10px; border-radius: 2px;
    margin: 3px 3px 3px 0;
    border: 1px solid var(--border2);
    color: var(--muted);
}
.pill-accent { color: var(--accent); border-color: rgba(0,212,255,0.3); background: rgba(0,212,255,0.06); }
.pill-green  { color: var(--green);  border-color: rgba(0,230,118,0.3); background: rgba(0,230,118,0.06); }
.pill-amber  { color: var(--amber);  border-color: rgba(255,171,64,0.3); background: rgba(255,171,64,0.06); }
.pill-red    { color: var(--red);    border-color: rgba(255,69,96,0.3);  background: rgba(255,69,96,0.06); }

/* ── PERSON PILL ── */
.person-row {
    display: flex; align-items: center; gap: 12px;
    padding: 12px 16px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 4px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
.person-row:hover { border-color: var(--border2); }
.avatar {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--bg3);
    border: 1px solid var(--border2);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Rajdhani', sans-serif;
    font-size: 12px; font-weight: 700;
    color: var(--accent); flex-shrink: 0;
}
.person-name { font-weight: 600; font-size: 14px; color: var(--text); }
.person-role { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--muted); margin-top: 1px; }

/* ── OPPORTUNITY CARD ── */
.opp-card {
    display: flex; gap: 14px; align-items: flex-start;
    padding: 14px 18px;
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 4px;
    margin-bottom: 10px;
    transition: border-color 0.2s;
}
.opp-card:hover { border-color: rgba(0,212,255,0.3); }
.opp-num {
    font-family: 'Rajdhani', sans-serif;
    font-size: 28px; font-weight: 700;
    color: var(--border2); line-height: 1;
    flex-shrink: 0; min-width: 28px;
}
.opp-text { font-size: 14px; line-height: 1.6; color: var(--text); }

/* ── OPENING LINE BOX ── */
.opening-box {
    background: linear-gradient(135deg, rgba(0,212,255,0.06), rgba(0,151,184,0.04));
    border: 1px solid rgba(0,212,255,0.25);
    border-radius: 4px;
    padding: 20px 24px;
    font-size: 15px; line-height: 1.7;
    color: var(--text);
    font-style: italic;
    position: relative;
}
.opening-box::before {
    content: '"';
    font-family: 'Rajdhani', sans-serif;
    font-size: 64px; font-weight: 700;
    color: rgba(0,212,255,0.15);
    position: absolute; top: -8px; left: 12px;
    line-height: 1;
}

/* ── INFO / SUCCESS BOXES ── */
.info-box {
    background: rgba(0,212,255,0.05);
    border: 1px solid rgba(0,212,255,0.2);
    border-radius: 4px; padding: 14px 18px;
    font-size: 14px; line-height: 1.6;
    color: var(--text); margin-bottom: 12px;
}
.success-box {
    background: rgba(0,230,118,0.05);
    border: 1px solid rgba(0,230,118,0.2);
    border-radius: 4px; padding: 14px 18px;
    font-size: 14px; line-height: 1.6;
    color: var(--text); margin-bottom: 12px;
}
.warn-box {
    background: rgba(255,171,64,0.05);
    border: 1px solid rgba(255,171,64,0.2);
    border-radius: 4px; padding: 14px 18px;
    font-size: 14px; line-height: 1.6;
    color: var(--text); margin-bottom: 12px;
}

/* ── VACANCY CARD ── */
.vac-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 4px; padding: 16px 20px;
    margin-bottom: 10px;
    display: flex; justify-content: space-between; align-items: flex-start;
}
.vac-title { font-weight: 600; font-size: 15px; margin-bottom: 6px; }
.fem-flag {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px; letter-spacing: 0.08em;
    color: var(--red); background: rgba(255,69,96,0.1);
    border: 1px solid rgba(255,69,96,0.3);
    padding: 3px 9px; border-radius: 2px;
}

/* ── TABLE ── */
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th {
    font-family: 'Rajdhani', sans-serif;
    font-size: 10px; font-weight: 700;
    letter-spacing: 0.15em; text-transform: uppercase;
    color: var(--muted); padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    text-align: left;
}
td { padding: 10px 16px; border-bottom: 1px solid var(--border); color: var(--text); }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,255,255,0.02); }

/* ── DIVIDER ── */
.divider { height: 1px; background: var(--border); margin: 20px 0; }

/* ── CONTENT PAD ── */
.content { padding: 28px 32px; }

/* ── EXPANDER ── */
.streamlit-expanderHeader {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 4px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-size: 13px !important; font-weight: 600 !important;
    letter-spacing: 0.08em !important;
    color: var(--muted) !important;
}
.streamlit-expanderContent {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}

/* ── DOWNLOAD BTN ── */
.stDownloadButton > button {
    background: transparent !important;
    color: var(--accent) !important;
    border: 1px solid rgba(0,212,255,0.4) !important;
    border-radius: 3px !important;
    font-family: 'Rajdhani', sans-serif !important;
    font-weight: 700 !important; font-size: 12px !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
}
.stDownloadButton > button:hover {
    background: rgba(0,212,255,0.08) !important;
    border-color: var(--accent) !important;
}

/* ── SPINNER ── */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

/* ── ANIMATIONS ── */
@keyframes fadeSlide {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}
.animate { animation: fadeSlide 0.35s ease forwards; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.5; }
}
.scanning { animation: pulse 1.5s ease-in-out infinite; }
</style>
""", unsafe_allow_html=True)

# ── CLIENTS ───────────────────────────────────────────────────────────────────
deepseek = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)
FIRECRAWL_KEY = st.secrets["FIRECRAWL_API_KEY"]

# ── FIRECRAWL ─────────────────────────────────────────────────────────────────
def firecrawl_crawl(url, max_pages=12):
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
            json={
                "url": url, "limit": max_pages,
                "scrapeOptions": {"formats": ["markdown"]},
                "includePaths": ["*about*","*team*","*people*","*leadership*",
                                 "*career*","*job*","*project*","*service*","*contact*"],
            },
            timeout=30
        )
        data = resp.json()
        job_id = data.get("id")
        if not job_id:
            return firecrawl_scrape_single(url)

        import time
        for _ in range(20):
            time.sleep(4)
            poll = requests.get(
                f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                timeout=15
            )
            poll_data = poll.json()
            if poll_data.get("status") == "completed":
                pages = poll_data.get("data", [])
                return [{"url": p.get("metadata", {}).get("sourceURL", url),
                         "markdown": p.get("markdown", "")} for p in pages if p.get("markdown")]
            elif poll_data.get("status") == "failed":
                break

        return firecrawl_scrape_single(url)
    except Exception as e:
        return firecrawl_scrape_single(url)


def firecrawl_scrape_single(url):
    try:
        resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
            json={"url": url, "formats": ["markdown"]},
            timeout=20
        )
        data = resp.json()
        md = data.get("data", {}).get("markdown", "")
        return [{"url": url, "markdown": md}] if md else []
    except:
        return []


def build_corpus(pages):
    chunks = []
    for p in pages:
        md = p.get("markdown", "").strip()
        if md:
            chunks.append(f"[PAGE: {p.get('url','')}]\n{md[:5000]}")
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
        "You are a B2B sales analyst for MIDAS IT, which sells FEA/FEM structural analysis software. Extract factual information only. Respond in JSON.",
        f"""From the website content below, extract and return ONLY valid JSON:
{{
  "company_name": "string",
  "tagline": "string or null",
  "locations": ["city1"],
  "founded": "year or null",
  "employee_count": "string or null",
  "overview": ["bullet 1", "bullet 2", "bullet 3"],
  "engineering_capabilities": ["bullet 1"],
  "project_types": ["bridge", "tunnel"],
  "software_mentioned": ["any FEA/CAD/BIM tools"],
  "people": [{{"name": "Full Name", "role": "Job Title", "tier": "Director|Senior|Engineer"}}],
  "open_roles": [{{"title": "Job title", "skills": ["skill1"], "fem_mentioned": true}}],
  "confidence": "High|Medium|Low"
}}
Return ONLY the JSON. No explanation, no markdown.
Website content:
{corpus}"""
    )


def analyze_sales(corpus, company_json):
    return ask_deepseek(
        "You are a senior B2B sales strategist for MIDAS IT, which sells FEA/FEM structural engineering software (MIDAS Civil, MIDAS Gen, MIDAS FEA NX). Be specific and actionable.",
        f"""Based on this company profile and website data, produce a sales strategy.
Company data:
{company_json}

Website content (excerpt):
{corpus[:8000]}

Return ONLY valid JSON:
{{
  "fem_opportunities": ["specific use case 1"],
  "pain_points": ["pain 1"],
  "entry_point": "Who to approach first and why",
  "value_positioning": "How to position MIDAS software for this company",
  "likely_objections": ["objection 1"],
  "first_conversation_angle": "Opening angle",
  "hiring_signals": ["signal 1"],
  "expansion_signals": ["signal 1"],
  "pre_meeting_mention": ["thing 1", "thing 2", "thing 3"],
  "smart_questions": ["question 1", "question 2", "question 3"],
  "opening_line": "One strong opening line for the first call",
  "overall_score": "Hot|Warm|Cold",
  "score_reason": "1-sentence reason"
}}"""
    )


# ── HELPERS ───────────────────────────────────────────────────────────────────
def safe_json(text):
    try:
        return json.loads(re.sub(r"```json|```", "", text).strip())
    except:
        return {}


def initials(name):
    return "".join(p[0] for p in name.split()[:2]).upper()


def linkedin_url(name):
    return f"https://www.linkedin.com/search/results/people/?keywords={name.replace(' ', '%20')}"


def score_cls(score):
    return {"Hot": "score-hot", "Warm": "score-warm", "Cold": "score-cold"}.get(score, "score-cold")


def card_cls(score):
    return {"Hot": "card-red", "Warm": "card-amber", "Cold": ""}.get(score, "")


def export_markdown(company, cd, sd):
    lines = [f"# MIDAS Sales Intel: {company}", f"*{datetime.now().strftime('%d %b %Y %H:%M')}*\n"]
    lines += ["## Overview"] + [f"- {b}" for b in cd.get("overview", [])]
    lines += ["\n## Capabilities"] + [f"- {b}" for b in cd.get("engineering_capabilities", [])]
    lines += ["\n## People"] + [f"- **{p['name']}** — {p.get('role','')}" for p in cd.get("people", [])]
    lines += ["\n## FEM Opportunities"] + [f"- {o}" for o in sd.get("fem_opportunities", [])]
    lines += [f"\n## Sales Strategy\n**Entry:** {sd.get('entry_point','')}\n**Value:** {sd.get('value_positioning','')}\n**Opening:** {sd.get('opening_line','')}"]
    lines += ["\n## Smart Questions"] + [f"- {q}" for q in sd.get("smart_questions", [])]
    return "\n".join(lines)


# ── TOP NAV ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-nav">
    <div class="nav-logo">MIDAS<span>·</span>INTEL</div>
    <div style="display:flex;align-items:center;gap:16px;">
        <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);">Manoj | MIDAS IT</div>
        <div class="nav-badge">Sales Intelligence v2</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── SEARCH BAR ────────────────────────────────────────────────────────────────
st.markdown('<div class="content" style="padding-bottom:0">', unsafe_allow_html=True)

col1, col2 = st.columns([5, 1])
with col1:
    website = st.text_input(
        "", placeholder="https://target-company.com",
        label_visibility="collapsed"
    )
with col2:
    run = st.button("ANALYSE →")

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('<div class="divider" style="margin:0"></div>', unsafe_allow_html=True)

# ── RUN ANALYSIS ─────────────────────────────────────────────────────────────
if run:
    if not website:
        st.markdown('<div class="content"><div class="warn-box">⚠ Enter a website URL to continue.</div></div>', unsafe_allow_html=True)
        st.stop()

    if not website.startswith("http"):
        website = "https://" + website

    st.markdown('<div class="content">', unsafe_allow_html=True)

    progress = st.progress(0, text="")
    status   = st.empty()

    status.markdown('<div class="scanning" style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--accent);letter-spacing:0.1em;">▶ CRAWLING WEBSITE WITH FIRECRAWL...</div>', unsafe_allow_html=True)
    pages = firecrawl_crawl(website)
    progress.progress(30)

    if not pages:
        st.markdown('<div class="warn-box">⚠ Could not extract content from this website.</div>', unsafe_allow_html=True)
        st.stop()

    status.markdown('<div class="scanning" style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--accent);letter-spacing:0.1em;">▶ BUILDING CONTENT CORPUS...</div>', unsafe_allow_html=True)
    corpus = build_corpus(pages)
    progress.progress(45)

    status.markdown('<div class="scanning" style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--accent);letter-spacing:0.1em;">▶ EXTRACTING COMPANY PROFILE...</div>', unsafe_allow_html=True)
    company_raw  = analyze_company(corpus)
    company_data = safe_json(company_raw)
    progress.progress(70)

    status.markdown('<div class="scanning" style="font-family:\'JetBrains Mono\',monospace;font-size:12px;color:var(--accent);letter-spacing:0.1em;">▶ GENERATING SALES STRATEGY...</div>', unsafe_allow_html=True)
    sales_raw  = analyze_sales(corpus, company_raw)
    sales_data = safe_json(sales_raw)
    progress.progress(100)

    status.empty()
    progress.empty()

    st.markdown('</div>', unsafe_allow_html=True)

    # ── HEADER BAND ───────────────────────────────────────────────────────
    company_name = company_data.get("company_name", website)
    score        = sales_data.get("overall_score", "Warm")
    score_reason = sales_data.get("score_reason", "")
    locs         = " · ".join(company_data.get("locations", [])) or "—"
    emp          = company_data.get("employee_count") or "—"
    conf         = company_data.get("confidence", "Medium")
    n_people     = len(company_data.get("people", []))
    n_roles      = len(company_data.get("open_roles", []))
    n_fem        = len(sales_data.get("fem_opportunities", []))
    n_pages      = len(pages)

    st.markdown(f"""
    <div style="background:var(--bg2);border-bottom:1px solid var(--border);padding:24px 32px 0;">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:20px;">
            <div>
                <div style="font-family:'Rajdhani',sans-serif;font-size:28px;font-weight:700;
                     color:var(--text);margin-bottom:6px;">{company_name}</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--muted);margin-bottom:10px;">
                    📍 {locs} &nbsp;·&nbsp; 👥 {emp} &nbsp;·&nbsp; Confidence:
                    <span style="color:var(--accent)">{conf}</span>
                </div>
                <div style="font-size:13px;color:var(--muted);max-width:600px;">{score_reason}</div>
            </div>
            <div style="text-align:right;">
                <div class="score-badge {score_cls(score)}" style="font-size:15px;padding:8px 20px;margin-bottom:8px;">
                    {score.upper()} LEAD
                </div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--muted);">
                    {datetime.now().strftime('%d %b %Y %H:%M')}
                </div>
            </div>
        </div>

        <div class="metric-grid">
            <div class="metric-cell">
                <div class="metric-val">{n_people}</div>
                <div class="metric-lbl">People Identified</div>
            </div>
            <div class="metric-cell">
                <div class="metric-val">{n_fem}</div>
                <div class="metric-lbl">FEM Opportunities</div>
            </div>
            <div class="metric-cell">
                <div class="metric-val">{n_roles}</div>
                <div class="metric-lbl">Open Roles</div>
            </div>
            <div class="metric-cell">
                <div class="metric-val">{n_pages}</div>
                <div class="metric-lbl">Pages Crawled</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "🏢  Company", "👥  People", "💡  FEM Opps",
        "🎯  Strategy", "📋  Vacancies", "📤  Export"
    ])

    # ── TAB 1: COMPANY ────────────────────────────────────────────────────
    with t1:
        st.markdown('<div class="content">', unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 2])

        with col_a:
            st.markdown('<div class="sec-head">Company Overview</div>', unsafe_allow_html=True)
            for b in company_data.get("overview", ["No data found"]):
                st.markdown(f"""
                <div class="card-accent animate" style="margin-bottom:8px;padding:12px 16px;">
                    <div style="font-size:14px;line-height:1.6;">{b}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown('<div class="sec-head" style="margin-top:24px;">Engineering Capabilities</div>', unsafe_allow_html=True)
            for b in company_data.get("engineering_capabilities", ["Not found"]):
                st.markdown(f"<div style='font-size:14px;padding:6px 0;border-bottom:1px solid var(--border);color:var(--text);'>→ {b}</div>", unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="sec-head">Project Types</div>', unsafe_allow_html=True)
            pts = company_data.get("project_types", [])
            if pts:
                pills = " ".join(f'<span class="pill pill-accent">{p}</span>' for p in pts)
                st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:var(--muted);font-size:13px;'>None detected</div>", unsafe_allow_html=True)

            st.markdown('<div class="sec-head" style="margin-top:24px;">Software & Tools Detected</div>', unsafe_allow_html=True)
            sw = company_data.get("software_mentioned", [])
            if sw:
                pills = " ".join(f'<span class="pill pill-amber">{s}</span>' for s in sw)
                st.markdown(f"<div>{pills}</div>", unsafe_allow_html=True)
                st.markdown("<div style='font-size:12px;color:var(--muted);margin-top:8px;'>Existing tools to position MIDAS against</div>", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="success-box" style="font-size:13px;">
                    ✦ No competing software detected — clean opportunity to introduce MIDAS as first FEA tool
                </div>""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 2: PEOPLE ─────────────────────────────────────────────────────
    with t2:
        st.markdown('<div class="content">', unsafe_allow_html=True)
        people = company_data.get("people", [])
        if people:
            for tier, icon in [("Director", "◈"), ("Senior", "◆"), ("Engineer", "◇")]:
                tier_people = [p for p in people if p.get("tier") == tier]
                if tier_people:
                    st.markdown(f'<div class="sec-head">{icon} {tier}s</div>', unsafe_allow_html=True)
                    for p in tier_people:
                        name = p.get("name", "")
                        role = p.get("role", "")
                        li   = linkedin_url(name)
                        ini  = initials(name)
                        st.markdown(f"""
                        <div class="person-row animate">
                            <div class="avatar">{ini}</div>
                            <div style="flex:1;">
                                <div class="person-name">{name}</div>
                                <div class="person-role">{role}</div>
                            </div>
                            <a href="{li}" target="_blank" style="font-family:'JetBrains Mono',monospace;
                               font-size:10px;color:var(--accent);text-decoration:none;
                               border:1px solid rgba(0,212,255,0.3);padding:4px 10px;border-radius:2px;
                               white-space:nowrap;letter-spacing:0.05em;">
                                LinkedIn ↗
                            </a>
                        </div>""", unsafe_allow_html=True)
                    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        else:
            st.markdown('<div class="warn-box">No people identified — the site may not have a team page. Try searching LinkedIn manually for senior engineers at this company.</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 3: FEM OPPORTUNITIES ──────────────────────────────────────────
    with t3:
        st.markdown('<div class="content">', unsafe_allow_html=True)
        col_a, col_b = st.columns([3, 2])

        with col_a:
            st.markdown('<div class="sec-head">FEM / FEA Application Opportunities</div>', unsafe_allow_html=True)
            for i, opp in enumerate(sales_data.get("fem_opportunities", ["None identified"]), 1):
                st.markdown(f"""
                <div class="opp-card animate">
                    <div class="opp-num">0{i}</div>
                    <div class="opp-text">{opp}</div>
                </div>""", unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="sec-head">Hiring Signals</div>', unsafe_allow_html=True)
            for sig in sales_data.get("hiring_signals", []):
                st.markdown(f'<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;"><span style="color:var(--green);">▲</span> {sig}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-head" style="margin-top:20px;">Expansion Signals</div>', unsafe_allow_html=True)
            for sig in sales_data.get("expansion_signals", []):
                st.markdown(f'<div style="padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;"><span style="color:var(--amber);">◆</span> {sig}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 4: SALES STRATEGY ─────────────────────────────────────────────
    with t4:
        st.markdown('<div class="content">', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown('<div class="sec-head">Entry Point</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="info-box">{sales_data.get("entry_point","Not determined")}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-head" style="margin-top:20px;">Value Positioning</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="success-box">{sales_data.get("value_positioning","Not determined")}</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-head" style="margin-top:20px;">Likely Objections</div>', unsafe_allow_html=True)
            for obj in sales_data.get("likely_objections", []):
                st.markdown(f"""
                <div class="card-accent card-red animate" style="margin-bottom:8px;padding:10px 14px;">
                    <div style="font-size:13px;">⚠ {obj}</div>
                </div>""", unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="sec-head">Pre-Meeting Cheat Sheet</div>', unsafe_allow_html=True)
            st.markdown("<div style='font-family:\"JetBrains Mono\",monospace;font-size:10px;color:var(--muted);letter-spacing:0.1em;margin-bottom:8px;'>3 THINGS TO MENTION</div>", unsafe_allow_html=True)
            for m in sales_data.get("pre_meeting_mention", []):
                st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;'><span style='color:var(--green);'>✓</span> {m}</div>", unsafe_allow_html=True)

            st.markdown("<div style='font-family:\"JetBrains Mono\",monospace;font-size:10px;color:var(--muted);letter-spacing:0.1em;margin:20px 0 8px;'>3 SMART QUESTIONS</div>", unsafe_allow_html=True)
            for q in sales_data.get("smart_questions", []):
                st.markdown(f"<div style='padding:8px 0;border-bottom:1px solid var(--border);font-size:13px;'><span style='color:var(--accent);'>?</span> {q}</div>", unsafe_allow_html=True)

            st.markdown('<div class="sec-head" style="margin-top:24px;">Opening Line</div>', unsafe_allow_html=True)
            opening = sales_data.get("opening_line", "")
            if opening:
                st.markdown(f'<div class="opening-box">{opening}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 5: VACANCIES ──────────────────────────────────────────────────
    with t5:
        st.markdown('<div class="content">', unsafe_allow_html=True)
        roles = company_data.get("open_roles", [])
        if roles:
            fem_count = sum(1 for r in roles if r.get("fem_mentioned"))
            if fem_count:
                st.markdown(f'<div class="success-box" style="margin-bottom:20px;">🎯 {fem_count} role(s) explicitly mention FEM/FEA — strong buying signal</div>', unsafe_allow_html=True)

            st.markdown('<div class="sec-head">Open Roles</div>', unsafe_allow_html=True)
            for role in roles:
                fem_flag = '<span class="fem-flag">FEM MENTIONED</span>' if role.get("fem_mentioned") else ""
                skills   = " ".join(f'<span class="pill">{s}</span>' for s in role.get("skills", []))
                st.markdown(f"""
                <div class="vac-card animate">
                    <div style="flex:1;">
                        <div class="vac-title">{role.get('title','Unknown role')}</div>
                        <div>{skills}</div>
                    </div>
                    {fem_flag}
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">No relevant vacancies found on this website.<br><span style="font-size:12px;color:var(--muted);">This may mean hiring is stable or jobs are posted on third-party boards.</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # ── TAB 6: EXPORT ─────────────────────────────────────────────────────
    with t6:
        st.markdown('<div class="content">', unsafe_allow_html=True)
        st.markdown('<div class="sec-head">Export Dossier</div>', unsafe_allow_html=True)

        md_out = export_markdown(company_name, company_data, sales_data)
        fname  = f"MIDAS_Intel_{company_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.md"
        st.download_button("📥  Download as Markdown", data=md_out, file_name=fname, mime="text/markdown")

        st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="sec-head">Raw JSON</div>', unsafe_allow_html=True)
        with st.expander("Company data"):
            st.json(company_data)
        with st.expander("Sales strategy"):
            st.json(sales_data)
        st.markdown('</div>', unsafe_allow_html=True)
