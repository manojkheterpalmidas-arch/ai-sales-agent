import streamlit as st
from openai import OpenAI
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib.parse

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
        "about", "staff"
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
        for line in page["markdown"].split("\n")[:10]:
            if 5 < len(line) < 80:
                return line.strip()

    return urlparse(url).netloc

# -------------------------------
# NAME VALIDATION (IMPROVED)
# -------------------------------
def is_valid_name(text):
    text = text.strip()

    # Must be 2–3 words
    if not re.match(r"^[A-Z][a-z]+(?:[-'][A-Z][a-z]+)?(?: [A-Z][a-z]+){1,2}$", text):
        return False

    words = text.split()

    # ❌ Reject if any word is too "generic"
    generic_words = [
        "asset", "management", "project", "bridge",
        "road", "rail", "design", "services",
        "engineering", "solutions", "infrastructure",
        "consulting", "group", "team", "business"
    ]

    for w in words:
        if w.lower() in generic_words:
            return False

    # ❌ Reject if all words are common nouns (not names)
    common_nouns = [
        "management", "bridge", "engineering",
        "project", "services", "design"
    ]

    if all(w.lower() in common_nouns for w in words):
        return False

    return True


# -------------------------------
# EXTRACT PEOPLE
# -------------------------------


def extract_people(pages):
    people = set()

    for page in pages:
        lines = page["markdown"].split("\n")

        for line in lines:
            text = line.strip()

            if not is_valid_name(text):
                continue

            people.add(text)

    return list(people)[:20]

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
# LLM ANALYSIS (STRICT + RELIABLE)
# -------------------------------
def analyze(company, text, people, projects):
    if not people:
        people = []

    prompt = f"""
Company: {company}

Website Data:
{text}

Extracted Name Candidates:
{people}

Projects:
{projects}

----------------------------------------
TASK
----------------------------------------

You must analyse the company and STRICTLY use the provided name candidates.

STEP 1 — FILTER REAL PEOPLE
From the "Extracted Name Candidates":
- Keep ONLY real human names
- REMOVE anything that is:
  - company name
  - project name
  - department
  - generic term (e.g. Asset Management, Infrastructure, etc.)

STEP 2 — CLASSIFY PEOPLE
Categorise ONLY valid individuals into:

- Directors / Leadership
- Senior / Principal Engineers
- Engineers

If no valid people exist, clearly say:
"No individual names found on the website"

STEP 3 — BUSINESS ANALYSIS
Provide:

1. What the company does
2. Engineering capabilities (focus on structural / bridge / geotech relevance)
3. Where FEM software can be applied
4. Recommended sales approach (very practical, not generic)

----------------------------------------
RULES (VERY IMPORTANT)
----------------------------------------

- DO NOT invent names
- DO NOT guess names
- ONLY use names from the provided list
- If list is wrong → return empty
- Be concise but insightful
- Focus on real engineering value

----------------------------------------
OUTPUT FORMAT
----------------------------------------

Use clear sections:

1. What the Company Does  
2. Engineering Capabilities  
3. Key Personnel  
4. FEM Opportunities  
5. Sales Strategy  

"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": "You are a strict data analyst for engineering sales. You only trust provided data and never hallucinate names."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2000
    )

    return response.choices[0].message.content
# -------------------------------
# Linkedin Search Link
# -------------------------------   
def generate_linkedin_search(name):
    query = urllib.parse.quote(name)
    return f"https://www.linkedin.com/search/results/people/?keywords={query}"


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

    # -------------------------------
    # PROCESS DATA
    # -------------------------------
    company = extract_company_name(pages, website)
    people = extract_people(pages)
    projects = extract_projects(pages)
    text = extract_company_text(pages)

    # -------------------------------
    # ANALYSIS
    # -------------------------------
    with st.spinner("🧠 Analyzing..."):
        result = analyze(company, text, people, projects)

    # -------------------------------
    # OUTPUT
    # -------------------------------
    st.subheader("🏢 Company")
    st.write(company)

    st.subheader("📊 Insights")
    st.write(result)

    # -------------------------------
    # CLEAN PEOPLE FROM LLM OUTPUT
    # -------------------------------
    clean_people = extract_clean_names_from_llm(result)

    st.subheader("👷 Key People")

    if clean_people:
        for person in clean_people:
            link = generate_linkedin_search(person)
            st.markdown(f"**{person}**  \n[🔗 Search on LinkedIn]({link})")
    else:
        st.write("No valid people identified")
