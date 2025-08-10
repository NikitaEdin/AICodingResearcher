from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState, CompanyInfo, CompanyAnalysis
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts

# 1. Searching the web for relevent tools
# 2. Scraping and extracting tool names
# 3. Researching each tool individually
# 4. Performing strucrtred analysis of each tool
# 5. Returning a structured list of tools with their details

class Workflow:
    def __init__(self):
        self.firecrawl = FirecrawlService()
        self.llm = ChatOpenAI(model="gpt-5-mini", temperature=0.3)
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()

    # Build the workflow graph
    def _build_workflow(self):
        graph = StateGraph(ResearchState)
        graph.add_node("extract_tools", self._extract_tools_step)
        graph.add_node("research", self._research_step)
        graph.add_node("analyse", self._analyse_step)
        graph.set_entry_point("extract_tools")

        graph.add_edge("extract_tools", "research")
        graph.add_edge("research", "analyse")
        graph.add_edge("analyse", END)

        return graph.compile()


    # Extract tools related to the query
    def _extract_tools_step(self, state: ResearchState) -> Dict[str, Any]:
        print(f"Finding articles about: {state.query}")

        # Step 1: Search for articles related to the query
        article_query = f"{state.query} tools comparison best alternatives"
        search_reslts = self.firecrawl.search_companies(article_query, num_results=3)

        # Step 2: Scrape content from the search results
        all_content = ""
        for result in search_reslts.data:
            url = result.get("url", "")
            scraped = self.firecrawl.scrape_company_pages(url)
            if scraped:
                all_content += scraped.markdown[:1000] + "\n\n"

        # Step 3: Use LLM to extract tool names from the content
        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content))
        ]


        # Step 4: Invoke the LLM to extract tool names
        try:
            response = self.llm.invoke(messages)
            tool_names = [
                name.strip()
                for name in response.content.strip().split("\n")
                if name.strip()  # Filter out empty lines
            ]
            print(f"Extracted tools: {', '.join(tool_names[:5])}")
            return {"extracted_tools": tool_names}
        except Exception as e:
            print(e)
            return {"extracted_tools": []}


    # Analyse the content of a specific company/tool page
    def _analyse_company_content(self, company_name: str, content: str) -> CompanyAnalysis:
        # Analyse the content of a specific company/tool page
        structured_llm = self.llm.with_structured_output(CompanyAnalysis)

        # Prepare the messages for the LLM
        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name, content))
        ]

        # Invoke the LLM to analyse the content
        try:
            analysis = structured_llm.invoke(messages)
            return analysis
        except Exception as e:
            print(f"Error analysing {company_name}: {e}")
            return CompanyAnalysis(
                pricing_model="Unknown",
                is_open_source=None,
                tech_stack=[],
                description="Failed",
                api_available=None,
                language_support=[],
                integration_capabilities=[]
            )

    # Research each tool individually
    def _research_step(self, state: ResearchState) -> Dict[str, Any]:
        extracted_tools = getattr(state, "extracted_tools", [])

        if not extracted_tools:
            print("No extracted tools found, skipping analysis.")
            search_results = self.firecrawl.search_companies(state.query, num_results=3)

            tool_names = [
                result.get("metadata", {}).get("title", "Unknown")
                for result in search_results.data
            ]
        else:
            tool_names = extracted_tools[:4]
        
        print(f"Researching specific tools: {', '.join(tool_names)}")

        companies = []
        for tool_name in tool_names:
            tool_search_results = self.firecrawl.search_companies(tool_name + " official site", num_results=1)

            if tool_search_results:
                result = tool_search_results.data[0]
                url = result.get("url", "")

                company = CompanyInfo(
                    name=tool_name,
                    description=result.get("markdown", ""),
                    website=url,
                    tech_stack=[],
                    competitors=[]
                )

                scraped = self.firecrawl.scrape_company_pages(url)
                if scraped:
                    content = scraped.markdown[:2500]  # Limit to first 2500 characters
                    analysis = self._analyse_company_content(company.name, content)

                    # Update the company info with analysis results
                    company.pricing_model = analysis.pricing_model
                    company.is_open_source = analysis.is_open_source
                    company.tech_stack = analysis.tech_stack
                    company.description = analysis.description
                    company.api_available = analysis.api_available
                    company.language_support = analysis.language_support
                    company.integration_capabilities = analysis.integration_capabilities

                companies.append(company)

        return {"comapnies": companies}
    
    # Perform structured analysis of each tool
    def _analyse_step(self, state: ResearchState) -> Dict[str, Any]:
        print("Generating recommendations")

        company_data = ", ".join([
            company.model_dump_json() for company in state.companies 
        ])

        messages = [
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query, company_data))
        ]

        response = self.llm.invoke(messages)
        return {"analysis": response.content}

    # Run the workflow with a given query
    def run(self, query: str) -> ResearchState:
        initial_state = ResearchState(query=query)
        final_state = self.workflow.invoke(initial_state)
        return ResearchState(**final_state)
                    
