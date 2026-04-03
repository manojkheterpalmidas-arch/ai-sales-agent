import streamlit as st
from firecrawl import FirecrawlApp
from openai import OpenAI

# -------------------------------
# INIT (STREAMLIT SECRETS)
# -------------------------------
firecrawl = FirecrawlApp(api_key=st.secrets["FIRECRAWL_API_KEY"])

client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# -------------------------------
# MULTI-PAGE CRAWL
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
# LLM CALL
# -------------------------------
def call_llm(prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a precise structural engineering analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=700
    )

    return response.choices[0].message.content


# -------------------------------
# ANALYSIS FUNCTIONS
# -------------------------------
def analyze_company(data, company):
    prompt = f"""
Analyze this engineering company.

COMPANY: {company}

DATA:
{data["home"]}
{data["services"]}

Return:

- Company overview
- History / positioning
- Sectors
- Engineering capabilities
- Types of structures
"""
    return call_llm(prompt)


def analyze_projects(data):
    prompt = f"""
Analyze engineering projects.

DATA:
{data["projects"]}

Return:
- Types of structures (bridges, buildings, geotech)
- Project complexity
- Engineering focus
"""
    return call_llm(prompt)


def extract_people(data):
    prompt = f"""
Extract ONLY engineering decision makers.

DATA:
{data["team"]}

Rules:
- Structural / Bridge / Geotechnical roles only
- Do NOT guess names

Format:
Name | Role | Decision Level

Decision Level:
- Technical Director → Decision Maker
- Senior Engineer → Influencer

Max 5 people.
"""
    return call_llm(prompt)


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

Return:

1. Where FEM is used
2. Key pain points
3. Best decision makers
4. Sales approach
5. Outreach message

Be specific and practical.
"""
    return call_llm(prompt)


# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence", layout="wide")

st.title("🚀 MIDAS Sales Intelligence Tool")

company = st.text_input("Company Name")
website = st.text_input("Website URL")

if st.button("Run Analysis"):

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🔥 Crawling website..."):
        data = crawl_pages(website)

    with st.spinner("🧠 Analyzing company..."):
        comp = analyze_company(data, company)

    with st.spinner("🏗️ Analyzing projects..."):
        proj = analyze_projects(data)

    with st.spinner("👥 Extracting decision makers..."):
        people = extract_people(data)

    with st.spinner("📊 Generating sales strategy..."):
        strategy = generate_strategy(company, comp, proj, people)

    # -------------------------------
    # DISPLAY CLEAN UI
    # -------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Company Overview")
        st.write(comp)

        st.subheader("🏗️ Engineering Projects")
        st.write(proj)

    with col2:
        st.subheader("👥 Key Decision Makers")
        st.write(people)

        st.subheader("📊 Sales Strategy")
        st.write(strategy)
