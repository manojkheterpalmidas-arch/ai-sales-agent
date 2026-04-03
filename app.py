import streamlit as st
import os
from firecrawl import FirecrawlApp
from openai import OpenAI

# -------------------------------
# INIT
# -------------------------------
firecrawl = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# -------------------------------
# MULTI PAGE CRAWL
# -------------------------------
def crawl_pages(base_url):
    pages = {
        "home": base_url,
        "services": base_url + "/services",
        "projects": base_url + "/projects",
        "team": base_url + "/team"
    }

    data = {}

    for key, url in pages.items():
        try:
            result = firecrawl.scrape_url(url, formats=["markdown"])
            data[key] = result["markdown"][:4000]
        except:
            data[key] = ""

    return data


# -------------------------------
# COMPANY + CAPABILITIES
# -------------------------------
def analyze_company(data, company):
    prompt = f"""
Analyze this engineering company.

COMPANY: {company}

HOME + SERVICES DATA:
{data["home"]}
{data["services"]}

Return:

1. Company Overview
2. Engineering Capabilities
   - structures
   - sectors
   - expertise

Be specific.
"""

    return call_llm(prompt)


# -------------------------------
# PROJECT ANALYSIS
# -------------------------------
def analyze_projects(data):
    prompt = f"""
Analyze project types from this data:

{data["projects"]}

Return:
- Types of structures (bridges, buildings, geotech)
- Complexity level
- Engineering focus

Be precise.
"""
    return call_llm(prompt)


# -------------------------------
# PEOPLE EXTRACTION
# -------------------------------
def extract_people(data):
    prompt = f"""
Extract ONLY engineering decision makers.

TEAM DATA:
{data["team"]}

Rules:
- Structural / Bridge / Geotech only
- No guessing

Classify:
Name | Role | Decision Level

Decision Level:
- Technical Director → Decision Maker
- Senior Engineer → Influencer

Max 5 people.
"""

    return call_llm(prompt)


# -------------------------------
# FINAL SALES STRATEGY
# -------------------------------
def generate_strategy(company, comp, proj, people):
    prompt = f"""
You are selling MIDAS FEM software.

Company: {company}

Company Info:
{comp}

Projects:
{proj}

People:
{people}

Generate:

1. Where they use FEM
2. Pain points
3. Best decision makers
4. Sales approach
5. Outreach message

Be practical and specific.
"""

    return call_llm(prompt)


# -------------------------------
# LLM CALL
# -------------------------------
def call_llm(prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a precise engineering analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=600
    )

    return response.choices[0].message.content


# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="AI Sales Intelligence V4", layout="wide")

st.title("🚀 Structural Engineering Intelligence (V4)")

company = st.text_input("Company Name")
website = st.text_input("Website URL")

if st.button("Run Analysis"):

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🔥 Crawling structured pages..."):
        data = crawl_pages(website)

    with st.spinner("🧠 Analyzing company..."):
        comp = analyze_company(data, company)

    with st.spinner("🏗️ Analyzing projects..."):
        proj = analyze_projects(data)

    with st.spinner("👥 Extracting people..."):
        people = extract_people(data)

    with st.spinner("📊 Building strategy..."):
        strategy = generate_strategy(company, comp, proj, people)

    # OUTPUT
    st.subheader("🏢 Company Overview")
    st.text(comp)

    st.subheader("🏗️ Projects & Capabilities")
    st.text(proj)

    st.subheader("👥 Key People")
    st.text(people)

    st.subheader("📊 Sales Strategy")
    st.text(strategy)