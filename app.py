import streamlit as st
from openai import OpenAI
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# -------------------------------
# 🔐 AUTH SYSTEM
# -------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

PASSCODE = "5487"  # 🔥 change this

if not st.session_state.authenticated:
    st.title("🔐 Secure Access")

    code = st.text_input("Enter 4-digit passcode", type="password")

    if st.button("Unlock"):
        if code == PASSCODE:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect passcode")

    st.stop()
# -------------------------------
# PAGE CONFIG + WHITE UI
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence Tool", layout="wide")

st.markdown("""
<style>
.stApp { background-color: white !important; color: black !important; }
html, body, [class*="css"] { color: black !important; }

.stTextInput > div > div > input {
    background-color: white !important;
    color: black !important;
    border: 1px solid #ccc !important;
}

button {
    background-color: #f0f0f0 !important;
    color: black !important;
    border: 1px solid #ccc !important;
}

pre, code {
    background-color: #f5f5f5 !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

/* INPUT BOX FIX (with visible cursor) */
.stTextInput > div > div > input {
    background-color: white !important;
    color: black !important;
    border: 1px solid #ccc !important;
    caret-color: black !important;   /* 🔥 THIS FIXES THE CURSOR */
    font-size: 16px;
    padding: 10px;
}

/* Focus state (when clicking input) */
.stTextInput > div > div > input:focus {
    border: 1px solid #888 !important;
    outline: none !important;
    box-shadow: 0 0 0 1px #aaa !important;
}

/* Placeholder text */
.stTextInput > div > div > input::placeholder {
    color: #888 !important;
}

/* Smooth typing feel */
input {
    transition: all 0.2s ease-in-out;
}

</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="
    position: fixed;
    top: 70px;   /* 🔥 move below Streamlit header */
    right: 25px;
    font-size: 14px;
    font-weight: 600;
    color: black;
    z-index: 9999;
">
    Manoj | MIDAS IT
</div>
""", unsafe_allow_html=True)
# -------------------------------
# INIT
# -------------------------------
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# -------------------------------
# SCRAPER
# -------------------------------
def scrape_page(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return ""

        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text(separator="\n")

        return text[:6000]
    except:
        return ""

# -------------------------------
# LINK DISCOVERY
# -------------------------------
def get_links(base_url):
    links = set()

    try:
        res = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")

        domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full = urljoin(base_url, href)

            if urlparse(full).netloc == domain:
                links.add(full)
    except:
        pass

    return list(links)

# -------------------------------
# CRAWL
# -------------------------------
def crawl_site(base_url):
    pages = []

    homepage = scrape_page(base_url)
    if homepage:
        pages.append({"url": base_url, "markdown": homepage})

    links = get_links(base_url)

    # 🔥 improved priority (important)
    priority = [
        "team", "people", "our-team",
        "leadership", "directors",
        "about", "staff",
        # 🔥 NEW (jobs)
        "careers", "career", "jobs",
        "vacancies", "join-us", "work-with-us"
    ]

    sorted_links = sorted(
        links,
        key=lambda x: any(p in x.lower() for p in priority),
        reverse=True
    )

    for link in sorted_links[:10]:
        text = scrape_page(link)

        if text:
            pages.append({"url": link, "markdown": text})

    return pages

# -------------------------------
# COMPANY NAME
# -------------------------------
def extract_company_name(pages, url):
    for page in pages:
        for line in page["markdown"].split("\n")[:15]:
            if 5 < len(line) < 80:
                return line.strip()

    return urlparse(url).netloc

# -------------------------------
# NAME VALIDATION (IMPROVED)
# -------------------------------
def is_valid_name(text):
    text = text.strip()

    if not re.match(r"^[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?(?: [A-Z][a-z]+){1,2}$", text):
        return False

    blacklist = [
        "management", "services", "engineering",
        "infrastructure", "impact", "solutions",
        "consulting", "group", "project",
        "rail", "transport", "design",
        "department", "team", "business"
    ]

    return not any(b in text.lower() for b in blacklist)

# -------------------------------
# PEOPLE EXTRACTION (FIXED)
# -------------------------------
def extract_people(pages):
    people = set()

    for page in pages:
        lines = page["markdown"].split("\n")

        for i, line in enumerate(lines):
            text = line.strip()

            if not is_valid_name(text):
                continue

            # 🔥 local context (key fix)
            context = " ".join(lines[max(0, i-3): i+3]).lower()

            if any(k in context for k in [
                "engineer", "structural", "bridge",
                "geotechnical", "civil",
                "principal", "senior", "director",
                "associate", "lead", "manager"
            ]):
                people.add(text)

    return list(people)[:15]

# -------------------------------
# PROJECTS
# -------------------------------
def extract_projects(pages):
    keywords = [
        "bridge", "tunnel", "geotechnical",
        "structural", "rail", "highway"
    ]

    found = set()

    for page in pages:
        text = page["markdown"].lower()

        for k in keywords:
            if k in text:
                found.add(k)

    return list(found)

# -------------------------------
# TEXT
# -------------------------------
def extract_company_text(pages):
    combined = ""

    for page in pages[:10]:
        combined += page["markdown"][:4000]

    return combined[:25000]

# -------------------------------
# JOBS
# -------------------------------

def extract_jobs(pages):
    job_keywords = [
        "engineer", "structural", "bridge",
        "geotechnical", "civil", "design",
        "analysis", "fea", "fem", "software"
    ]

    jobs = []

    for page in pages:
        url = page["url"].lower()

        # 🔥 only look at likely job pages
        if not any(k in url for k in ["career", "job", "vacanc"]):
            continue

        lines = page["markdown"].split("\n")

        for line in lines:
            text = line.strip()

            if 10 < len(text) < 120:
                if any(k in text.lower() for k in job_keywords):
                    jobs.append(text)

    return list(set(jobs))[:20]


# -------------------------------
# LLM ANALYSIS (IMPROVED PROMPT)
# -------------------------------
def analyze(company, text, people, projects,jobs):
    if not people:
        people = "No people found"

    prompt = f"""
Company: {company}

Data:
{text}

People Found:
{people}

Projects:
{projects}

Jobs Data:
{jobs}

Provide a FULL structured report based ONLY on the provided website data.

1. Company Overview
Summarise what the company does in max 5 concise bullet points
Include ALL office locations (city names only in one bullet point)
Do NOT infer missing locations
2. Engineering Capabilities
Summarise in max 6 concise bullet points
Focus on technical strengths, domains, and services
3. Key Personnel
Extract ONLY real human names (ignore generic titles or unclear entries)
Categorise into:
Directors
Senior / Principal Engineers
Engineers
Present in a clean table format

Rules:

Do NOT invent names
Exclude anything that does not clearly look like a person’s name
4. FEM Application Opportunities
Identify specific and contextual use cases where FEM can be applied based on company activities
Provide max 5 bullet points
Avoid generic statements
5. Recommended Sales Approach

(Heading must be exactly: Recommended Sales Approach)

Provide:

Ideal entry point (who to approach first)
Key pain points inferred from services/projects
Value positioning strategy
Likely objections
Suggested first conversation angle
All must be in seperate bullet points

6. Open Vacancy Insights

(Heading must be exactly: Open Vacancy)

Based ONLY on the Jobs Data provided:

- Identify relevant roles in:
  - Structural / Bridge / Geotechnical

For each role:
- Mention job title (if identifiable)
- Mention key skills or tools
- Highlight ANY mention of:
  - FEM / FEA / analysis software

Also provide:
- Hiring trend insight (e.g. growing team, specialised roles)

If no relevant jobs found:
→ Clearly state: "No relevant vacancies found"

7. LinkedIn Search Links

(Heading must be exactly: LinkedIn Search)

Create clickable LinkedIn search URLs for each extracted person
Use ONLY the name (no company or location)
One seperate link per person

8. Key Sales Signals 
Identify:
Hiring trends
Expansion indicators
Technical maturity
Project types
Max 5 bullet points

9. Pre-Meeting Cheat Sheet for MIDAS IT FEA Software Solutions

Provide:

3 things to mention
3 smart questions to ask
1 strong opening line

Clearly mention missing or weak data areas

IMPORTANT RULES:
For each section, assign:
High / Medium / Low confidence

Use ONLY provided data
Do NOT hallucinate or infer beyond evidence
If information is missing → explicitly state “Not found”
Keep output concise, structured, and professional
Do NOT repeat information across sections
Make sure LinkedIn links are clickable
Fill all the 9 points
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a structural engineering sales expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2500
    )

    return response.choices[0].message.content

# -------------------------------
# UI
# -------------------------------
st.title("🚀 MIDAS Sales Intelligence Tool")

website = st.text_input("Enter Company Website URL")

if st.button("Run Analysis"):

    if not website:
        st.warning("Enter a website")
        st.stop()

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🔍 Crawling..."):
        pages = crawl_site(website)

    if not pages:
        st.error("Could not extract data")
        st.stop()

    company = extract_company_name(pages, website)

    st.subheader("🏢 Company")
    st.write(company)

    people = extract_people(pages)
    projects = extract_projects(pages)
    text = extract_company_text(pages)

    with st.spinner("🧠 Analyzing..."):
        result = analyze(company, text, people, projects,jobs)

    st.subheader("📊 Insights")
    st.write(result)
