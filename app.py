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
    st.set_page_config(page_title="MIDAS Intel", page_icon="🔐")
    st.title("🔐 Secure Access")
    code = st.text_input("Enter passcode", type="password")
    if st.button("Unlock"):
        if code == PASSCODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect passcode")
    st.stop()

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MIDAS Sales Intelligence", layout="wide", page_icon="🚀")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #ffffff;
    color: #1a1a1a;
}

.stApp { background-color: #ffffff; }

/* Top bar label */
.top-label {
    position: fixed; top: 14px; right: 20px;
    font-size: 13px; font-weight: 600;
    color: #1a1a1a; z-index: 9999;
    background: #f0f0f0; padding: 4px 12px;
    border-radius: 20px;
}

/* Section cards */
.section-card {
    background: #fafafa;
    border: 1px solid #e8e8e8;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 16px;
}

.section-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 12px;
}

/* Signal badges */
.badge {
    display: inline-block;
    font-size: 11px; font-weight: 600;
    padding: 3px 10px; border-radius: 20px;
    margin: 3px 3px 3px 0;
}
.badge-high   { background: #dcfce7; color: #166534; }
.badge-medium { background: #fef9c3; color: #854d0e; }
.badge-low    { background: #fee2e2; color: #991b1b; }
.badge-blue   { background: #dbeafe; color: #1e40af; }
.badge-gray   { background: #f3f4f6; color: #374151; }

/* Metric cards */
.metric-row { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.metric-box {
    flex: 1; min-width: 120px;
    background: #f8faff;
    border: 1px solid #e0e7ff;
    border-radius: 8px;
    padding: 14px 16px;
    text-align: center;
}
.metric-val { font-size: 24px; font-weight: 700; color: #1e40af; }
.metric-lbl { font-size: 11px; color: #888; margin-top: 2px; }

/* Table */
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th { background: #f3f4f6; padding: 8px 12px; text-align: left; font-weight: 600; font-size: 12px; color: #555; }
td { padding: 8px 12px; border-bottom: 1px solid #f0f0f0; }
tr:hover td { background: #fafafa; }

/* Person pill */
.person-pill {
    display: inline-flex; align-items: center; gap: 8px;
    background: #f0f4ff; border: 1px solid #c7d7ff;
    border-radius: 6px; padding: 6px 12px;
    margin: 4px; font-size: 13px;
}
.person-avatar {
    width: 26px; height: 26px; border-radius: 50%;
    background: #1e40af; color: white;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 700; flex-shrink: 0;
}

/* Buttons */
.stButton > button {
    background: #1e40af !important;
    color: white !important;
    font-weight: 600 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-size: 14px !important;
    width: 100%;
}
.stButton > button:hover { background: #1d3a9e !important; }

/* Input */
.stTextInput > div > div > input {
    border: 1.5px solid #e0e0e0 !important;
    border-radius: 8px !important;
    padding: 10px 14px !important;
    font-size: 15px !important;
    color: #1a1a1a !important;
    background: white !important;
    caret-color: black !important;
}
.stTextInput > div > div > input:focus {
    border-color: #1e40af !important;
    box-shadow: 0 0 0 3px rgba(30,64,175,0.1) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 2px solid #f0f0f0; }
.stTabs [data-baseweb="tab"] {
    font-size: 13px; font-weight: 600;
    padding: 8px 16px; border-radius: 6px 6px 0 0;
}
.stTabs [aria-selected="true"] { background: #1e40af; color: white !important; }

/* Divider */
hr { border: none; border-top: 1px solid #f0f0f0; margin: 20px 0; }

/* Confidence pill */
.conf { font-size: 11px; padding: 2px 8px; border-radius: 10px; font-weight: 600; margin-left: 6px; }
.conf-high   { background: #dcfce7; color: #166534; }
.conf-medium { background: #fef9c3; color: #854d0e; }
.conf-low    { background: #fee2e2; color: #991b1b; }
</style>

<div class="top-label">Manoj | MIDAS IT</div>
""", unsafe_allow_html=True)

# ── CLIENTS ───────────────────────────────────────────────────────────────────
deepseek = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)
FIRECRAWL_KEY = st.secrets["FIRECRAWL_API_KEY"]

# ── FIRECRAWL ─────────────────────────────────────────────────────────────────
def firecrawl_crawl(url, max_pages=12):
    """Use Firecrawl to crawl the site and return markdown content."""
    try:
        # Start crawl job
        resp = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            headers={"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"},
            json={
                "url": url,
                "limit": max_pages,
                "scrapeOptions": {"formats": ["markdown"]},
                "includePaths": ["*about*", "*team*", "*people*", "*leadership*",
                                 "*career*", "*job*", "*project*", "*service*", "*contact*"],
            },
            timeout=30
        )
        data = resp.json()
        job_id = data.get("id")
        if not job_id:
            return firecrawl_scrape_single(url)

        # Poll for results
        import time
        for _ in range(20):
            time.sleep(4)
            poll = requests.get(
                f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                headers={"Authorization": f"Bearer {FIRECRAWL_KEY}"},
                timeout=15
            )
            poll_data = poll.json()
            status = poll_data.get("status")
            if status == "completed":
                pages = poll_data.get("data", [])
                return [{"url": p.get("metadata", {}).get("sourceURL", url),
                         "markdown": p.get("markdown", "")} for p in pages if p.get("markdown")]
            elif status == "failed":
                break

        return firecrawl_scrape_single(url)

    except Exception as e:
        st.warning(f"Firecrawl crawl failed ({e}), falling back to single-page scrape.")
        return firecrawl_scrape_single(url)


def firecrawl_scrape_single(url):
    """Scrape a single page via Firecrawl."""
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


# ── TEXT PREP ─────────────────────────────────────────────────────────────────
def build_corpus(pages):
    """Merge all page markdown into a single clean string, tagged by URL."""
    chunks = []
    for p in pages:
        url = p.get("url", "")
        md = p.get("markdown", "").strip()
        if md:
            chunks.append(f"[PAGE: {url}]\n{md[:5000]}")
    return "\n\n---\n\n".join(chunks)[:40000]


# ── AI ANALYSIS (split into focused calls) ───────────────────────────────────
def ask_deepseek(system, user, max_tokens=2000):
    resp = deepseek.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        temperature=0.1,
        max_tokens=max_tokens
    )
    return resp.choices[0].message.content.strip()


def analyze_company(corpus):
    return ask_deepseek(
        "You are a B2B sales analyst for MIDAS IT, which sells FEA/FEM structural analysis software. Extract factual information only. Respond in JSON.",
        f"""From the website content below, extract and return ONLY valid JSON with these keys:

{{
  "company_name": "string",
  "tagline": "string or null",
  "locations": ["city1", "city2"],
  "founded": "year or null",
  "employee_count": "string or null",
  "overview": ["bullet 1", "bullet 2", "bullet 3"],
  "engineering_capabilities": ["bullet 1", ...],
  "project_types": ["bridge", "tunnel", ...],
  "software_mentioned": ["any FEA/CAD/BIM tools mentioned"],
  "people": [
    {{"name": "Full Name", "role": "Job Title", "tier": "Director|Senior|Engineer"}}
  ],
  "open_roles": [
    {{"title": "Job title", "skills": ["skill1"], "fem_mentioned": true}}
  ],
  "confidence": "High|Medium|Low"
}}

Return ONLY the JSON object. No explanation, no markdown.

Website content:
{corpus}"""
    )


def analyze_sales(corpus, company_json):
    return ask_deepseek(
        "You are a senior B2B sales strategist for MIDAS IT, which sells FEA/FEM structural engineering software (MIDAS Civil, MIDAS Gen, MIDAS FEA NX). Be specific and actionable.",
        f"""Based on this company profile and website data, produce a sales strategy for MIDAS IT.

Company data:
{company_json}

Website content (excerpt):
{corpus[:8000]}

Return ONLY valid JSON with exactly these keys:
{{
  "fem_opportunities": ["specific use case 1", ...],
  "pain_points": ["pain 1", ...],
  "entry_point": "Who to approach first and why",
  "value_positioning": "How to position MIDAS software specifically for this company",
  "likely_objections": ["objection 1", ...],
  "first_conversation_angle": "Opening line / angle",
  "hiring_signals": ["signal 1", ...],
  "expansion_signals": ["signal 1", ...],
  "pre_meeting_mention": ["thing to mention 1", "thing to mention 2", "thing to mention 3"],
  "smart_questions": ["question 1", "question 2", "question 3"],
  "opening_line": "One strong opening line for the first call",
  "overall_score": "Hot|Warm|Cold",
  "score_reason": "1-sentence reason"
}}"""
    )


# ── HELPERS ───────────────────────────────────────────────────────────────────
def safe_json(text):
    try:
        text = re.sub(r"```json|```", "", text).strip()
        return json.loads(text)
    except:
        return {}


def initials(name):
    parts = name.split()
    return ("".join(p[0] for p in parts[:2])).upper()


def linkedin_url(name):
    q = name.replace(" ", "%20")
    return f"https://www.linkedin.com/search/results/people/?keywords={q}"


def score_badge(score):
    colors = {"Hot": "badge-high", "Warm": "badge-medium", "Cold": "badge-low"}
    return colors.get(score, "badge-gray")


def export_markdown(company, company_data, sales_data):
    lines = [f"# MIDAS Sales Intelligence: {company}", f"*Generated {datetime.now().strftime('%d %b %Y %H:%M')}*\n"]

    lines.append("## Company Overview")
    for b in company_data.get("overview", []):
        lines.append(f"- {b}")

    lines.append("\n## Engineering Capabilities")
    for b in company_data.get("engineering_capabilities", []):
        lines.append(f"- {b}")

    lines.append("\n## Key People")
    for p in company_data.get("people", []):
        lines.append(f"- **{p['name']}** — {p.get('role','')}")

    lines.append("\n## FEM Opportunities")
    for b in sales_data.get("fem_opportunities", []):
        lines.append(f"- {b}")

    lines.append("\n## Sales Strategy")
    lines.append(f"**Entry Point:** {sales_data.get('entry_point','')}")
    lines.append(f"**Value Positioning:** {sales_data.get('value_positioning','')}")
    lines.append(f"**Opening Line:** {sales_data.get('opening_line','')}")

    lines.append("\n## Pre-Meeting Cheat Sheet")
    for q in sales_data.get("smart_questions", []):
        lines.append(f"- Q: {q}")

    return "\n".join(lines)


# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("## 🚀 MIDAS Sales Intelligence")
st.markdown("*Enter a prospect's website to generate a full pre-sales dossier*")

col1, col2 = st.columns([4, 1])
with col1:
    website = st.text_input("", placeholder="https://example-engineering.com", label_visibility="collapsed")
with col2:
    run = st.button("Analyse →")

if run:
    if not website:
        st.warning("Please enter a website URL.")
        st.stop()

    if not website.startswith("http"):
        website = "https://" + website

    # ── CRAWL ─────────────────────────────────────────────────────────────
    progress = st.progress(0, text="🔍 Crawling website with Firecrawl...")
    pages = firecrawl_crawl(website)

    if not pages:
        st.error("Could not extract any content from this website.")
        st.stop()

    progress.progress(30, text="📄 Building content corpus...")
    corpus = build_corpus(pages)

    # ── ANALYSE ───────────────────────────────────────────────────────────
    progress.progress(50, text="🧠 Extracting company profile...")
    company_raw = analyze_company(corpus)
    company_data = safe_json(company_raw)

    progress.progress(75, text="💡 Generating sales strategy...")
    sales_raw = analyze_sales(corpus, company_raw)
    sales_data = safe_json(sales_raw)

    progress.progress(100, text="✅ Done!")
    progress.empty()

    company_name = company_data.get("company_name", website)

    # ── HEADER ────────────────────────────────────────────────────────────
    score = sales_data.get("overall_score", "Warm")
    score_reason = sales_data.get("score_reason", "")

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin:24px 0 8px;">
        <div style="font-size:24px;font-weight:700;">{company_name}</div>
        <span class="badge {score_badge(score)}" style="font-size:13px;padding:5px 14px;">{score} Lead</span>
    </div>
    <div style="font-size:13px;color:#666;margin-bottom:24px;">{score_reason}</div>
    """, unsafe_allow_html=True)

    # ── METRICS ROW ───────────────────────────────────────────────────────
    locs = ", ".join(company_data.get("locations", [])) or "—"
    emp  = company_data.get("employee_count") or "—"
    n_people = len(company_data.get("people", []))
    n_roles  = len(company_data.get("open_roles", []))
    n_fem    = len(sales_data.get("fem_opportunities", []))

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-box"><div class="metric-val">{n_people}</div><div class="metric-lbl">People found</div></div>
        <div class="metric-box"><div class="metric-val">{n_roles}</div><div class="metric-lbl">Open roles</div></div>
        <div class="metric-box"><div class="metric-val">{n_fem}</div><div class="metric-lbl">FEM opportunities</div></div>
        <div class="metric-box"><div class="metric-val">{len(pages)}</div><div class="metric-lbl">Pages crawled</div></div>
    </div>
    <div style="font-size:12px;color:#888;margin-bottom:20px;">📍 {locs} &nbsp;·&nbsp; 👥 {emp}</div>
    """, unsafe_allow_html=True)

    # ── TABS ──────────────────────────────────────────────────────────────
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "🏢 Company", "👥 People", "💡 FEM Opps", "🎯 Sales Strategy", "📋 Vacancies", "📤 Export"
    ])

    # ── TAB 1: COMPANY ────────────────────────────────────────────────────
    with t1:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown('<div class="section-title">Overview</div>', unsafe_allow_html=True)
            for b in company_data.get("overview", ["Not found"]):
                st.markdown(f"• {b}")

            st.markdown('<div class="section-title" style="margin-top:20px;">Engineering Capabilities</div>', unsafe_allow_html=True)
            for b in company_data.get("engineering_capabilities", ["Not found"]):
                st.markdown(f"• {b}")

        with col_b:
            st.markdown('<div class="section-title">Project Types</div>', unsafe_allow_html=True)
            for p in company_data.get("project_types", ["Not found"]):
                st.markdown(f'<span class="badge badge-blue">{p}</span>', unsafe_allow_html=True)

            st.markdown('<div class="section-title" style="margin-top:20px;">Software / Tools Mentioned</div>', unsafe_allow_html=True)
            sw = company_data.get("software_mentioned", [])
            if sw:
                for s in sw:
                    st.markdown(f'<span class="badge badge-gray">{s}</span>', unsafe_allow_html=True)
            else:
                st.markdown("*None detected — good opportunity to introduce MIDAS*")

    # ── TAB 2: PEOPLE ─────────────────────────────────────────────────────
    with t2:
        people = company_data.get("people", [])
        if people:
            # Group by tier
            for tier in ["Director", "Senior", "Engineer"]:
                tier_people = [p for p in people if p.get("tier") == tier]
                if tier_people:
                    st.markdown(f'<div class="section-title">{tier}s</div>', unsafe_allow_html=True)
                    for p in tier_people:
                        name = p.get("name", "")
                        role = p.get("role", "")
                        li   = linkedin_url(name)
                        ini  = initials(name)
                        st.markdown(f"""
                        <div class="person-pill">
                            <div class="person-avatar">{ini}</div>
                            <div>
                                <div style="font-weight:600;">{name}</div>
                                <div style="font-size:11px;color:#666;">{role}</div>
                            </div>
                            <a href="{li}" target="_blank" style="margin-left:8px;font-size:11px;color:#1e40af;text-decoration:none;">LinkedIn ↗</a>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
        else:
            st.info("No people identified. The site may not have a team page.")

    # ── TAB 3: FEM OPPORTUNITIES ──────────────────────────────────────────
    with t3:
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown('<div class="section-title">FEM / FEA Application Opportunities</div>', unsafe_allow_html=True)
            for i, opp in enumerate(sales_data.get("fem_opportunities", ["Not identified"]), 1):
                st.markdown(f"""
                <div class="section-card" style="margin-bottom:10px;">
                    <div style="font-size:11px;color:#1e40af;font-weight:700;margin-bottom:4px;">0{i}</div>
                    <div style="font-size:14px;">{opp}</div>
                </div>
                """, unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="section-title">Key Sales Signals</div>', unsafe_allow_html=True)
            for sig in sales_data.get("hiring_signals", []) + sales_data.get("expansion_signals", []):
                st.markdown(f'<span class="badge badge-high">📈 {sig}</span><br>', unsafe_allow_html=True)

    # ── TAB 4: SALES STRATEGY ─────────────────────────────────────────────
    with t4:
        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown('<div class="section-title">Entry Point</div>', unsafe_allow_html=True)
            st.info(sales_data.get("entry_point", "Not determined"))

            st.markdown('<div class="section-title" style="margin-top:16px;">Value Positioning</div>', unsafe_allow_html=True)
            st.success(sales_data.get("value_positioning", "Not determined"))

            st.markdown('<div class="section-title" style="margin-top:16px;">Likely Objections</div>', unsafe_allow_html=True)
            for obj in sales_data.get("likely_objections", []):
                st.markdown(f"⚠️ {obj}")

        with col_b:
            st.markdown('<div class="section-title">Pre-Meeting Cheat Sheet</div>', unsafe_allow_html=True)
            st.markdown("**3 Things to Mention:**")
            for m in sales_data.get("pre_meeting_mention", []):
                st.markdown(f"✅ {m}")

            st.markdown("**3 Smart Questions to Ask:**")
            for q in sales_data.get("smart_questions", []):
                st.markdown(f"❓ {q}")

            st.markdown('<div class="section-title" style="margin-top:16px;">Opening Line</div>', unsafe_allow_html=True)
            opening = sales_data.get("opening_line", "")
            if opening:
                st.markdown(f"""
                <div style="background:#1e40af;color:white;border-radius:8px;padding:16px;
                     font-size:14px;line-height:1.6;font-style:italic;">
                    "{opening}"
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 5: VACANCIES ──────────────────────────────────────────────────
    with t5:
        roles = company_data.get("open_roles", [])
        if roles:
            for role in roles:
                fem_flag = "🔴 FEM Mentioned" if role.get("fem_mentioned") else ""
                skills = ", ".join(role.get("skills", [])) or "—"
                st.markdown(f"""
                <div class="section-card">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="font-weight:600;font-size:15px;">{role.get('title','Unknown role')}</div>
                        <span style="color:#dc2626;font-size:12px;font-weight:600;">{fem_flag}</span>
                    </div>
                    <div style="font-size:12px;color:#666;margin-top:6px;">Skills: {skills}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            fem_roles = [r for r in roles if r.get("fem_mentioned")]
            if fem_roles:
                st.success(f"🎯 {len(fem_roles)} role(s) mention FEM/FEA — strong signal this company uses or needs analysis software.")
        else:
            st.info("No relevant vacancies found on this website.")

    # ── TAB 6: EXPORT ─────────────────────────────────────────────────────
    with t6:
        st.markdown("### Export this dossier")
        md_export = export_markdown(company_name, company_data, sales_data)
        st.download_button(
            "📥 Download as Markdown",
            data=md_export,
            file_name=f"MIDAS_Intel_{company_name.replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )

        st.markdown("---")
        st.markdown("**Raw JSON (for CRM / further processing)**")
        with st.expander("Company data JSON"):
            st.json(company_data)
        with st.expander("Sales strategy JSON"):
            st.json(sales_data)
