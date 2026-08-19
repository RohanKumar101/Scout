import html
import re
import time

import streamlit as st

from src.agents.agents import build_reader_agent, build_search_agent, critic_chain, writer_chain


st.set_page_config(
    page_title="Scout — AI Research Agent",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="collapsed",
)


STEPS = [
    {
        "key": "search",
        "number": "01",
        "icon": "⌕",
        "title": "Discover",
        "desc": "Finds timely, credible sources across the web.",
        "spinner": "Discovering reliable sources…",
        "complete": "Sources found",
    },
    {
        "key": "reader",
        "number": "02",
        "icon": "◫",
        "title": "Read",
        "desc": "Extracts detail from the most useful source.",
        "spinner": "Reading the strongest source…",
        "complete": "Source read",
    },
    {
        "key": "writer",
        "number": "03",
        "icon": "✦",
        "title": "Synthesize",
        "desc": "Turns the research into a structured report.",
        "spinner": "Writing your research brief…",
        "complete": "Brief drafted",
    },
    {
        "key": "critic",
        "number": "04",
        "icon": "✓",
        "title": "Review",
        "desc": "Checks the report for rigor and clarity.",
        "spinner": "Reviewing the research brief…",
        "complete": "Quality checked",
    },
]
STEP_KEYS = [step["key"] for step in STEPS]

EXAMPLES = [
    "Future of LLMs in the technology industry",
    "The latest AI agents and their practical uses",
    "A five-year roadmap for AGI development",
]


