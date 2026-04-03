import streamlit as st
from openai import OpenAI
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# -------------------------------
# PAGE CONFIG + WHITE UI
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence Tool", layout="wide")

st.markdown("""
<style>
.stApp { background-color: white !important; color: black !important; }
html, body, [class*="css"]  { color: black !important; }
h1, h2, h3, h4 { color: black !important; }
pre, code { background-color: #f5f5f5 !important; color: black !important; }
</style>
""", unsafe_allow_html=True)

# -------------------------------
# INIT LLM
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

    priority = ["team", "people", "about", "project", "service"]

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
# VALID NAME FILTER
# -------------------------------
def is_valid_name(text):
    if not re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", text):
        return False

    blacklist = [
        "management","services","engineering","infrastructure",
        "impact","solutions","consulting","group",
        "project","rail","transport","design"
    ]

    return not any(b in text.lower() for b in blacklist)

# -------------------------------
# ENGINEER EXTRACTION
# -------------------------------
def extract_people(pages):
    people = []

    role_keywords = [
        "engineer","structural","bridge",
        "geotechnical","civil","principal",
        "senior","lead"
    ]

    for page in pages:
        lines = page["markdown"].split("\n")

        for i in range(len(lines)-1):
            name = lines[i].strip()
            role = lines[i+1].strip().lower()

            if not is_valid_name(name):
                continue

            if any(k in role for k in role_keywords):
                people.append(f"{name} | {lines[i+1].strip()}")

    return list(set(people))[:6]

# -------------------------------
# SERPER LINKEDIN SEARCH
# -------------------------------
def find_linkedin_profile(name, company):
    try:
        query = f"{name} {company} linkedin"

        url = "https://google.serper.dev/search"

        headers = {
            "X-API-KEY": st.secrets["SERPER_API_KEY"],
            "Content-Type": "application/json"
        }

        res = requests.post(url, json={"q": query}, headers=headers)
        data = res.json()

        for result in data.get("organic", []):
            link = result.get("link", "")

            if "linkedin.com/in/" in link:
                return link

        return "Not found"

    except:
        return "Error"

# -------------------------------
# ENRICH PEOPLE
# -------------------------------
def enrich_people(people, company):
    enriched = []

    for p in people:
        name = p.split("|")[0].strip()
        role = p.split("|")[1].strip() if "|" in p else ""

        linkedin = find_linkedin_profile(name, company)

        enriched.append({
            "name": name,
            "role": role,
            "linkedin": linkedin
        })

    return enriched

# -------------------------------
# PROJECTS
# -------------------------------
def extract_projects(pages):
    keywords = [
        "bridge","tunnel","geotechnical",
        "structural","rail","highway"
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
# LLM
# -------------------------------
def analyze(company, text, people, projects):
    if not people:
        people = "No engineers found"

    prompt = f"""
Company: {company}

Data:
{text}

Engineers:
{people}

Projects:
{projects}

Provide FULL report:
1. What company does
2. Engineering focus
3. FEM opportunity
4. Sales strategy (DETAILED)

Do not stop early.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role":"system","content":"You are a structural engineering sales expert."},
            {"role":"user","content":prompt}
        ],
        temperature=0.2,
        max_tokens=2000
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

    enriched = enrich_people(people, company)

    with st.spinner("🧠 Analyzing..."):
        result = analyze(company, text, people, projects)

    # MAIN OUTPUT
    st.subheader("📊 Insights")
    st.write(result)

    # ENGINEERS WITH LINKEDIN
    with st.expander("👷 Engineers + LinkedIn"):
        if enriched:
            for p in enriched:
                st.write(f"**{p['name']}** – {p['role']}")
                st.write(p["linkedin"])
        else:
            st.write("No engineers found")

    # PROJECTS
    with st.expander("🏗️ Projects"):
        st.write(projects)
