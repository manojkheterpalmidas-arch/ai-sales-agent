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

PASSCODE = "5487"

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
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence Tool", layout="wide")

st.markdown("""
<style>
.stApp { background-color: white !important; color: black !important; }
html, body { color: black !important; }

.stTextInput input {
    background-color: white !important;
    color: black !important;
    border: 1px solid #ccc !important;
    caret-color: black !important;
}

button {
    background-color: #f0f0f0 !important;
    color: black !important;
}

pre, code {
    background-color: #f5f5f5 !important;
    color: black !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# HEADER TAG
# -------------------------------
st.markdown("""
<div style="position: fixed; top: 70px; right: 25px;
font-size: 14px; font-weight: 600;">
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
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code != 200:
            return ""

        soup = BeautifulSoup(res.text, "html.parser")
        return soup.get_text(separator="\n")[:6000]
    except:
        return ""

# -------------------------------
# LINKS
# -------------------------------
def get_links(base_url):
    links = set()
    try:
        res = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
        soup = BeautifulSoup(res.text, "html.parser")
        domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            full = urljoin(base_url, a["href"])
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

    priority = ["team", "people", "about", "leadership"]

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
# NAME VALIDATION
# -------------------------------
def is_valid_name(text):
    return bool(re.match(r"^[A-Z][a-z]+(?: [A-Z][a-z]+){1,2}$", text))

# -------------------------------
# EXTRACT PEOPLE
# -------------------------------
def extract_people(pages):
    people = set()

    for page in pages:
        for line in page["markdown"].split("\n"):
            name = line.strip()

            if is_valid_name(name):
                people.add(name)

    return list(people)[:20]

# -------------------------------
# PROJECTS
# -------------------------------
def extract_projects(pages):
    keywords = ["bridge", "tunnel", "geotechnical", "rail", "highway"]
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
    return "".join([p["markdown"][:4000] for p in pages])[:25000]

# -------------------------------
# LLM ANALYSIS
# -------------------------------
def analyze(company, text, people, projects):

    prompt = f"""
Company: {company}

Data:
{text}

People:
{people}

Projects:
{projects}

TASK:
- Filter real people only
- Categorise into roles
- Do full company + sales analysis

DO NOT invent names.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a strict engineering sales analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=2000
    )

    return response.choices[0].message.content

# -------------------------------
# CLEAN NAMES FROM LLM OUTPUT
# -------------------------------
def extract_clean_names_from_llm(text):
    pattern = r"\b[A-Z][a-z]+(?: [A-Z][a-z]+){1,2}\b"
    names = re.findall(pattern, text)

    blacklist = ["Asset Management", "Quick Links", "Get In Touch"]

    return list(set([n for n in names if n not in blacklist]))

# -------------------------------
# LINKEDIN
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

    company = extract_company_name(pages, website)
    people = extract_people(pages)
    projects = extract_projects(pages)
    text = extract_company_text(pages)

    with st.spinner("🧠 Analyzing..."):
        result = analyze(company, text, people, projects)

    st.subheader("🏢 Company")
    st.write(company)

    st.subheader("📊 Insights")
    st.write(result)

    # 🔥 CLEAN PEOPLE
    clean_people = extract_clean_names_from_llm(result)

    st.subheader("👷 Key People")

    if clean_people:
        for person in clean_people:
            link = generate_linkedin_search(person)
            st.markdown(f"**{person}**  \n[🔗 Search on LinkedIn]({link})")
    else:
        st.write("No valid people identified")
