import asyncio
import re
import streamlit as st
from crawl4ai import AsyncWebCrawler
from langchain_ollama import ChatOllama
from duckduckgo_search import DDGS

# -------------------------------
# LLM
# -------------------------------
llm = ChatOllama(model="mistral")


# -------------------------------
# CRAWLER
# -------------------------------
async def crawl_website(base_url):
    pages = [
        base_url,
        base_url + "/about",
        base_url + "/team",
        base_url + "/people",
        base_url + "/services"
    ]

    content = ""

    async with AsyncWebCrawler() as crawler:
        for url in pages:
            try:
                result = await crawler.arun(url=url)
                if result and result.markdown:
                    content += result.markdown[:2000]
            except:
                continue

    return content[:8000]


# -------------------------------
# EXTRACT PEOPLE
# -------------------------------
def extract_people(text):
    prompt = f"""
Extract key people from this company.

Focus on:
- Structural engineers
- Technical directors
- Engineering leads

Return:
Name | Role

TEXT:
{text}
"""
    return llm.invoke(prompt).content


# -------------------------------
# FIND LINKEDIN (REALISTIC)
# -------------------------------
def find_linkedin(name, company):
    query = f"{name} {company} LinkedIn"

    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=3))

    for r in results:
        if "linkedin.com/in" in r["href"]:
            return r["href"]

    return "Not found"


# -------------------------------
# EMAIL FINDER
# -------------------------------
def find_emails(text, domain):
    emails = re.findall(r"[A-Za-z0-9._%+-]+@" + domain, text)
    return list(set(emails))


def guess_email(name, domain):
    parts = name.lower().split()
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[-1]}@{domain}"
    return None


# -------------------------------
# STRATEGY
# -------------------------------
def generate_strategy(company, data, people):
    prompt = f"""
You are a sales expert selling FEM software (MIDAS type).

Company: {company}

Data:
{data}

People:
{people}

Generate:

1. Company focus
2. FEM usage potential
3. Key targets
4. Pain points
5. Sales strategy
6. Email outreach idea
"""

    return llm.invoke(prompt).content


# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="AI Sales Agent V3", layout="wide")

st.title("🚀 AI Sales Agent (Structural Engineering Focus)")

company = st.text_input("Company Name")
website = st.text_input("Website URL")

if st.button("Run Analysis"):

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("Crawling website..."):
        data = asyncio.run(crawl_website(website))

    with st.spinner("Extracting people..."):
        people = extract_people(data)

    st.subheader("👥 Key People")
    st.text(people)

    # Extract domain
    domain = website.replace("https://", "").replace("http://", "").split("/")[0]

    st.subheader("🔗 LinkedIn Profiles")
    for line in people.split("\n")[:5]:
        if "|" in line:
            name = line.split("|")[0].strip()
            link = find_linkedin(name, company)
            st.write(f"{name}: {link}")

    st.subheader("📧 Emails Found")
    emails = find_emails(data, domain)
    for e in emails:
        st.write(e)

    st.subheader("📧 Email Guesses")
    for line in people.split("\n")[:5]:
        if "|" in line:
            name = line.split("|")[0].strip()
            guess = guess_email(name, domain)
            if guess:
                st.write(guess)

    with st.spinner("Generating strategy..."):
        strategy = generate_strategy(company, data, people)

    st.subheader("📊 Sales Strategy")
    st.text(strategy)