st.markdown(
    """
    <style>
    :root {
        --ink: #182230;
        --muted: #667085;
        --quiet: #98a2b3;
        --line: #e6eaf0;
        --canvas: #f7f8fc;
        --panel: #ffffff;
        --subtle: #f8faff;
        --brand: #5458e8;
        --brand-dark: #4145ce;
        --brand-soft: #eef0ff;
        --success: #14805e;
        --success-soft: #eaf8f2;
        --danger: #d44747;
        --danger-soft: #fff1f1;
        --shadow: 0 16px 40px rgba(28, 39, 62, .08);
    }

    html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    .stApp { background: var(--canvas); color: var(--ink); }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { max-width: 1240px; padding: 1.35rem 2.4rem 3.5rem; }
    *:focus-visible { outline: 3px solid rgba(84, 88, 232, .28) !important; outline-offset: 2px; }

    /* App shell */
    .topbar { display: flex; align-items: center; justify-content: space-between; padding: .25rem 0 1.5rem; }
    .brand { display: flex; align-items: center; gap: .7rem; color: var(--ink); font-weight: 750; font-size: 1.02rem; letter-spacing: -.025em; }
    .brand-mark { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 11px; background: linear-gradient(135deg, #686bff, #4447bf); color: white; font-size: 1rem; box-shadow: 0 8px 16px rgba(84, 88, 232, .25); }
    .topbar-note { display: flex; align-items: center; gap: .45rem; color: var(--muted); font-size: .82rem; }
    .status-dot { width: 7px; height: 7px; background: #1bae76; border-radius: 99px; box-shadow: 0 0 0 4px #e7f7ef; }

    .hero { max-width: 760px; padding: 1.3rem 0 2.2rem; }
    .eyebrow { display: inline-flex; align-items: center; gap: .4rem; color: var(--brand); background: var(--brand-soft); padding: .35rem .62rem; border-radius: 999px; font-size: .7rem; font-weight: 750; letter-spacing: .075em; text-transform: uppercase; }
    .hero h1 { color: var(--ink); font-size: clamp(2rem, 4.2vw, 3.5rem); letter-spacing: -.055em; line-height: 1.06; margin: .8rem 0 .75rem; font-weight: 750; }
    .hero p { max-width: 620px; color: var(--muted); font-size: 1.02rem; line-height: 1.65; margin: 0; }
    .hero strong { color: var(--ink); font-weight: 650; }

    /* Surfaces */
    div[class*="st-key-research_card"], div[class*="st-key-agent_board"],
    div[class*="st-key-report_card"], div[class*="st-key-review_card"],
    div[class*="st-key-error_card"] {
        background: var(--panel); border: 1px solid var(--line); border-radius: 18px;
        box-shadow: var(--shadow); padding: 1.35rem !important;
    }
    div[class*="st-key-research_card"] { padding: 1.55rem !important; }
    div[class*="st-key-error_card"] { border-color: #ffd5d5; background: var(--danger-soft); margin-top: 1.2rem; }
    div[class*="st-key-report_card"] { border-color: #dfe1ff; }
    div[class*="st-key-review_card"] { border-color: #d9eee5; background: #fcfffd; }

    .section-label { color: var(--brand); font-size: .7rem; font-weight: 750; letter-spacing: .1em; text-transform: uppercase; }
    .section-title { color: var(--ink); margin: .3rem 0 .25rem; font-size: 1.12rem; font-weight: 720; letter-spacing: -.025em; }
    .section-copy { color: var(--muted); font-size: .84rem; line-height: 1.5; margin: 0 0 1.2rem; }
    .divider { height: 1px; background: var(--line); margin: 2rem 0; }

    /* Prompt form */
    .stTextArea > label { color: var(--ink) !important; font-size: .88rem !important; font-weight: 700 !important; }
    .stTextArea textarea { min-height: 116px !important; padding: .9rem 1rem !important; resize: vertical !important; border: 1px solid #d8dfea !important; background: #fff !important; color: var(--ink) !important; border-radius: 12px !important; font-size: .95rem !important; line-height: 1.55 !important; box-shadow: none !important; }
    .stTextArea textarea:focus { border-color: var(--brand) !important; box-shadow: 0 0 0 4px rgba(84, 88, 232, .12) !important; }
    .stTextArea textarea::placeholder { color: #98a2b3 !important; }
    .input-helper { color: var(--muted); font-size: .76rem; line-height: 1.5; margin: .6rem 0 1.2rem; }
    .stButton > button { min-height: 2.9rem !important; border-radius: 10px !important; font-weight: 700 !important; transition: transform .15s ease, box-shadow .15s ease, background .15s ease !important; }
    div[class*="st-key-run_research"] .stButton > button, div[class*="st-key-run_research"] button {
        color: #fff !important; background: var(--brand) !important; border: 1px solid var(--brand) !important; box-shadow: 0 8px 18px rgba(84, 88, 232, .2) !important;
    }
    div[class*="st-key-run_research"] .stButton > button:hover:not(:disabled), div[class*="st-key-run_research"] button:hover:not(:disabled) { background: var(--brand-dark) !important; transform: translateY(-1px); box-shadow: 0 10px 22px rgba(84, 88, 232, .28) !important; }
    .stButton > button:disabled { opacity: .58 !important; }
    .example-caption { color: var(--quiet); font-size: .72rem; font-weight: 650; letter-spacing: .06em; text-transform: uppercase; margin: 1.1rem 0 .55rem; }
    div[class*="st-key-example_buttons"] .stButton > button, div[class*="st-key-new_research"] .stButton > button, div[class*="st-key-retry"] .stButton > button {
        background: var(--panel) !important; color: #475467 !important; border: 1px solid #dde3ed !important; box-shadow: none !important; font-size: .78rem !important; padding: .45rem .7rem !important;
    }
    div[class*="st-key-example_buttons"] .stButton > button:hover:not(:disabled), div[class*="st-key-new_research"] .stButton > button:hover:not(:disabled) { background: var(--brand-soft) !important; border-color: #c9ccff !important; color: var(--brand) !important; }

    /* Research plan and agent cards */
    .plan-head { display: flex; align-items: center; justify-content: space-between; padding-bottom: .85rem; border-bottom: 1px solid var(--line); margin-bottom: .95rem; }
    .plan-count { color: var(--success); background: var(--success-soft); border-radius: 999px; padding: .22rem .48rem; font-size: .7rem; font-weight: 700; }
    .agent-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .7rem; }
    .agent { min-height: 128px; position: relative; box-sizing: border-box; padding: .85rem; background: #fbfcfe; border: 1px solid var(--line); border-radius: 13px; }
    .agent.active { background: #f4f5ff; border-color: #bfc2ff; box-shadow: 0 6px 16px rgba(84, 88, 232, .08); }
    .agent.complete { background: #f8fffb; border-color: #c9ebdd; }
    .agent.failed { background: #fff8f8; border-color: #ffd0d0; }
    .agent-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: .8rem; }
    .agent-number { color: var(--quiet); font-size: .68rem; font-weight: 750; letter-spacing: .08em; }
    .agent-icon { width: 27px; height: 27px; border-radius: 8px; display: grid; place-items: center; background: #eef1f6; color: #596579; font-size: .9rem; font-weight: 750; }
    .agent.active .agent-icon { color: var(--brand); background: #e2e4ff; }
    .agent.complete .agent-icon { color: var(--success); background: #dff5eb; }
    .agent.failed .agent-icon { color: var(--danger); background: #ffe5e5; }
    .agent-name { color: var(--ink); font-size: .87rem; font-weight: 720; letter-spacing: -.01em; }
    .agent-copy { color: var(--muted); font-size: .73rem; line-height: 1.42; margin: .25rem 0 .65rem; }
    .agent-state { position: absolute; bottom: .75rem; left: .85rem; color: var(--quiet); font-size: .68rem; font-weight: 650; }
    .agent.active .agent-state { color: var(--brand); }
    .agent.complete .agent-state { color: var(--success); }
    .agent.failed .agent-state { color: var(--danger); }
    .pulse { display: inline-block; width: 6px; height: 6px; margin-right: .32rem; border-radius: 50%; background: currentColor; animation: pulse 1.35s infinite; }
    @keyframes pulse { 50% { opacity: .35; transform: scale(.7); } }
    .board-foot { display: flex; align-items: center; gap: .5rem; color: var(--muted); font-size: .74rem; margin-top: 1rem; }
    .board-progress { height: 5px; flex: 1; background: #edf0f5; border-radius: 999px; overflow: hidden; }
    .board-progress > span { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, #575be8, #7c80f4); transition: width .35s ease; }

    /* Results */
    .results-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; }
    .results-heading h2 { color: var(--ink); font-size: 1.45rem; letter-spacing: -.035em; margin: 0; }
    .results-topic { color: var(--muted); font-size: .84rem; line-height: 1.5; margin: .35rem 0 0; }
    .result-kicker { display: flex; align-items: center; gap: .45rem; color: var(--brand); font-size: .7rem; font-weight: 750; letter-spacing: .095em; text-transform: uppercase; margin-bottom: .75rem; }
    .result-kicker.review { color: var(--success); }
    div[class*="st-key-report_card"] .stMarkdown, div[class*="st-key-review_card"] .stMarkdown { color: #475467; font-size: .94rem; line-height: 1.75; }
    div[class*="st-key-report_card"] .stMarkdown h1, div[class*="st-key-report_card"] .stMarkdown h2, div[class*="st-key-report_card"] .stMarkdown h3, div[class*="st-key-review_card"] .stMarkdown h1, div[class*="st-key-review_card"] .stMarkdown h2, div[class*="st-key-review_card"] .stMarkdown h3 { color: var(--ink); letter-spacing: -.025em; }
    .stDownloadButton > button { color: var(--brand) !important; background: #fff !important; border: 1px solid #cfd2ff !important; border-radius: 9px !important; font-size: .8rem !important; font-weight: 700 !important; margin-top: .8rem; box-shadow: none !important; }
    .stDownloadButton > button:hover { background: var(--brand-soft) !important; }
    .raw-label { color: var(--muted); font-size: .75rem; font-weight: 700; letter-spacing: .065em; text-transform: uppercase; margin: 1.75rem 0 .65rem; }
    details { background: var(--panel); border: 1px solid var(--line); border-radius: 11px; box-shadow: none; margin-bottom: .6rem; }
    details summary { color: #475467 !important; font-size: .82rem !important; font-weight: 650 !important; padding: .78rem .9rem !important; }
    .raw-output { color: #475467; background: #f8fafc; border: 1px solid #edf0f5; border-radius: 8px; white-space: pre-wrap; overflow-wrap: anywhere; max-height: 370px; overflow-y: auto; padding: .85rem; font: .75rem/1.65 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }
    .error-title { color: #a92b2b; font-size: .95rem; font-weight: 750; margin-bottom: .25rem; }
    .error-copy { color: #813c3c; font-size: .84rem; line-height: 1.55; margin-bottom: .9rem; }
    .footer { color: var(--quiet); text-align: center; font-size: .74rem; padding-top: 2.75rem; }
    .stSpinner > div { border-top-color: var(--brand) !important; }

    @media (max-width: 820px) {
        .block-container { padding: 1rem 1rem 2.5rem; }
        .topbar { padding-bottom: 1rem; }
        .topbar-note { font-size: .72rem; }
        .hero { padding: .75rem 0 1.55rem; }
        .hero h1 { font-size: 2.15rem; }
        .hero p { font-size: .93rem; }
        div[data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 1rem !important; }
        div[data-testid="stColumn"] { min-width: 100% !important; flex: 1 1 100% !important; }
        div[class*="st-key-research_card"], div[class*="st-key-agent_board"], div[class*="st-key-report_card"], div[class*="st-key-review_card"] { padding: 1.1rem !important; }
    }
    @media (max-width: 480px) {
        .topbar-note { display: none; }
        .hero h1 { font-size: 1.9rem; }
        .agent-grid { grid-template-columns: 1fr; }
        .agent { min-height: 116px; }
        .results-heading { align-items: stretch; flex-direction: column; }
        .stTextArea textarea { min-height: 104px !important; }
    }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; transition-duration: .01ms !important; } }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state():
    defaults = {
        "results": {},
        "running": False,
        "done": False,
        "error": None,
        "last_topic": "",
        "topic_input": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_state()


def use_example(example: str):
    st.session_state.topic_input = example


def start_run():
    st.session_state.results = {}
    st.session_state.running = True
    st.session_state.done = False
    st.session_state.error = None
    st.session_state.last_topic = st.session_state.topic_input.strip()


def reset_all():
    st.session_state.results = {}
    st.session_state.running = False
    st.session_state.done = False
    st.session_state.error = None
    st.session_state.last_topic = ""
    st.session_state.topic_input = ""


def retry_pending_step():
    st.session_state.error = None
    st.session_state.running = True


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://[^\s)\]>\"']+", text or "")


def normalize_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text_value = item.get("text")
                if text_value is not None:
                    parts.append(str(text_value))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(content, dict):
        text_value = content.get("text")
        if text_value is not None:
            return str(text_value)
    return str(content)


def extract_urls_from_messages(messages) -> list[str]:
    seen = set()
    ordered = []
    for msg in messages or []:
        content = getattr(msg, "content", "")
        text = normalize_content(content)
        for url in extract_urls(text):
            if url not in seen:
                seen.add(url)
                ordered.append(url)
    return ordered


def run_step(step_key: str, topic: str, results: dict):
    if step_key == "search":
        agent = build_search_agent()
        response = agent.invoke(
            {"messages": [("user", f"Find recent, reliable and detailed information about: {topic}. Keep original source URLs verbatim.")]}
        )
        search_text = normalize_content(response["messages"][-1].content)
        source_urls = extract_urls_from_messages(response.get("messages", []))
        return {"text": search_text, "source_urls": source_urls}

    if step_key == "reader":
        agent = build_reader_agent()
        search_payload = results["search"]
        search_text = normalize_content(search_payload["text"] if isinstance(search_payload, dict) else search_payload)
        response = agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"Based on the following search results about '{topic}', pick the most relevant URL and scrape it for deeper content.\n\n"
                        f"Search Results:\n{search_text[:4000]}",
                    )
                ]
            }
        )
        return normalize_content(response["messages"][-1].content)

    if step_key == "writer":
        search_payload = results["search"]
        search_text = normalize_content(search_payload["text"] if isinstance(search_payload, dict) else search_payload)
        source_urls = search_payload.get("source_urls", []) if isinstance(search_payload, dict) else []
        research = f"SEARCH RESULTS:\n{search_text}\n\nDETAILED SCRAPED CONTENT:\n{normalize_content(results['reader'])}"
        sources = "\n".join(f"- {url}" for url in source_urls) or "- No URLs captured"
        return writer_chain.invoke({"topic": topic, "research": research, "sources": sources})

    if step_key == "critic":
        return critic_chain.invoke({"report": results["writer"]})

    raise ValueError(f"Unknown step: {step_key}")


def get_step_state(step_key: str, results: dict, running: bool, error: str | None) -> str:
    if step_key in results:
        return "complete"
    index = STEP_KEYS.index(step_key)
    previous_complete = all(key in results for key in STEP_KEYS[:index])
    if previous_complete and error:
        return "failed"
    if previous_complete and running:
        return "active"
    return "waiting"


def render_agent_board(results: dict, running: bool, error: str | None) -> str:
    cards = []
    for step in STEPS:
        state = get_step_state(step["key"], results, running, error)
        if state == "complete":
            state_text = step["complete"]
        elif state == "active":
            state_text = '<span class="pulse"></span>Working now'
        elif state == "failed":
            state_text = "Needs attention"
        else:
            state_text = "Queued"
        cards.append(
            f'''<div class="agent {state}">
                <div class="agent-top"><span class="agent-number">AGENT {step['number']}</span><span class="agent-icon">{step['icon']}</span></div>
                <div class="agent-name">{step['title']}</div>
                <div class="agent-copy">{step['desc']}</div>
                <div class="agent-state">{state_text}</div>
            </div>'''
        )
    completed = len(results)
    progress = int(completed / len(STEPS) * 100)
    board_status = "Complete" if completed == len(STEPS) else f"{completed} of {len(STEPS)} complete"
    return f'''<div class="agent-grid">{"".join(cards)}</div>
        <div class="board-foot"><div class="board-progress"><span style="width:{progress}%"></span></div><span>{board_status}</span></div>'''


# App header
st.markdown(
    """
    <div class="topbar">
        <div class="brand"><span class="brand-mark">⌕</span><span>Scout</span></div>
        <div class="topbar-note"><span class="status-dot"></span>Research system online</div>
    </div>
    <section class="hero">
        <span class="eyebrow">AI research workspace</span>
        <h1>From question to a trusted brief.</h1>
        <p>Give <strong>Scout</strong> a topic. Four specialist agents discover sources, read deeply, synthesize the evidence, and review the final report.</p>
    </section>
    """,
    unsafe_allow_html=True,
)


input_column, board_column = st.columns([1.35, 1], gap="large")

with input_column:
    with st.container(key="research_card"):
        st.markdown('<div class="section-label">New research</div><div class="section-title">What would you like to understand?</div><p class="section-copy">Be specific about the subject, time period, or angle you care about.</p>', unsafe_allow_html=True)
        topic = st.text_area(
            "Research question",
            placeholder="For example: How are AI agents changing software development teams in 2026?",
            key="topic_input",
            label_visibility="visible",
            disabled=st.session_state.running,
        )
        st.markdown('<div class="input-helper">Scout searches current sources and creates a downloadable, structured research brief.</div>', unsafe_allow_html=True)
        with st.container(key="run_research"):
            run_button = st.button(
                "Start research  →" if not st.session_state.running else "Research in progress…",
                use_container_width=True,
                disabled=st.session_state.running,
            )

    with st.container(key="example_buttons"):
        st.markdown('<div class="example-caption">Or try a suggested question</div>', unsafe_allow_html=True)
        example_columns = st.columns(3, gap="small")
        for index, example in enumerate(EXAMPLES):
            with example_columns[index]:
                st.button(
                    example,
                    key=f"example_{index}",
                    on_click=use_example,
                    args=(example,),
                    use_container_width=True,
                    disabled=st.session_state.running,
                )

with board_column:
    with st.container(key="agent_board"):
        completed_count = len(st.session_state.results)
        st.markdown(
            f'''<div class="plan-head"><div><div class="section-label">Research plan</div><div class="section-title">Your agent team</div></div>
            <span class="plan-count">{completed_count}/4 done</span></div>''',
            unsafe_allow_html=True,
        )
        st.markdown(
            render_agent_board(st.session_state.results, st.session_state.running, st.session_state.error),
            unsafe_allow_html=True,
        )


if run_button:
    if not topic.strip():
        st.warning("Enter a research question to begin.")
    else:
        start_run()
        st.rerun()


if st.session_state.error and not st.session_state.running:
    with st.container(key="error_card"):
        st.markdown('<div class="error-title">One of the agents needs another try</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="error-copy">{html.escape(st.session_state.error)}</div>', unsafe_allow_html=True)
        with st.container(key="retry"):
            st.button("Retry this step", on_click=retry_pending_step)


# Run one stage per Streamlit rerun so progress is visible and recoverable.
if st.session_state.running and not st.session_state.done and not st.session_state.error:
    results = st.session_state.results
    pending = next((step for step in STEPS if step["key"] not in results), None)
    if pending is None:
        st.session_state.running = False
        st.session_state.done = True
        st.rerun()
    try:
        with st.spinner(pending["spinner"]):
            results[pending["key"]] = run_step(pending["key"], st.session_state.last_topic, results)
        st.session_state.results = results
        st.rerun()
    except Exception as exc:
        st.session_state.running = False
        st.session_state.error = f"{pending['title']} agent failed: {exc}"
        st.rerun()


results = st.session_state.results
if results:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    heading_column, action_column = st.columns([5, 1.45], vertical_alignment="bottom")
    with heading_column:
        safe_topic = html.escape(st.session_state.last_topic)
        st.markdown(
            f'<div class="results-heading"><div><h2>Research brief</h2><p class="results-topic">{safe_topic} · {len(results)} of {len(STEPS)} agents complete</p></div></div>',
            unsafe_allow_html=True,
        )
    with action_column:
        with st.container(key="new_research"):
            st.button("New research", on_click=reset_all, use_container_width=True)

    if "writer" in results:
        with st.container(key="report_card"):
            st.markdown('<div class="result-kicker">✦ Synthesis complete</div>', unsafe_allow_html=True)
            st.markdown(normalize_content(results["writer"]))
            filename_topic = re.sub(r"[^a-z0-9]+", "_", st.session_state.last_topic.lower()).strip("_")[:45] or "research"
            st.download_button(
                label="Download report (.pdf)",
                data=normalize_content(results["writer"]),
                file_name=f"{filename_topic}_research_brief.pdf",
                mime="application/pdf",
            )

    if "critic" in results:
        with st.container(key="review_card"):
            st.markdown('<div class="result-kicker review">✓ Independent review</div>', unsafe_allow_html=True)
            st.markdown(normalize_content(results["critic"]))

    if "search" in results or "reader" in results:
        st.markdown('<div class="raw-label">Research trail</div>', unsafe_allow_html=True)
        if "search" in results:
            search_payload = results["search"]
            search_text = normalize_content(search_payload["text"] if isinstance(search_payload, dict) else search_payload)
            with st.expander("Discover agent — source notes", expanded=False):
                st.markdown(f'<div class="raw-output">{html.escape(search_text)}</div>', unsafe_allow_html=True)
            if isinstance(search_payload, dict) and search_payload.get("source_urls"):
                with st.expander("Discover agent — extracted URLs", expanded=False):
                    st.markdown(
                        '<div class="raw-output">'
                        + html.escape("\n".join(search_payload["source_urls"]))
                        + "</div>",
                        unsafe_allow_html=True,
                    )
        if "reader" in results:
            with st.expander("Read agent — extracted notes", expanded=False):
                st.markdown(f'<div class="raw-output">{html.escape(normalize_content(results["reader"]))}</div>', unsafe_allow_html=True)


st.markdown('<div class="footer">Scout · a four-agent research workflow</div>', unsafe_allow_html=True)
