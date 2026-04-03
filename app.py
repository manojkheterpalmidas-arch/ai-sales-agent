import streamlit as st
from openai import OpenAI
import re
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

# -------------------------------
# INIT
# -------------------------------
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

# -------------------------------
# BROWSER SCRAPER
# -------------------------------
def browser_scrape(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(url, timeout=30000)
            page.wait_for_timeout(3000)

            content = page.inner_text("body")

            browser.close()

            return content[:6000]

    except:
        return ""

# -------------------------------
# GET LINKS
# -------------------------------
def get_internal_links(base_url):
    links = set()

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(base_url, timeout=30000)

            anchors = page.query_selector_all("a")
            domain = urlparse(base_url).netloc

            for a in anchors:
                href = a.get_attribute("href")
                if not href:
                    continue

                full_url = urljoin(base_url, href)

                if urlparse(full_url).netloc == domain:
                    links.add(full_url)

            browser.close()

    except:
        pass

    return list(links)

# -------------------------------
# CRAWL
# -------------------------------
def crawl_site(base_url):
    pages = []

    homepage = browser_scrape(base_url)
    if homepage:
        pages.append({"url": base_url, "markdown": homepage})

    links = get_internal_links(base_url)

    priority = ["team", "people", "about", "project", "service"]

    sorted_links = sorted(
        links,
        key=lambda x: any(p in x.lower() for p in priority),
        reverse=True
    )

    for link in sorted_links[:10]:
        text = browser_scrape(link)

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
    # must be two words, capitalized
    if not re.match(r"^[A-Z][a-z]+ [A-Z][a-z]+$", text):
        return False

    # reject common non-human words
    blacklist = [
        "management", "services", "engineering",
        "infrastructure", "impact", "solutions",
        "consulting", "group", "project",
        "rail", "transport", "design"
    ]

    if any(b in text.lower() for b in blacklist):
        return False

    return True

# -------------------------------
# ENGINEER EXTRACTION (FIXED)
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

            # strict validation
            if not is_valid_name(name):
                continue

            if any(k in role for k in role_keywords):
                people.append(f"{name} | {lines[i+1].strip()}")

    return list(set(people))[:8]

# -------------------------------
# PROJECT DETECTION
# -------------------------------
def extract_projects(pages):
    keywords = [
        "bridge", "tunnel", "geotechnical",
        "structural", "rail", "highway",
        "infrastructure"
    ]

    found = set()

    for page in pages:
        text = page["markdown"].lower()

        for k in keywords:
            if k in text:
                found.add(k)

    return list(found)

# -------------------------------
# TEXT COMBINE
# -------------------------------
def extract_company_text(pages):
    combined = ""

    for page in pages[:10]:
        combined += page["markdown"][:4000]

    return combined[:25000]

# -------------------------------
# LLM ANALYSIS
# -------------------------------
def analyze(company, text, people, projects):
    if not people:
        people_text = "No engineers found on website"
    else:
        people_text = people

    prompt = f"""
Company: {company}

Website Data:
{text}

Engineers:
{people_text}

Projects:
{projects}

Analyze:

1. What the company does
2. Engineering capabilities
3. Relevant engineers (if any)
4. Where FEM is used
5. Sales opportunities

If no engineers found, clearly say that.
Do NOT invent names.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a structural engineering sales expert."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=900
    )

    return response.choices[0].message.content

# -------------------------------
# UI
# -------------------------------
st.title("🚀 MIDAS Sales Intelligence Tool (Clean Engineer Detection)")

website = st.text_input("Enter Company Website URL")

if st.button("Run Analysis"):

    if not website:
        st.warning("Please enter a website URL")
        st.stop()

    if not website.startswith("http"):
        website = "https://" + website

    with st.spinner("🌐 Crawling website..."):
        pages = crawl_site(website)

    st.write(f"🔎 Pages crawled: {len(pages)}")

    if not pages:
        st.error("❌ Website blocked or not accessible.")
        st.stop()

    company = extract_company_name(pages, website)

    st.subheader("🏢 Company")
    st.write(company)

    people = extract_people(pages)
    projects = extract_projects(pages)
    text = extract_company_text(pages)

    with st.spinner("🧠 Analyzing..."):
        result = analyze(company, text, people, projects)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👷 Engineers")
        if people:
            st.write(people)
        else:
            st.write("No engineers found on website")

        st.subheader("🏗️ Projects")
        st.write(projects)

    with col2:
        st.subheader("📊 Insights")
        st.write(result)
