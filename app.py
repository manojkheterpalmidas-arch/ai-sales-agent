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
# SMART CRAWL
# -------------------------------
def crawl_site(base_url):
    try:
        crawl = firecrawl.crawl_url(
            base_url,
            limit=10  # crawl multiple pages
        )

        pages = crawl["data"]

        content = {
            "team": "",
            "projects": "",
            "company": ""
        }

        for page in pages:
            url = page["url"]
            text = page.get("markdown", "")

            if any(x in url.lower() for x in ["team", "people", "about"]):
                content["team"] += text

            elif any(x in url.lower() for x in ["project", "portfolio"]):
                content["projects"] += text

            else:
                content["company"] += text

        return content

    except Exception as e:
        return {"team": "", "projects": "", "company": ""}


# -------------------------------
# LLM CALL
# -------------------------------
def call_llm(prompt):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are an engineering analyst. Be accurate, but reasonable."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=700
    )

    return response.choices[0].message.content


# -------------------------------
# ANALYSIS
# -------------------------------
def analyze_company(text):
    prompt = f"""
Analyze this company.

{text}

Return:
- What they do
- Engineering sectors
- Capabilities
"""
    return call_llm(prompt)


def analyze_projects(text):
    prompt = f"""
Extract project types.

{text}

Return:
- Types of structures
- Engineering focus
"""
    return call_llm(prompt)


def extract_people(text):
    prompt = f"""
Extract key engineering people.

{text}

Focus:
- Structural engineers
- Technical directors
- Bridge / geotech engineers

Format:
Name | Role | Decision Level
"""
    return call_llm(prompt)


def generate_strategy(company, comp, proj, people):
    prompt = f"""
You are selling MIDAS software.

Company: {company}

Data:
{comp}
{proj}
{people}

Return:
- FEM usage
- Pain points
- Target people
- Sales approach
"""
    return call_llm(prompt)


# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="MIDAS Sales Intelligence V4.6", layout="wide")

st.title("🚀 MIDAS Sales Intelligence (Smart Crawl)")

company = st.text_input("Company Name")
website = st.text_input("Website URL")

if st.button("Run Analysis"):

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🔥 Smart crawling website..."):
        data = crawl_site(website)

    with st.spinner("🧠 Analyzing company..."):
        comp = analyze_company(data["company"])

    with st.spinner("🏗️ Analyzing projects..."):
        proj = analyze_projects(data["projects"])

    with st.spinner("👥 Extracting people..."):
        people = extract_people(data["team"])

    with st.spinner("📊 Generating strategy..."):
        strategy = generate_strategy(company, comp, proj, people)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏢 Company Overview")
        st.write(comp)

        st.subheader("🏗️ Projects")
        st.write(proj)

    with col2:
        st.subheader("👥 People")
        st.write(people)

        st.subheader("📊 Strategy")
        st.write(strategy)
