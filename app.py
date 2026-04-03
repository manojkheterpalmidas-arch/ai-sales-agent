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
# CRAWL
# -------------------------------
def crawl_site(url):
    crawl = firecrawl.crawl_url(url, limit=8)
    return crawl["data"]

# -------------------------------
# EXTRACT PEOPLE (REAL)
# -------------------------------
def extract_people(pages):
    people = []

    for page in pages:
        text = page.get("markdown", "")

        # find name-like patterns
        matches = re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", text)

        for m in matches[:5]:
            people.append(m)

    return list(set(people))[:5]

# -------------------------------
# EXTRACT PROJECT KEYWORDS
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
# EXTRACT COMPANY TEXT
# -------------------------------
def extract_company_text(pages):
    combined = ""

    for page in pages[:3]:
        combined += page.get("markdown", "")[:1000]

    return combined

# -------------------------------
# LLM ANALYSIS (ONLY INTERPRET)
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

Analyze:

1. What company does
2. Engineering capabilities
3. Which people are decision makers
4. Where FEM is used
5. Sales strategy

ONLY use given data.
Do NOT invent anything.
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
st.title("🚀 MIDAS Sales Intelligence V5 (Accurate Mode)")

company = st.text_input("Company Name")
website = st.text_input("Website URL")

if st.button("Run Analysis"):

    with st.spinner("Crawling..."):
        pages = crawl_site(website)

    people = extract_people(pages)
    projects = extract_projects(pages)
    text = extract_company_text(pages)

    with st.spinner("Analyzing..."):
        result = analyze(company, text, people, projects)

    st.subheader("👥 Extracted People (Raw)")
    st.write(people)

    st.subheader("🏗️ Detected Project Types")
    st.write(projects)

    st.subheader("📊 Analysis")
    st.write(result)
