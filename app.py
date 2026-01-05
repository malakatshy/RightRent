from openai import OpenAI
import streamlit as st
import fitz
import io
from streamlit_pdf_viewer import pdf_viewer


def highlight_pdf(original_pdf_bytes, analysis_json, user_prefs):
    """
    Highlights the PDF based on user preference importance levels:
    - Low: No highlighting (user doesn't care)
    - Medium: Yellow highlighting (might be problematic but acceptable)
    - High: Red highlighting (critical, cannot compromise)
    """
    import json
    clean_json = analysis_json.replace("```json", "").replace("```", "").strip()
    risks = json.loads(clean_json)

    doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")

    # Color map based on USER PREFERENCE importance level
    color_map = {
        "High": (1, 0, 0),  # Red - critical issues user cannot compromise on
        "Medium": (1, 1, 0),  # Yellow - might be problematic but acceptable
        # "Low" is intentionally omitted - no highlighting for low importance
    }

    for risk in risks:
        quote = risk.get("exact_quote", "").strip()
        category = risk.get("preference_category", "")
        is_legal_violation = risk.get("is_legal_violation", False)

        # LEGAL VIOLATIONS are ALWAYS highlighted in RED, regardless of user preference
        if is_legal_violation:
            importance = "High"
        # Special handling for budget - verify with Python math (AI can't be trusted with math)
        elif category == "budget":
            # חילוץ בטוח של המספר (ניקוי פסיקים או סימני מטבע אם ה-AI טעה והחזיר מחרוזת)
            raw_rent = risk.get("rent_amount", 0)
            try:
                rent_amount = float(str(raw_rent).replace(',', '').replace('$', '').strip())
            except ValueError:
                rent_amount = 0

            user_budget = float(user_prefs.get("budget", 0))

            # בדיקה מתמטית קשיחה: רק אם X > Budget נצבע באדום
            if rent_amount > user_budget:
                importance = "High"
            else:
                # אם שכר הדירה תקין, אנחנו מגדירים חשיבות נמוכה כדי שהקוד ידלג על זה
                importance = "Low"

        else:
            # Look up the user's importance level for this category
            importance = user_prefs.get(category, "Medium")  # Default to Medium if unknown

        # Skip highlighting for Low importance - user doesn't care
        # BUT never skip legal violations!
        if importance == "Low" and not is_legal_violation:
            continue

        color = color_map.get(importance, (1, 1, 0))  # Default yellow if importance not found

        if len(quote) > 3:
            for page in doc:
                # First attempt: exact search
                text_instances = page.search_for(quote)

                # Second attempt: search first 20 characters if not found
                if not text_instances and len(quote) > 20:
                    text_instances = page.search_for(quote[:20])

                for inst in text_instances:
                    highlight = page.add_highlight_annot(inst)
                    highlight.set_colors(stroke=color)

                    # --- ADDED FOR XAI: Attach the explanation to the highlight ---
                    explanation = risk.get("explanation", "No explanation provided.")
                    issue_name = risk.get("issue_name", "Clause Analysis")
                    highlight.set_info(title=issue_name, content=explanation)

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
    You are an expert Israeli Legal AI Assistant specializing in residential rental agreements.
    Your task: Identify clauses that relate to the Tenant's Preferences AND any clauses that VIOLATE Israeli law.

    ### LEGAL KNOWLEDGE BASE (Ground Truth - Israeli Law):
    {legal_knowledge}

    ### TENANT PREFERENCES (User Input):
    {user_prefs}

    ---
    ### ANALYSIS PROTOCOL:

    **STEP 1 - BUDGET CHECK (MANDATORY):**
    - Find the monthly rent amount in the contract.
    - User's maximum budget is: ${user_prefs.get('budget', 'Not specified')} per month.
    - ONLY if rent is GREATER than budget → Include with preference_category "budget".
    - Do NOT include rent if it is LESS THAN or EQUAL TO the budget - this is fine!

    **STEP 2 - PREFERENCE-BY-PREFERENCE SCAN:**
    For EACH user preference, search the contract for relevant clauses.
    Use these EXACT preference_category values:
    - "rent_increase": Rent adjustment, increase, or indexation clauses
    - "termination": Early exit, cancellation, or notice period clauses
    - "repairs": Maintenance and repair responsibility clauses
    - "pets": Animal/pet policies
    - "subletting": Sublease or roommate clauses
    - "deposit": Security deposit, guarantee, or collateral terms

    **STEP 3 - LEGAL VIOLATIONS (CRITICAL):**
    Cross-reference ALL contract clauses against the Legal Knowledge Base.
    You MUST identify ANY clause that violates Israeli law, even if the user did not express a preference.

    Key laws to check:
    - Article 7 & 25H: Landlord must repair structural defects within 30 days
    - Article 25Y: SECURITY deposit cannot exceed 3 months rent; landlord must notify before using it
    - Article 25T(b): Tenant cannot be charged for building insurance or brokerage fees
    - Article 25YG: If landlord has cancellation rights, tenant must have equivalent rights
    - Article 8: "As-Is" clauses may be void if landlord knew of defects

    **IMPORTANT - These are NOT legal violations:**
    - Pet policies (allowing or prohibiting pets) - these are landlord's discretion
    - Pet deposits (separate from security deposit) - these are legal
    - Requiring landlord consent for subletting - this is standard and legal (Article 22)
    - Reasonable late fees - these are legal if not excessive

    ---
    ### EXACT_QUOTE RULES (CRITICAL FOR PDF HIGHLIGHTING):
    The "exact_quote" field MUST be a VERBATIM copy-paste from the contract text.
    - Quote COMPLETE SENTENCES - start from the beginning of a sentence to the period.
    - Copy the EXACT characters, including punctuation and spacing.
    - Do NOT paraphrase, summarize, or translate.
    - Include enough context for clear highlighting (aim for 50-150 characters).
    - Example GOOD quote: "The Tenant is responsible for all repairs and maintenance, including structural issues."
    - Example BAD quote: "structural issues" (too short, no context)

    ---
    ### OUTPUT FORMAT:
    Return ONLY a valid JSON array. No markdown, no explanation, no ```json``` wrapper.

    Each object MUST have these 7 fields:
    {{
        "issue_name": "Brief title",
        "preference_category": "rent_increase" | "termination" | "repairs" | "pets" | "subletting" | "deposit" | "budget",
        "rent_amount": 2500,  # <-- NEW: Extract the raw number found in the contract (0 if not budget related)
        "is_legal_violation": true | false,
        "exact_quote": "Verbatim text from contract",
        "explanation": "A transparent justification (XAI) that clearly states: 1) The legal issue/clause involved, 2)
        Why it is risky according to the Legal Knowledge Base, and 3) How it relates to the specific Tenant Preferences provided.",
        "negotiation_tip": "How to fix it"
    }}

    IMPORTANT: 
    - Set is_legal_violation to TRUE if the clause violates any Article in the Legal Knowledge Base.
    - Legal violations MUST always be included, even for "Low" importance user preferences.
    - If no issues found, return an empty array: []
    """

    # 3. Call DeepSeek Chat (Fast model)
    # Using 'deepseek-chat' for fast responses (deepseek-reasoner is too slow - 10+ minutes)
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"CONTRACT TEXT TO ANALYZE:\n{contract_text}"},
        ],
        # timeout=60,  # 60 second timeout to prevent hanging
        stream=False
    )

    # Return the analysis result
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
            st.markdown("<h3 style='color: #2E7D32; font-weight: 600; line-height: 1;'>RightRent</h3>",
                        unsafe_allow_html=True)
    with header_right:
        st.markdown("<p style='text-align: right; color: black; font-weight: 500; margin: 0;'>About / Help</p>",
                    unsafe_allow_html=True)

    # --- Hero Section ---
    st.markdown(
        "<h1 style='text-align: center; font-size: 42px; font-weight: 700;'>Understand your rental <br> contract with confidence</h1>",
        unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: #666; font-size: 19px;'>AI-powered highlights, personalised risk analysis, and guided <br> negotiation messaging.</p>",
        unsafe_allow_html=True)

    st.markdown("<div style='margin: 10px;'></div>", unsafe_allow_html=True)

    # --- Feature Cards ---
    c_pad1, c1, c2, c3, c_pad2 = st.columns([1, 3, 3, 3, 1])

    with c1:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>⚙️</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Preferences setup</h4>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color: #666; font-size: 15px;'>Tell us what matters so the AI can personalize the review</p>",
            unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>📄</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Contract upload</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 15px;'>We analyse risks, mismatches, and unclear terms</p>",
                    unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>👁️</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Review & negotiation</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; font-size: 15px;'>See AI-highlighted clauses and draft your message</p>",
                    unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin: 15px;'></div>", unsafe_allow_html=True)

    # --- Centered Start Button ---
    b_left, b_center, b_right = st.columns([2, 1, 2])
    with b_center:
        if st.button("Start now", use_container_width=True, type="primary"):
            go_to_step(2)

    # Disclaimer
    st.markdown("<div style='margin-top: 20px;'><hr></div>", unsafe_allow_html=True)
    st.caption(
        "RightRent is an AI tool and does not provide legal advice. Always review your final contract with a professional.")

# ==========================================
# Step 2: Personal Preferences
# ==========================================
elif st.session_state.step == 2:
    # Header
    header_left, header_right = st.columns([8, 2])
    with header_left:
        col_icon, col_brand = st.columns([0.4, 10])
        with col_icon: st.image("icon_page.png", width=35)
        with col_brand: st.markdown("<h3 style='color: #2E7D32; font-weight: 600; line-height: 1;'>RightRent</h3>",
                                    unsafe_allow_html=True)

    st.markdown("<h1 style='font-size: 32px;'>Tell us what matters to you</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color: gray; font-size: 17px;'>Your preferences help identify clauses that may not match your needs.</p>",
        unsafe_allow_html=True)

    # Main Grid
    col_ratings, col_budget = st.columns([1.6, 1])

    with col_ratings:
        st.markdown(
            "<div style='border: 1px solid #E6E9EF; padding: 15px; border-radius: 10px; background-color: white;'><b>Importance ratings</b></div>",
            unsafe_allow_html=True)


        def importance_row(label, key, help_text):
            c_label, c_input = st.columns([2, 1])
            with c_label:
                st.markdown(
                    f"<p style='margin-top: 12px; font-size: 15px;'>{label} <span title='{help_text}' style='cursor: help; color: #2E7D32;'>(?)</span></p>",
                    unsafe_allow_html=True)
            with c_input:
                return st.radio(label, ["Low", "Medium", "High"], key=key, horizontal=True,
                                label_visibility="collapsed")


        rent_inc = importance_row("📈 Rent increase limitations", "rent_inc", "Limit rent increases")
        termination = importance_row("🕒 Early termination flexibility", "term", "Break lease early")
        repairs = importance_row("🔧 Repairs responsibility", "repairs", "Landlord covers repairs")
        pets = importance_row("🐾 Pets policy", "pets", "Pets in property")
        subletting = importance_row("👥 Subletting permissions", "sublet", "Renting to rooms")
        deposit = importance_row("🛡️ Deposit & guarantees", "deposit", "Security deposit fairness")

    with col_budget:
        st.markdown(
            "<div style='border: 1px solid #E6E9EF; padding: 15px; border-radius: 10px; background-color: white;'><b>Budget</b><br><small style='color:gray;'>Maximum monthly rent</small></div>",
            unsafe_allow_html=True)
        budget = st.number_input("Budget", min_value=0, step=100, value=2500, label_visibility="collapsed")
        st.markdown("<p style='color: gray; font-size: 12px; margin-top: -5px;'>Max amount in $</p>",
                    unsafe_allow_html=True)

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
                        highlighted_pdf = highlight_pdf(pdf_bytes, analysis_results, st.session_state.user_prefs)

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

    # --- שורת כפתורי פעולה עליונה ---
    if "highlighted_pdf" in st.session_state:
        col_spacer, col_save, col_print = st.columns([6, 2, 2])

        with col_save:
            st.download_button(
                label="💾 Save PDF",
                data=st.session_state.highlighted_pdf,
                file_name="RightRent_Analysis.pdf",
                mime="application/pdf",
                use_container_width=True
            )

        with col_print:
            if st.button("🖨️ Print", use_container_width=True):
                st.info("To print, use the printer icon in the PDF menu below. 👇")

    # --- PDF Viewer Section (פתרון חסין דפדפנים) ---
    if "highlighted_pdf" in st.session_state:
        # הצגת החוזה המסומן
        pdf_viewer(st.session_state.highlighted_pdf, height=750)

    # =============================================================
    # חדש: סעיף Explainable AI (XAI) - שקיפות והסברים
    # =============================================================
    st.markdown("---")
    st.markdown("### 🔍 Clause Justifications (Explainable AI)")
    st.caption("Our AI provides reasoning for every highlight to ensure transparency and trust.")

    import json

    if "analysis_results" in st.session_state:
        try:
            # ניקוי ה-JSON ופירוק הממצאים
            clean_json = st.session_state.analysis_results.replace("```json", "").replace("```", "").strip()
            analysis_data = json.loads(clean_json)

            # יצירת כרטיס הסבר לכל ממצא
            for item in analysis_data:
                # קביעת האייקון לפי רמת הסיכון (אדום להפרות חוק או תקציב)
                is_violation = item.get("is_legal_violation", False)
                is_budget = item.get("preference_category") == "budget"
                icon = "🔴" if (is_violation or is_budget) else "🟡"

                with st.expander(f"{icon} {item.get('issue_name')}"):
                    st.write(f"**Justification:** {item.get('explanation')}")
                    st.write(f"**Negotiation Tip:** {item.get('negotiation_tip')}")
                    st.info(f"**Verbatim Clause:** \"{item.get('exact_quote')}\"")
        except:
            st.info("Additional justifications are being processed.")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- Negotiation Trigger ---
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("Generate message to landlord", type="primary", use_container_width=True):
            st.session_state.show_popup = True

    # --- Negotiation Pop-up Window (הקוד הקיים שלך) ---
    if st.session_state.get('show_popup', False):
        st.markdown(
            "<div style='background-color: rgba(0,0,0,0.5); position: fixed; top:0; left:0; width:100%; height:100%; z-index:999;'></div>",
            unsafe_allow_html=True)

        with st.container():
            st.markdown(
                "<div style='background-color: white; padding: 30px; border-radius: 15px; border: 1px solid #ddd; position: relative; z-index: 1000; margin-top: -700px;'>",
                unsafe_allow_html=True)

            st.subheader("Draft message to landlord")
            st.caption("Based on the highlighted clauses in your contract")
            tone = st.radio("Tone:", ["Polite", "Neutral", "Firm"], horizontal=True)
            draft_text = f"Hello, I have reviewed the rental agreement. Based on my preferences, I would like to discuss some points..."
            final_message = st.text_area("Edit your message:", value=draft_text, height=200)

            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                if st.button("Cancel"):
                    st.session_state.show_popup = False
                    st.rerun()
            with c3:
                whatsapp_url = f"https://wa.me/?text={final_message.replace(' ', '%20')}"
                st.markdown(
                    f'<a href="{whatsapp_url}" target="_blank" style="text-decoration:none;"><div style="background-color:#25D366; color:white; padding:10px; border-radius:10px; text-align:center; font-weight:bold;">Send via WhatsApp</div></a>',
                    unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Back"):
        go_to_step(3)