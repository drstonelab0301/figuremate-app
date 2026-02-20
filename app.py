import streamlit as st
import fitz  # PyMuPDF
import openai
import base64
import requests
import re
from datetime import datetime

# ============================================================
# 1. PAGE CONFIG & PREMIUM CSS
# ============================================================
st.set_page_config(
    page_title="FigureMate AI - Pro",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

    html, body, [class*="css"] {
        font-family: 'Pretendard', 'Inter', -apple-system, system-ui, sans-serif !important;
    }
    .stMarkdown p, .stMarkdown li {
        font-size: 1.1rem !important;
        line-height: 1.75 !important;
        color: #334155 !important;
        margin-bottom: 1.2rem !important;
    }
    h1, h2, h3, h4 {
        color: #0f172a !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Sidebar Density */
    section[data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > div {
        gap: 0.5rem !important;
    }

    /* CTA Button */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        font-size: 0.95rem;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
        transition: all 0.3s ease;
        width: 100%;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 8px 12px -3px rgba(37, 99, 235, 0.3);
    }
    .stButton > button:disabled {
        background: #cbd5e1;
        cursor: not-allowed;
        transform: none;
        box-shadow: none;
    }

    /* Chat Input - Red Border */
    .stChatInputContainer { padding-bottom: 2rem !important; }
    .stChatInput {
        border-radius: 12px !important;
        border: 2px solid #ff4b4b !important;
        transition: box-shadow 0.2s;
    }
    .stChatInput:focus-within {
        border-color: #ff4b4b !important;
        box-shadow: 0 0 0 3px rgba(255, 75, 75, 0.1);
    }
    .chat-guide {
        background-color: #fff1f2;
        border: 1px solid #fecdd3;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        color: #9f1239;
        font-size: 0.95rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .refine-history {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        color: #166534;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# 2. UTILITY FUNCTIONS
# ============================================================

def bytes_to_base64(data, ext="png"):
    encoded = base64.b64encode(data).decode("utf-8")
    return f"data:image/{ext.replace('.', '')};base64,{encoded}"


def build_asset_list(figures):
    """Builds a text description of available figures for LLM prompts."""
    if not figures:
        return "AVAILABLE FIGURES:\n(No figures available)"
    lines = ["AVAILABLE FIGURES:"]
    for fid, data in figures.items():
        lines.append(f"- [[{fid}]]: {data['caption'][:100]}... (Source: {data['source']})")
    return "\n".join(lines)


# ============================================================
# 3. PDF INGESTION ENGINE
# ============================================================

def extract_text_and_figures(files):
    """Parses up to 5 PDFs. Limits 15k chars/doc. Filters images >100px."""
    merged_text = []
    figure_registry = {}
    global_img_count = 1

    for uploaded_file in files:
        try:
            uploaded_file.seek(0)
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")

            # Text extraction (truncated)
            chunks = [f"--- Document: {uploaded_file.name} ---"]
            total_chars = 0
            for page in doc:
                text = page.get_text()
                if total_chars + len(text) > 15000:
                    chunks.append(text[:15000 - total_chars] + "\n...(Truncated)...")
                    break
                chunks.append(text)
                total_chars += len(text)
            merged_text.append("\n".join(chunks))

            # Figure extraction
            caption_pat = re.compile(r"^(Figure|Fig)(\.|)\s*\d+", re.IGNORECASE)
            for page_num, page in enumerate(doc):
                blocks = page.get_text("blocks")
                for block in blocks:
                    text = block[4].strip()
                    if not caption_pat.match(text):
                        continue
                    caption_rect = fitz.Rect(block[:4])
                    pr = page.rect
                    roi = fitz.Rect(pr.x0 + 30, max(0, caption_rect.y0 - 450), pr.x1 - 30, caption_rect.y0)
                    try:
                        pix = page.get_pixmap(clip=roi, dpi=150)
                        if pix.width > 100 and pix.height > 100:
                            img_id = f"IMG_{global_img_count:02d}"
                            png_bytes = pix.tobytes("png")
                            figure_registry[img_id] = {
                                "id": img_id,
                                "source": uploaded_file.name,
                                "page": page_num + 1,
                                "caption": text,
                                "bytes": png_bytes,
                                "b64": bytes_to_base64(png_bytes),
                                "ext": "png"
                            }
                            global_img_count += 1
                    except Exception:
                        pass
        except Exception:
            continue

    full_text = "\n\n".join(merged_text)
    return full_text, figure_registry, len(full_text) // 4


# ============================================================
# 4. AI ORCHESTRATION (Generation + Refinement)
# ============================================================

def generate_report(api_key, text, figures, model="gpt-4o"):
    """First-pass report generation with structured prompt."""
    client = openai.OpenAI(api_key=api_key)
    asset_list = build_asset_list(figures)

    system_prompt = f"""
You are an Expert Technical Analyst.

{asset_list}

[Instruction]
Synthesize the provided documents into ONE cohesive, definitive professional technical report.
Do NOT just list summaries. Weave a compelling narrative.

[Structure - STRICTLY FOLLOW]

# [Compelling Main Title]

## 1. Introduction
(Context, Problem Statement, and Background)

## 2. Core Architecture & Methodology
(Explain the 'How'. *CRITICAL: Insert [[IMG_XX]] tags here naturally to illustrate concepts.*)

## 3. Deep Dive Analysis
(Performance, nuances, comparisons, and results.)

## 4. Conclusion & Verdict
(Final thoughts, future outlook, and takeaways.)

## 5. References
(List the source documents used in the analysis.)

[Formatting Rules]
- Use clear headings (##).
- Use bullet points (-) for listing features.
- Use bold type (**) for emphasis.
- Output format: [REPORT_MARKDOWN] ||| [DALL-E PROMPT]
"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text[:100000]}
            ],
            temperature=0.4
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


def refine_report(api_key, original_text, instruction, figures, history=None, model="gpt-4o"):
    """Context-aware refinement with figure registry re-injection and history context."""
    client = openai.OpenAI(api_key=api_key)
    asset_list = build_asset_list(figures)
    
    history_text = ""
    if history:
        history_text = "[Previous Edit History]\n" + "\n".join([f"- {h}" for h in history]) + "\n"

    system_prompt = f"""
You are a meticulous Senior Technical Editor.
Rewrite the [Original Report] below according to the [User Edit Request].

{asset_list}

{history_text}
[CRITICAL RULES]
1. Output the COMPLETE rewritten report from beginning to end. Never output only the changed section.
2. User instructions (and past history) ALWAYS OVERRIDE default formats. Maintain the language, tone, and structural format established in the [Original Report] unless requested otherwise. Do NOT force a default structure if the user asked for a custom format (e.g., brief summary, table, specific sections).
3. PRESERVE all existing [[IMG_XX]] tags. Keep them in context or move them to a better position. NEVER delete them.
4. Do NOT include conversational filler like "Sure, here's the revised version". Output ONLY raw Markdown.
"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"[Original Report]\n{original_text}\n\n[User Edit Request]\n{instruction}"}
            ],
            temperature=0.3
        )
        content = resp.choices[0].message.content.strip()
        # Strip accidental code fences
        if content.startswith("```"):
            content = re.sub(r"^```(?:markdown)?\n?", "", content)
            content = re.sub(r"\n?```$", "", content)
        return content.strip()
    except Exception as e:
        return f"Error: {e}"


def generate_hero_image(api_key, prompt_text):
    """Generates a DALL-E 3 hero image."""
    client = openai.OpenAI(api_key=api_key)
    try:
        resp = client.images.generate(
            model="dall-e-3", prompt=prompt_text[:4000],
            size="1024x1024", quality="standard", n=1
        )
        return resp.data[0].url
    except Exception:
        return None


# ============================================================
# 5. MARKDOWN EXPORT COMPILER
# ============================================================

def compile_markdown_export(blog_text, hero_b64, figure_registry):
    """Returns (preview_md, download_md) to prevent browser crash."""
    lines = []
    date_str = datetime.now().strftime("%Y-%m-%d")
    lines.append(f"# Technical Analysis Report\n**Date:** {date_str} | **By:** FigureMate AI\n\n---\n")

    if hero_b64:
        lines.append("![Hero Concept][HERO_IMG]\n\n")

    # Replace [[IMG_XX]] with reference-link syntax
    tag_pat = re.compile(r"\[\[?(IMG_\d+)\]?\]", re.IGNORECASE)

    def _replacer(m):
        img_id = m.group(1).upper()
        if img_id in figure_registry:
            d = figure_registry[img_id]
            cap = d['caption'].replace("[", "(").replace("]", ")")
            return f"\n\n![{cap}][{img_id}]\n*{cap} (Source: {d['source']})*\n\n"
        return ""

    lines.append(tag_pat.sub(_replacer, blog_text))
    lines.append("\n\n---\n### Asset References\n")

    body = "\n".join(lines)

    preview_md = body + "\n\n(Image data omitted for preview. Download full file below.)"

    download_md = body
    if hero_b64:
        download_md += f"\n[HERO_IMG]: {hero_b64}"
    for img_id, data in figure_registry.items():
        download_md += f"\n[{img_id}]: {data['b64']}"

    return preview_md, download_md


# ============================================================
# 6. SESSION STATE HELPERS
# ============================================================

def init_session_state():
    """Initializes all session state keys."""
    defaults = {
        "final_result": None,
        "refine_history": [],     # List of past refinement requests
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ============================================================
# 7. UI COMPONENTS (Modularized)
# ============================================================

def render_sidebar():
    """Renders the sidebar and returns (api_key, model, extracted_data, figure_data, generate_btn)."""
    with st.sidebar:
        st.markdown("**⚙️ Settings**")
        api_key = st.text_input("OpenAI Key", type="password", placeholder="sk-...", label_visibility="collapsed")

        col_s1, col_s2 = st.columns([2, 1])
        with col_s1:
            model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini"], index=0, label_visibility="collapsed")
        with col_s2:
            if st.button("Clear", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        st.markdown("---")
        st.markdown("**📂 Upload PDFs**")
        uploaded_files = st.file_uploader("Upload", type=["pdf"], accept_multiple_files=True, label_visibility="collapsed")

        extracted_data = None
        figure_data = {}

        if uploaded_files:
            if len(uploaded_files) > 5:
                st.error("Max 5 files.")
            else:
                names = [f.name for f in uploaded_files]
                if st.session_state.get('last_uploaded') != names:
                    with st.spinner("Analyzing..."):
                        extracted_data, figure_data, tokens = extract_text_and_figures(uploaded_files)
                        st.session_state['extracted_data'] = extracted_data
                        st.session_state['figure_data'] = figure_data
                        st.session_state['total_tokens'] = tokens
                        st.session_state['last_uploaded'] = names
                else:
                    extracted_data = st.session_state.get('extracted_data')
                    figure_data = st.session_state.get('figure_data')

                if 'total_tokens' in st.session_state:
                    c1, c2 = st.columns(2)
                    c1.caption(f"**Size**: {st.session_state['total_tokens'] // 1000}k Tok")
                    c2.caption(f"**Est**: ${(st.session_state['total_tokens'] / 1000) * 0.005:.3f}")

                if figure_data:
                    st.success(f"{len(figure_data)} Figures extracted")
                    with st.expander("View Assets"):
                        for fid, d in figure_data.items():
                            st.image(d['bytes'], caption=f"[{fid}]", use_container_width=True)
        else:
            st.caption("Upload up to 5 PDFs to begin.")

        st.markdown("---")

        api_ready = api_key and api_key.startswith("sk-")
        data_ready = extracted_data is not None
        generate_btn = st.button("🚀 GENERATE REPORT", disabled=not (api_ready and data_ready), use_container_width=True, type="primary")

        st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.8rem; margin-top:2rem;'>Powered by FigureMate AI</div>", unsafe_allow_html=True)

    return api_key, model, extracted_data, figure_data, generate_btn


def render_empty_state():
    """Renders the landing page when no report has been generated."""
    st.markdown("""
    <div style="text-align: center; margin-top: 5vh;">
        <div style="font-size: 3rem; margin-bottom: 0.5rem;">🧠</div>
        <h1 style="color: #0f172a; font-size: 2.2rem; margin-bottom: 0.5rem; letter-spacing: -1px;">FigureMate AI</h1>
        <p style="font-size: 1.1rem; color: #64748b; margin-bottom: 2rem;">Context-Aware Knowledge Synthesis Engine</p>
    </div>
    """, unsafe_allow_html=True)


def render_report_content(res):
    """Renders the generated report with interleaved images."""
    # Hero Image
    if res.get('hero_url'):
        st.image(res['hero_url'], use_container_width=True)
        st.caption("AI-Generated Conceptual Visualization")

    st.markdown("---")

    # Interleaved text + images
    content = res['blog']
    pattern = re.compile(r"(\[\[?IMG_\d+\]?\])", re.IGNORECASE)
    parts = pattern.split(content)

    for part in parts:
        tag_match = re.match(r"\[\[?(IMG_\d+)\]?\]", part, re.IGNORECASE)
        if tag_match:
            img_id = tag_match.group(1).upper()
            if img_id in res['figures']:
                data = res['figures'][img_id]
                st.markdown("<br>", unsafe_allow_html=True)
                _, col_img, _ = st.columns([1, 8, 1])
                with col_img:
                    st.image(data['bytes'], caption=f"Figure {img_id}: {data['caption']} (Source: {data['source']})", use_container_width=True)
                st.markdown("<br>", unsafe_allow_html=True)
        else:
            if part.strip():
                st.markdown(part, unsafe_allow_html=True)

    st.markdown("---")


def render_refine_section(api_key, model):
    """Renders the interactive refinement chat and history."""
    # Show refinement history
    if st.session_state.refine_history:
        for i, entry in enumerate(st.session_state.refine_history):
            st.markdown(f'<div class="refine-history">✅ <strong>이전 수정 #{i+1}:</strong> {entry}</div>', unsafe_allow_html=True)

    # Guide box
    st.markdown("""
    <div class="chat-guide">
        <span>💡</span>
        <div><strong>AI Editor Active:</strong> 결과물 미세조정 — 마음에 들지 않는 부분을 입력하면 AI가 즉시 수정합니다.</div>
    </div>
    """, unsafe_allow_html=True)

    user_instruction = st.chat_input("Ask FigureMate to refine the report...")

    if user_instruction:
        if not api_key:
            st.warning("API Key needed for refinement.")
            return

        with st.chat_message("user"):
            st.write(user_instruction)

        with st.chat_message("assistant"):
            with st.spinner("Refining content..."):
                res = st.session_state.final_result
                new_blog = refine_report(
                    api_key,
                    res['blog'],
                    user_instruction,
                    res['figures'],
                    st.session_state.refine_history,
                    model
                )

                if "Error:" not in new_blog:
                    preview_md, download_md = compile_markdown_export(new_blog, res['hero_b64'], res['figures'])
                    st.session_state.final_result['blog'] = new_blog
                    st.session_state.final_result['preview_md'] = preview_md
                    st.session_state.final_result['download_md'] = download_md
                    st.session_state.refine_history.append(user_instruction)
                    st.rerun()
                else:
                    st.error(f"Update failed: {new_blog}")


def render_export_section(res):
    """Renders the copy and download buttons."""
    with st.expander("📋 One-Click Copy"):
        st.code(res['preview_md'], language="markdown")

    col_dl, _ = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="📥 Download Markdown Report",
            data=res['download_md'],
            file_name="FigureMate_Report.md",
            mime="text/markdown",
            use_container_width=True,
            type="primary"
        )


# ============================================================
# 8. MAIN CONTROLLER
# ============================================================

def main():
    init_session_state()

    # Sidebar (returns controls)
    api_key, model, extracted_data, figure_data, generate_btn = render_sidebar()

    # Generation Pipeline
    if generate_btn:
        with st.status("🧠 전문적인 분석 문서 생성 중...", expanded=True) as status:
            st.write("📝 **Drafting** — 문서 분석 및 보고서 작성 중...")
            raw = generate_report(api_key, extracted_data, figure_data, model)

            if "Error:" not in raw:
                parts = raw.split("|||")
                blog = parts[0].strip()
                dalle_prompt = parts[1].strip() if len(parts) > 1 else "Abstract Technology"

                st.write("🎨 **Visualizing** — DALL-E 3 Hero Image 생성 중...")
                hero_url = generate_hero_image(api_key, dalle_prompt)
                hero_b64 = None
                if hero_url:
                    try:
                        hero_b64 = bytes_to_base64(requests.get(hero_url).content)
                    except Exception:
                        pass

                st.write("💾 **Assembling** — 최종 보고서 조립 중...")
                preview_md, download_md = compile_markdown_export(blog, hero_b64, figure_data)

                st.session_state.final_result = {
                    "blog": blog,
                    "hero_url": hero_url,
                    "preview_md": preview_md,
                    "download_md": download_md,
                    "figures": figure_data,
                    "hero_b64": hero_b64
                }
                st.session_state.refine_history = []
                status.update(label="✅ Complete!", state="complete", expanded=False)
            else:
                st.error(f"Analysis Failed: {raw}")

    # Rendering
    if st.session_state.final_result:
        res = st.session_state.final_result
        render_report_content(res)
        render_refine_section(api_key, model)
        render_export_section(res)
    else:
        render_empty_state()


if __name__ == "__main__":
    main()
