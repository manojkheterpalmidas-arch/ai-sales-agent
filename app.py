import streamlit as st
from firecrawl import FirecrawlApp
from openai import OpenAI

# -------------------------------
# INIT
# -------------------------------
firecrawl = FirecrawlApp(api_key=st.secrets["FIRECRAWL_API_KEY"])

client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# -------------------------------
# CLEAN TEXT (CRITICAL)
# -------------------------------
def clean_text(text):
    lines = text.split("\n")
    filtered = []

    for line in lines:
        if len(line.strip()) > 40:
            filtered.append(line.strip())

    return "\n".join(filtered[:200])


# -------------------------------
# CRAWL MULTIPLE PAGES
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
            data[key] = result["markdown"]
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
            {"role": "system", "content": "You are a precise and strict engineering analyst. Never guess."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=600
    )

    return response.choices[0].message.content


# -------------------------------
# COMPANY ANALYSIS (STRICT)
# -------------------------------
def analyze_company(home_text, services_text):
    text = clean_text(home_text + "\n" + services_text)

    prompt = f"""
Extract ONLY factual company information.

DATA:
{text}

Return:
- What the company does
- Engineering sectors
- Capabilities

If not found → say NOT AVAILABLE

NO assumptions.
"""
    return call_llm(prompt)


# -------------------------------
# PROJECT ANALYSIS
# -------------------------------
def analyze_projects(project_text):
    project_text = clean_text(project_text)

    prompt = f"""
Extract ONLY real project information.

DATA:
{project_text}

Return:
- Types of structures mentioned (bridges, buildings, geotech, etc.)
- Project categories

If unclear → say NOT CLEAR

NO guessing.
"""
    return call_llm(prompt)


# -------------------------------
# PEOPLE EXTRACTION (STRICT)
# -------------------------------
def extract_people(team_text):
    team_text = clean_text(team_text)

    prompt = f"""
Extract ONLY real people explicitly mentioned.

DATA:
{team_text}

Rules:
- ONLY extract names that clearly appear
- DO NOT guess
- If none → return "NOT FOUND"

Focus ONLY:
- Structural engineers
- Bridge engineers
- Geotechnical engineers
- Technical directors

Format:
Name | Role | Decision Level

Decision Level:
- Technical Director → Decision Maker
- Senior Engineer → Influencer
"""
    return call_llm(prompt)


# -------------------------------
# SALES STRATEGY (DATA-BASED)
# -------------------------------
def generate_strategy(company, comp, proj, people):
    prompt = f"""
You are a sales engineer selling FEM software (MIDAS).

Use ONLY the provided data.

Company Info:
{comp}

Projects:
{proj}

People:
{people}

If data is missing → say "INSUFFICIENT DATA"

Return:
- Where FEM is used (ONLY if clear)
- Pain points (based on projects)
- Best person to approach
- Practical sales approach

NO guessing.
"""
    return call_llm(prompt)


# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence V4.5", layout="wide")

st.title("🚀 MIDAS Sales Intelligence (Accurate Mode)")

company = st.text_input("Company Name")
website = st.text_input("Website URL")

if st.button("Run Analysis"):

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🔥 Crawling website..."):
        data = crawl_pages(website)

    with st.spinner("🧠 Analyzing company..."):
        comp = analyze_company(data["home"], data["services"])

    with st.spinner("🏗️ Extracting projects..."):
        proj = analyze_projects(data["projects"])

    with st.spinner("👥 Extracting people..."):
        people = extract_people(data["team"])

    with st.spinner("📊 Generating strategy..."):
        strategy = generate_strategy(company, comp, proj, people)

    # -------------------------------
    # DISPLAY
    # -------------------------------
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Company Overview")
        st.write(comp)

        st.subheader("🏗️ Projects & Structures")
        st.write(proj)

    with col2:
        st.subheader("👥 Key People")
        st.write(people)

        st.subheader("📊 Sales Strategy")
        st.write(strategy)
