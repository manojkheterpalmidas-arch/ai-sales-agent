import streamlit as st
from openai import OpenAI
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

st.set_page_config(page_title="MIDAS Sales Intelligence Tool", layout="wide")

st.markdown("""
<style>

/* Main app background */
.stApp {
    background-color: white !important;
    color: black !important;
}

/* Text */
html, body, [class*="css"]  {
    color: black !important;
}

/* Headers */
h1, h2, h3, h4 {
    color: black !important;
}

/* Input boxes */
input, textarea {
    background-color: white !important;
    color: black !important;
}

/* Buttons */
button {
    background-color: #f0f0f0 !important;
    color: black !important;
    border: 1px solid #ccc !important;
}

/* Expanders (your "bars") */
details {
    background-color: white !important;
    border: 1px solid #ddd !important;
    border-radius: 8px;
    padding: 10px;
}

/* Expander header */
summary {
    color: black !important;
    font-weight: 600;
}

/* Code blocks (very important — your dark bars) */
code {
    background-color: #f5f5f5 !important;
    color: black !important;
}

/* Preformatted blocks */
pre {
    background-color: #f5f5f5 !important;
    color: black !important;
    border-radius: 8px;
    padding: 10px;
}

/* Data boxes / JSON display */
.stCodeBlock {
    background-color: #f5f5f5 !important;
    color: black !important;
}

/* Expandable JSON (your current dark box issue) */
.css-1d391kg, .css-1v0mbdj {
    background-color: white !important;
    color: black !important;
}

</style>
""", unsafe_allow_html=True)
# -------------------------------
# INIT
# -------------------------------
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# -------------------------------
# SCRAPER (STREAMLIT SAFE)
# -------------------------------
def scrape_page(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US"
        }

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
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(base_url, headers=headers, timeout=10)
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
        lines = page["markdown"].split("\n")

        for line in lines[:10]:
            if 5 < len(line) < 80:
                return line.strip()

    return urlparse(url).netloc

# -------------------------------
# STRICT NAME VALIDATION
# -------------------------------
def is_valid_name(text):
    if not re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", text):
        return False

    blacklist = [
        "management", "services", "engineering",
        "infrastructure", "impact", "solutions",
        "consulting", "group", "project",
        "rail", "transport", "design"
    ]

    return not any(b in text.lower() for b in blacklist)

# -------------------------------
# ENGINEER EXTRACTION
# -------------------------------
def extract_people(pages):
    people = []

    role_keywords = [
        "engineer", "structural", "bridge",
        "geotechnical", "civil",
        "principal", "senior", "lead"
    ]

    for page in pages:
        lines = page["markdown"].split("\n")

        for i in range(len(lines) - 1):
            name = lines[i].strip()
            role = lines[i + 1].strip().lower()

            if not is_valid_name(name):
                continue

            if any(k in role for k in role_keywords):
                people.append(f"{name} | {lines[i+1].strip()}")

    return list(set(people))[:8]

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
# LLM
# -------------------------------
def analyze(company, text, people, projects):
    if not people:
        people = "No engineers found on website"

    prompt = f"""
Company: {company}

Data:
{text}

Engineers:
{people}

Projects:
{projects}

Analyze:
- What company does
- Engineering focus
- Relevant engineers
- FEM opportunities
- Sales approach

Do not invent names.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a structural engineering sales expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=2000
    )

    return response.choices[0].message.content

# -------------------------------
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

    st.write(f"Pages crawled: {len(pages)}")

    if not pages:
        st.error("Could not extract data.")
        st.stop()

    company = extract_company_name(pages, website)

    st.subheader("🏢 Company")
    st.write(company)

    people = extract_people(pages)
    projects = extract_projects(pages)
    text = extract_company_text(pages)

    with st.spinner("🧠 Analyzing..."):
        result = analyze(company, text, people, projects)

    # 🔥 MAIN OUTPUT FIRST
    st.subheader("📊 Insights")
    st.write(result)

    # 🔥 BACKGROUND DATA (COLLAPSIBLE)
    with st.expander("🔍 View Extracted Data (Engineers & Projects)"):

        st.subheader("👷 Engineers")
        st.write(people if people else "No engineers found")

        st.subheader("🏗️ Projects")
        st.write(projects)
