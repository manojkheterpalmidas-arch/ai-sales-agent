import streamlit as st
from openai import OpenAI
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

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
def fallback_scrape(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        text = soup.get_text(separator="\n")
        return text[:6000]  # 🔥 increased

    except:
        return ""

# -------------------------------
# GET INTERNAL LINKS
# -------------------------------
def get_internal_links(base_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(base_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        links = set()
        domain = urlparse(base_url).netloc

        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(base_url, href)

            if urlparse(full_url).netloc == domain:
                links.add(full_url)

        return list(links)

    except:
        return []

# -------------------------------
# DEEP CRAWL
# -------------------------------
def crawl_site(base_url):
    pages = []

    # homepage
    homepage = fallback_scrape(base_url)
    if homepage:
        pages.append({"url": base_url, "markdown": homepage})

    # discover links
    links = get_internal_links(base_url)

    priority_keywords = ["about", "team", "people", "project", "service", "portfolio"]

    sorted_links = sorted(
        links,
        key=lambda x: any(p in x.lower() for p in priority_keywords),
        reverse=True
    )

    # 🔥 increased from 10 → 15
    for link in sorted_links[:15]:
        text = fallback_scrape(link)

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

    domain = re.sub(r"https?://(www\.)?", "", url)
    return domain.split("/")[0]

# -------------------------------
# PEOPLE EXTRACTION
# -------------------------------
def extract_people(pages):
    people = set()

    for page in pages:
        matches = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", page["markdown"])

        for m in matches:
            people.add(m)

    return list(people)[:8]

# -------------------------------
# PROJECT DETECTION
# -------------------------------
def extract_projects(pages):
    keywords = [
        "bridge", "tunnel", "geotechnical",
        "structural", "infrastructure",
        "rail", "highway"
    ]

    found = set()

    for page in pages:
        text = page["markdown"].lower()

        for k in keywords:
            if k in text:
                found.add(k)

    return list(found)

# -------------------------------
# COMBINE TEXT (DEEPER)
# -------------------------------
def extract_company_text(pages):
    combined = ""

    # 🔥 increased pages + depth
    for page in pages[:12]:
        combined += page["markdown"][:4000]

    return combined[:25000]  # 🔥 increased total cap

# -------------------------------
# LLM ANALYSIS
# -------------------------------
def analyze(company, text, people, projects):
    prompt = f"""
Company: {company}

Website Data:
{text}

People Found:
{people}

Project Types:
{projects}

Analyze:

1. What the company does
2. Engineering capabilities
3. Decision makers (from given names only)
4. Where FEM is used
5. Sales strategy

Be realistic and specific.
DO NOT invent data.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a senior engineering sales analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=900
    )

    return response.choices[0].message.content

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence V6.1", layout="wide")

st.title("🚀 MIDAS Sales Intelligence Tool (Deep Crawl + High Accuracy)")

website = st.text_input("Enter Company Website URL")

if st.button("Run Analysis"):

    if not website:
        st.warning("Please enter a website URL")
        st.stop()

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🔍 Deep crawling website..."):
        pages = crawl_site(website)

    st.write(f"🔎 Pages crawled: {len(pages)}")

    if not pages:
        st.error("❌ Could not extract data.")
        st.stop()

    company = extract_company_name(pages, website)

    st.subheader("🏢 Detected Company")
    st.write(company)

    people = extract_people(pages)
    projects = extract_projects(pages)
    text = extract_company_text(pages)

    with st.spinner("🧠 Analyzing..."):
        result = analyze(company, text, people, projects)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Extracted People")
        st.write(people)

        st.subheader("🏗️ Project Types")
        st.write(projects)

    with col2:
        st.subheader("📊 Analysis")
        st.write(result)
