# AI-Powered Developer Tools Research & Analysis
This project automates the discovery, scraping, and analysis of developer tools and software products using AI.  
Given a topic or category, it searches the web for relevant tools, extracts their names, visits their official sites, produces structured and comparable data about each, along with recommendations of when it's best to use it.

### Preview
![](/preview.gif)

<br>

## ✨ Featuers
- **Automated Tool Discovery**: Expands a user query into targeted searches to find relevant tools and alternatives.

- **Web Scraping & Content Aggregation**: Uses `Firecrawl` to scrape articles and official product pages.

- **LLM-Powered Extraction**: Identifies tool names from unstructured text using OpenAI GPT-5 Mini.

- **Structured Company Analysis**: Extracts pricing, open-source status, tech stack, integrations, language support, and API availability.

---
## 🔄 Workflow 
1. **Tool Discovery** – Search the web for related tools and alternatives using `Firecrawl`.  
2. **Content Scraping** – Extract text from relevant articles and pages.  
3. **Tool Extraction** – Use GPT-5 to identify tool names from scraped text.  
4. **Company Research** – Locate and scrape official sites for each extracted tool.  
5. **Structured AI Analysis** – Analyse site content with GPT-5 Mini to extract key product details.  

## 🛠 Tech Stack

- **[LangChain](https://www.langchain.com/)** – Orchestration of LLM prompts and structured output.
- **[LangGraph](https://github.com/langchain-ai/langgraph)** – Workflow and state management.
- **[Firecrawl](https://github.com/mendableai/firecrawl)** – Search and scrape web pages for relevant data.
- **[OpenAI GPT-5 Mini](https://platform.openai.com/)** – LLM for extraction and analysis.
- **[UV](https://github.com/astral-sh/uv)** – Fast Python package installer and environment manager.
- **Python 3.10+**