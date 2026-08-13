from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain
import re


def _extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)\]>\"']+", text or "")


def _extract_urls_from_messages(messages) -> list[str]:
    seen = set()
    ordered = []

    for msg in messages or []:
        content = getattr(msg, "content", "")
        if isinstance(content, list):
            content = "\n".join(str(item) for item in content)
        urls = _extract_urls(str(content))
        for url in urls:
            if url not in seen:
                seen.add(url)
                ordered.append(url)

    return ordered

def run_research_pipeline(topic : str) -> dict:

    state = {}

    #search agent working 
    print("\n"+" ="*50)
    print("step 1 - search agent is working ...")
    print("="*50)

    search_agent = build_search_agent()
    search_result = search_agent.invoke({
        "messages" : [("user", f"Find recent, reliable and detailed information about: {topic}. Keep original source URLs verbatim.")]
    })
    state["search_results"] = search_result['messages'][-1].content
    state["source_urls"] = _extract_urls_from_messages(search_result.get("messages", []))

    print("\n search result ",state['search_results'])
    print("\n extracted source URLs ", state["source_urls"])


    #step 2 - reader agent 
    print("\n"+" ="*50)
    print("step 2 - Reader agent is scraping top resources ...")
    print("="*50)

    reader_agent = build_reader_agent()
    reader_result = reader_agent.invoke({
        "messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{state['search_results'][:4000]}"
        )]
    })

    state['scraped_content'] = reader_result['messages'][-1].content

    print("\nscraped content: \n", state['scraped_content'])


    #step 3 - writer chain 

    print("\n"+" ="*50)
    print("step 3 - Writer is drafting the report ...")
    print("="*50)

    research_combined = (
        f"SEARCH RESULTS : \n {state['search_results']} \n\n"
        f"DETAILED SCRAPED CONTENT : \n {state['scraped_content']}"
    )

    state["report"] = writer_chain.invoke({
        "topic" : topic,
        "research" : research_combined,
        "sources": "\n".join(f"- {url}" for url in state.get("source_urls", [])) or "- No URLs captured"
    })

    print("\n Final Report\n",state['report'])


    #critic report 

    print("\n"+" ="*50)
    print("step 4 - critic is reviewing the report ")
    print("="*50)

    state["feedback"] = critic_chain.invoke({
        "report":state['report']
    })

    print("\n critic report \n", state['feedback'])

    return state