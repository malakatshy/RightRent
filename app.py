from openai import OpenAI
import streamlit as st
import fitz
import io
import base64

def display_pdf(pdf_bytes):
    """Embeds the PDF in an iframe for viewing in the browser."""
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


def highlight_pdf(original_pdf_bytes, analysis_json):
    import json
    clean_json = analysis_json.replace("```json", "").replace("```", "").strip()
    risks = json.loads(clean_json)

    doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")

    color_map = {
        "High": (1, 0, 0), "Medium": (1, 1, 0), "Low": (0.7, 1, 0.7)
    }

    for risk in risks:
        quote = risk.get("exact_quote", "").strip()
        color = color_map.get(risk.get("risk_level"), (1, 1, 0))

        if len(quote) > 3:
            for page in doc:
                text_instances = page.search_for(quote)

                # ניסיון שני: אם לא נמצא, נחפש רק את 20 התווים הראשונים של הציטוט
                if not text_instances and len(quote) > 20:
                    text_instances = page.search_for(quote[:20])

                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=color)
                    highlight.update()

    output_stream = io.BytesIO()
    output_stream.write(doc.tobytes())
    doc.close()
    return output_stream.getvalue()

# Initialize the DeepSeek client using the API key from secrets
client = OpenAI(
    api_key=st.secrets["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)


def analyze_contract(contract_text, user_prefs):
    """
    Analyzes the contract using Retrieval-Augmented Generation (RAG).
    Cross-references the contract with legal_context.txt using DeepSeek-R1.
    """
    # 1. Load the Israeli Legal Context (Ground Truth)
    try:
        with open("legal_context.txt", "r", encoding="utf-8") as f:
            legal_knowledge = f.read()
    except FileNotFoundError:
        # Fallback if file is missing (crucial for stability)
        legal_knowledge = "Landlord must fix structural issues. Cash deposit max 3 months. Fair Rental Law 2017 applies."

    # 2. Craft the High-Precision RAG Prompt
    # We include numerical instructions to ensure the budget check is performed.
    system_prompt = f"""
    You are an elite Israeli Legal AI Assistant. Your goal is to find 'Gaps' between the Tenant's Preferences and the Rental Contract.

    ### LEGAL KNOWLEDGE BASE (Your Ground Truth):
    {legal_knowledge}

    ### TENANT PREFERENCES:
    {user_prefs}

    ### OPERATIONAL RULES:
    1. NUMERICAL AUDIT: Extract the rent price from the contract and compare it to the user's budget.
    2. CITATION: If a clause violates a law from the Knowledge Base, name the Chapter/Article.
    3. JSON OUTPUT: You MUST return ONLY a JSON list of objects. No prose, no conversation.

    Each JSON object must contain:
    - "issue_name": Short title.
    - "risk_level": "High", "Medium", or "Low".
    - "exact_quote": The EXACT sentence from the contract (used for PDF highlighting).
    - "explanation": Why it is a risk/violation.
    - "negotiation_tip": How to fix it with the landlord.
    
    CRITICAL: You must explicitly check every user preference. For example, if 'pets' is High Importance and the
    contract says 'No animals', you MUST include it as a Medium risk issue with the exact quote.
    """

    # 3. Call DeepSeek-R1 (The Reasoner)
    # Using 'deepseek-reasoner' triggers the Chain-of-Thought needed for legal logic.
    response = client.chat.completions.create(
        model="deepseek-reasoner",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CONTRACT TEXT TO ANALYZE:\n{contract_text}"},
        ],
        stream=False
    )

    # Returning the full message content (DeepSeek-R1 provides the reasoning and final text)
    return response.choices[0].message.content



def extract_text_from_pdf(uploaded_file):
    """
    Reads the uploaded PDF file and extracts text from every page.
    """
    # Open the PDF directly from the Streamlit UploadedFile object
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = ""

    for page in doc:
        full_text += page.get_text()

    doc.close()
    return full_text

# --- Page Configuration ---
st.set_page_config(
    page_title="RightRent - Rental Agreement Analysis", 
    page_icon="icon_page.png",
    layout="wide" 
)

# --- Updated CSS for Logo Safety and Layout ---
st.markdown("""
    <style>
        /* Increase top padding to prevent logo clipping */
        .block-container {
            padding-top: 3.5rem; 
            padding-bottom: 1rem;
        }
        /* Vertical alignment for the header */
        [data-testid="column"] {
            display: flex;
            align-items: center;
        }
        /* Tighten headers */
        h1 { margin-top: 0px !important; padding-top: 5px; }
        h3 { margin-bottom: 0px !important; }
        
        /* General gap control */
        [data-testid="stVerticalBlock"] {
            gap: 0.7rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'user_prefs' not in st.session_state:
    st.session_state.user_prefs = {}

# --- Navigation ---
def go_to_step(step_number):
    st.session_state.step = step_number
    st.rerun()

# ==========================================
# Step 1: Welcome & Homepage
# ==========================================
if st.session_state.step == 1:
    # --- Top Navigation Bar ---
    header_left, header_right = st.columns([8, 2])
    with header_left:
        # Adjusted column widths for better logo/text proximity
        col_icon, col_brand = st.columns([0.4, 10])
        with col_icon:
            st.image("icon_page.png", width=35)
        with col_brand:
            # Removed negative margin to prevent top-clipping
            st.markdown("<h3 style='color: #2E7D32; font-weight: 600; line-height: 1;'>RightRent</h3>", unsafe_allow_html=True)
    with header_right:
        st.markdown("<p style='text-align: right; color: black; font-weight: 500; margin: 0;'>About / Help</p>", unsafe_allow_html=True)

    # --- Hero Section ---
    st.markdown("<h1 style='text-align: center; font-size: 42px; font-weight: 700;'>Understand your rental <br> contract with confidence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; font-size: 19px;'>AI-powered highlights, personalised risk analysis, and guided <br> negotiation messaging.</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 10px;'></div>", unsafe_allow_html=True)

    # --- Feature Cards ---
    c_pad1, c1, c2, c3, c_pad2 = st.columns([1, 3, 3, 3, 1])
    
    with c1:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>⚙️</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Preferences setup</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 15px;'>Tell us what matters so the AI can personalize the review</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>📄</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Contract upload</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 15px;'>We analyse risks, mismatches, and unclear terms</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>👁️</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Review & negotiation</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 15px;'>See AI-highlighted clauses and draft your message</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin: 15px;'></div>", unsafe_allow_html=True)

    # --- Centered Start Button ---
    b_left, b_center, b_right = st.columns([2, 1, 2])
    with b_center:
        if st.button("Start now", use_container_width=True, type="primary"):
            go_to_step(2)

    # Disclaimer
    st.markdown("<div style='margin-top: 20px;'><hr></div>", unsafe_allow_html=True)
    st.caption("RightRent is an AI tool and does not provide legal advice. Always review your final contract with a professional.")

# ==========================================
# Step 2: Personal Preferences
# ==========================================
elif st.session_state.step == 2:
    # Header
    header_left, header_right = st.columns([8, 2])
    with header_left:
        col_icon, col_brand = st.columns([0.4, 10])
        with col_icon: st.image("icon_page.png", width=35)
        with col_brand: st.markdown("<h3 style='color: #2E7D32; font-weight: 600; line-height: 1;'>RightRent</h3>", unsafe_allow_html=True)

    st.markdown("<h1 style='font-size: 32px;'>Tell us what matters to you</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: gray; font-size: 17px;'>Your preferences help identify clauses that may not match your needs.</p>", unsafe_allow_html=True)

    # Main Grid
    col_ratings, col_budget = st.columns([1.6, 1])

    with col_ratings:
        st.markdown("<div style='border: 1px solid #E6E9EF; padding: 15px; border-radius: 10px; background-color: white;'><b>Importance ratings</b></div>", unsafe_allow_html=True)
        
        def importance_row(label, key, help_text):
            c_label, c_input = st.columns([2, 1])
            with c_label:
                st.markdown(f"<p style='margin-top: 12px; font-size: 15px;'>{label} <span title='{help_text}' style='cursor: help; color: #2E7D32;'>(?)</span></p>", unsafe_allow_html=True)
            with c_input:
                return st.radio(label, ["Low", "Medium", "High"], key=key, horizontal=True, label_visibility="collapsed")

        rent_inc = importance_row("📈 Rent increase limitations", "rent_inc", "Limit rent increases")
        termination = importance_row("🕒 Early termination flexibility", "term", "Break lease early")
        repairs = importance_row("🔧 Repairs responsibility", "repairs", "Landlord covers repairs")
        pets = importance_row("🐾 Pets policy", "pets", "Pets in property")
        subletting = importance_row("👥 Subletting permissions", "sublet", "Renting to rooms")
        deposit = importance_row("🛡️ Deposit & guarantees", "deposit", "Security deposit fairness")

    with col_budget:
        st.markdown("<div style='border: 1px solid #E6E9EF; padding: 15px; border-radius: 10px; background-color: white;'><b>Budget</b><br><small style='color:gray;'>Maximum monthly rent</small></div>", unsafe_allow_html=True)
        budget = st.number_input("Budget", min_value=0, step=100, value=2500, label_visibility="collapsed")
        st.markdown("<p style='color: gray; font-size: 12px; margin-top: -5px;'>Max amount in $</p>", unsafe_allow_html=True)

    # Footer
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    f_left, f_mid, f_right = st.columns([1, 4, 1])
    with f_left:
        if st.button("Back", use_container_width=True): go_to_step(1)
    with f_right:
        if st.button("Next", use_container_width=True, type="primary"):
            st.session_state.user_prefs = {
                "rent_increase": rent_inc,
                "termination": termination,
                "repairs": repairs,
                "pets": pets,
                "subletting": subletting,
                "deposit": deposit,
                "budget": budget
            }
            go_to_step(3)
# ==========================================
# Step 3: Contract Upload
# ==========================================
elif st.session_state.step == 3:
    header_left, header_right = st.columns([8, 2])
    with header_left:
        col_icon, col_brand = st.columns([0.4, 10])
        with col_icon: st.image("icon_page.png", width=35)
        with col_brand: st.markdown("<h3 style='color: #2E7D32; font-weight: 600;'>RightRent</h3>",
                                    unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; font-size: 42px; font-weight: 700;'>Upload your rental contract</h1>",
                unsafe_allow_html=True)

    col_pad_left, col_main, col_pad_right = st.columns([1, 2, 1])
    with col_main:
        st.markdown(
            "<div style='border: 1px solid #E6E9EF; padding: 40px; border-radius: 15px; background-color: white; text-align: center;'>Select your PDF</div>",
            unsafe_allow_html=True)
        st.markdown("<div style='margin-top: -80px;'></div>", unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"], label_visibility="collapsed")

        if uploaded_file is not None:
            st.success(f"'{uploaded_file.name}' ready! ✔️")

            if st.button("Upload & analyze →", type="primary", use_container_width=True):
                with st.spinner("Our AI is performing RAG-based analysis..."):
                    try:
                        # FIX: Capture bytes BEFORE extracting text
                        pdf_bytes = uploaded_file.getvalue()

                        # Reset file pointer and extract text
                        uploaded_file.seek(0)
                        contract_text = extract_text_from_pdf(uploaded_file)

                        # Analyze with DeepSeek-R1
                        analysis_results = analyze_contract(contract_text, st.session_state.user_prefs)

                        # Create Highlighted PDF
                        highlighted_pdf = highlight_pdf(pdf_bytes, analysis_results)

                        # Save to session state
                        st.session_state.highlighted_pdf = highlighted_pdf
                        st.session_state.analysis_results = analysis_results
                        go_to_step(4)
                    except Exception as e:
                        st.error(f"Analysis Error: {e}")

    if st.button("Back"): go_to_step(2)

# ==========================================
# Step 4: Review & Negotiation
# ==========================================
elif st.session_state.step == 4:
    header_left, header_right = st.columns([8, 2])
    with header_left:
        col_icon, col_brand = st.columns([0.4, 10])
        with col_icon: st.image("icon_page.png", width=35)
        with col_brand: st.markdown("<h3 style='color: #2E7D32; font-weight: 600;'>RightRent</h3>",
                                    unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center;'>Your rental contract - reviewed</h1>", unsafe_allow_html=True)

    # --- PDF Viewer Section ---
    if "highlighted_pdf" in st.session_state:
        display_pdf(st.session_state.highlighted_pdf)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Negotiation Trigger ---
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("Generate message to landlord", type="primary", use_container_width=True):
            st.session_state.show_popup = True

    # --- Negotiation Pop-up Window ---
    if st.session_state.get('show_popup', False):
        st.markdown(
            "<div style='background-color: rgba(0,0,0,0.5); position: fixed; top:0; left:0; width:100%; height:100%; z-index:999;'></div>",
            unsafe_allow_html=True)

        with st.container():
            # Adjust margin-top if the popup is too high/low on your screen
            st.markdown(
                "<div style='background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #ddd; position: relative; z-index: 1000; margin-top: -700px;'>",
                unsafe_allow_html=True)

            st.subheader("Draft message to landlord")
            st.caption("Based on the highlighted clauses in your contract")

            tone = st.radio("Tone:", ["Polite", "Neutral", "Firm"], horizontal=True)

            # Using the fast DeepSeek logic for drafting
            draft_text = f"Hello, I have reviewed the rental agreement. Based on my preferences, I would like to discuss some points..."

            final_message = st.text_area("Edit your message:", value=draft_text, height=200)

            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                if st.button("Cancel"):
                    st.session_state.show_popup = False
                    st.rerun()
            with c3:
                whatsapp_url = f"[https://wa.me/?text=](https://wa.me/?text=){final_message.replace(' ', '%20')}"
                st.markdown(
                    f'<a href="{whatsapp_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold;">Send via WhatsApp</div></a>',
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Back"):
        go_to_step(3)