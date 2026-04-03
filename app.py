import streamlit as st
from firecrawl import FirecrawlApp
from openai import OpenAI
import re

# -------------------------------
# INIT
# -------------------------------
firecrawl = FirecrawlApp(api_key=st.secrets["FIRECRAWL_API_KEY"])

client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# -------------------------------
# SMART SCRAPE (NO crawl_url)
# -------------------------------
def crawl_site(base_url):
    pages_to_try = [
        base_url,
        base_url + "/about",
        base_url + "/about-us",
        base_url + "/services",
        base_url + "/projects",
        base_url + "/portfolio",
        base_url + "/team",
        base_url + "/people",
        base_url + "/who-we-are"
    ]

    pages = []

    for url in pages_to_try:
        try:
            result = firecrawl.scrape_url(url, formats=["markdown"])
            text = result.get("markdown", "")

            if len(text) > 200:
                pages.append({
                    "url": url,
                    "markdown": text
                })
        except:
            continue

    return pages


# -------------------------------
# AUTO DETECT COMPANY NAME
# -------------------------------
def extract_company_name(pages, url):
    for page in pages:
        text = page.get("markdown", "")
        lines = text.split("\n")

        for line in lines[:10]:
            if 5 < len(line) < 80:
                return line.strip()

    # fallback to domain
    domain = re.sub(r"https?://(www\.)?", "", url)
    return domain.split("/")[0]


# -------------------------------
# EXTRACT PEOPLE (BASIC BUT REAL)
# -------------------------------
def extract_people(pages):
    people = set()

    for page in pages:
        text = page.get("markdown", "")

        matches = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)

        for m in matches:
            if len(m.split()) == 2:
                people.add(m)

    return list(people)[:5]


# -------------------------------
# EXTRACT PROJECT TYPES
# -------------------------------
def extract_projects(pages):
    keywords = ["bridge", "tunnel", "geotechnical", "structural", "infrastructure"]

    found = set()

    for page in pages:
        text = page.get("markdown", "").lower()

        for k in keywords:
            if k in text:
                found.add(k)

    return list(found)


# -------------------------------
# COMBINE TEXT
# -------------------------------
def extract_company_text(pages):
    combined = ""

    for page in pages[:3]:
        combined += page.get("markdown", "")[:1500]

    return combined


# -------------------------------
# LLM ANALYSIS (CONTROLLED)
# -------------------------------
def analyze(company, text, people, projects):
    prompt = f"""
Company: {company}

Website Info:
{text}

People Found:
{people}

Project Types:
{projects}

Analyze STRICTLY:

1. What company does
2. Engineering capabilities
3. Who are decision makers (from given names only)
4. Where FEM is used (only if clear)
5. Sales strategy (based on projects)

DO NOT invent names or projects.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a strict engineering analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=700
    )

    return response.choices[0].message.content


# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence", layout="wide")

st.title("🚀 MIDAS Sales Intelligence Tool")

website = st.text_input("Enter Company Website URL")

if st.button("Run Analysis"):

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🔍 Crawling website..."):
        pages = crawl_site(website)

    if not pages:
        st.error("No data found. Try another website.")
    else:
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
            st.subheader("👥 Extracted People (Raw)")
            st.write(people)

            st.subheader("🏗️ Project Types")
            st.write(projects)

        with col2:
            st.subheader("📊 Analysis")
            st.write(result)
