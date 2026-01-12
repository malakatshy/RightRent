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
                rent_amount = float(str(raw_rent).replace(',', '').replace('$', '').replace('₪', '').strip())
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
    - Find the monthly rent amount in the contract (usually in NIS/Shekels).
    - User's maximum budget is: ₪{user_prefs.get('budget', 'Not specified')} per month.
    - Ensure you convert or recognize the currency correctly as Israeli New Shekels (NIS).
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
    page_title="RightRent",
    page_icon="icon_page.svg",
    layout="wide"
)

# --- Updated CSS for Branding, Spacing, and Right-Alignment ---
st.markdown("""
    <style>
        /* 1. Background Gradient */
        .stApp {
            background: linear-gradient(180deg, #FFFFFF 0%, #F1F8E9 100%);
        }

        .block-container { padding-top: 3rem; padding-bottom: 1rem; }

        /* 2. Vertically Align Columns */
        [data-testid="column"] { display: flex; align-items: center; justify-content: center; }

        /* 3. Header Styling */
        h1 { 
            margin-bottom: 10px !important; /* Added space between title and sentence */
            color: black !important;
            text-align: center !important;
            font-size: 38px !important;
            font-weight: 700 !important;
        }
        /* Professional Section Headers for Step 2 */
        .section-header {
            color: #333;
            font-size: 18px;
            font-weight: 600;
            border-bottom: 2px solid #308C14; /* RightRent Green Underline */
            padding-bottom: 5px;
            margin-bottom: 20px !important;
            width: 100%;
            text-align: left;
        }
        
        h2, h3 { margin: 0px !important; padding: 0px !important; color: #308C14 !important; }

        .brand-text { margin-left: -15px !important; white-space: nowrap; }

        /* 4. Help Button: Pushed to the far right */
        div[data-testid="column"]:last-child {
            justify-content: flex-end; /* Pushes content in the right-most column to the edge */
        }

        div[key="help_btn_step1"] button {
            background-color: transparent !important;
            border: none !important;
            color: black !important;
            text-decoration: underline !important;
            text-align: right !important;
            padding-right: 0px !important; /* Align exactly with the grid edge */
        }

        /* 5. Start Now Button */
        div.stButton > button[kind="primary"] {
            background-color: #308C14 !important;
            color: white !important;
            border-radius: 8px !important;
            padding: 0.6rem 2rem !important;
            border: none !important;
            font-weight: 600 !important;
        }

        /* 6. Feature Cards Styling (Centered Design) */
        .feature-card {
            background-color: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
            text-align: center;
            height: 210px;
            width: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            border: 1px solid #E6E9EF;
        }

        /* Tooltip styles */
        .tooltip { position: relative; display: inline-block; cursor: pointer; color: #308C14; font-weight: bold; margin-left: 5px; }
        .tooltip .tooltiptext { visibility: hidden; width: 280px; background-color: #333; color: #fff; text-align: left; border-radius: 8px; padding: 12px; position: absolute; z-index: 1000; bottom: 125%; left: 50%; margin-left: -140px; opacity: 0; transition: opacity 0.3s; transition-delay: 0.4s; font-size: 13px; line-height: 1.4; font-weight: normal; box-shadow: 0px 4px 10px rgba(0,0,0,0.2); pointer-events: none; }
        .tooltip:hover .tooltiptext, .tooltip:active .tooltiptext { visibility: visible; opacity: 1; }
    </style>
""", unsafe_allow_html=True)


# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'user_prefs' not in st.session_state:
    # הגדרת ערכי ברירת מחדל התחלתיים
    st.session_state.user_prefs = {
        "rent_increase": "Low",
        "termination": "Low",
        "repairs": "Low",
        "pets": "Low",
        "subletting": "Low",
        "deposit": "Low",
        "budget": 0
    }


# --- Navigation ---
def go_to_step(step_number):
    st.session_state.step = step_number
    st.rerun()


def generate_negotiation_message(selected_items, tone):
    """
    Generates a negotiation message from the tenant's first-person perspective.
    Ensures a consistent sign-off and WhatsApp formatting.
    """
    issues_summary = "\n".join([f"- {item['issue_name']}: {item['explanation']}" for item in selected_items])

    system_prompt = f"""
    You are the TENANT. Write a {tone} message to your potential landlord.
    Focus ONLY on these issues: 
    {issues_summary}

    ### CRITICAL IDENTITY RULES:
    - ALWAYS write in the FIRST person (use "I", "my", "me", "mine").
    - NEVER speak as an advocate, lawyer, or third party.

    ### WHATSAPP FORMATTING:
    - Use single asterisks for bold: *Text*.
    - No Markdown headers (#).
    - Clear line breaks between paragraphs.

    ### MANDATORY SIGN-OFF:
    - You MUST end the message EXACTLY with:
      Best regards,
      [Your Name]
    """

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "system", "content": system_prompt}],
        stream=False
    )
    return response.choices[0].message.content


def importance_row(label, key, category_name, help_text):
    options = ["Low", "Medium", "High"]
    current_val = st.session_state.user_prefs.get(category_name, "Medium")
    default_index = options.index(current_val)

    c_label, c_input = st.columns([1, 1.5])
    with c_label:
        st.markdown(
            f"""
            <div style='margin-top: 12px; font-size: 15px;'>
                {label}
                <div class="tooltip">(?)
                    <span class="tooltiptext">{help_text}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with c_input:
        return st.radio(label, options, index=default_index, key=key, horizontal=True,
                        label_visibility="collapsed")


@st.dialog("How RightRent Works")
def show_help_dialog():
    st.markdown("""
    Welcome to **RightRent**! Our system uses advanced AI to ensure your rental agreement is fair and legally compliant.

    ### Your Journey:
    1. **Preferences Setup:** Tell us what matters most (e.g., pets, subletting, or budget).
    2. **Contract Upload:** Upload your PDF contract. Our AI analyzes every clause against Israeli law.
    3. **AI Review:** See risks highlighted directly on your PDF with clear justifications.
    4. **Negotiation:** Choose the issues you want to fix and generate a professional message for your landlord.

    ---
    **If you need help, contact us:** 📧 [rightrent.israel@gmail.com](https://mail.google.com/mail/?view=cm&fs=1&to=rightrent.israel@gmail.com)
    """)
# ==========================================
# Step 1: Welcome & Homepage
# ==========================================
if st.session_state.step == 1:
    # --- Standardized Header ---
    # Using [9, 1] instead of [8, 2] to push the button even further to the edge
    header_left, header_right = st.columns([9, 1])
    with header_left:
        col_icon, col_brand = st.columns([0.04, 0.94], gap="small")
        with col_icon: st.image("icon_page.svg", width=45)
        with col_brand: st.markdown("<h2 class='brand-text' style='font-size: 32px; font-weight: 700;'>RightRent</h2>", unsafe_allow_html=True)

    with header_right:
        if st.button("About / Help", key="help_btn_step1"):
            show_help_dialog()

    # --- Hero Section ---
    st.markdown("<h1>Understand your rental <br> contract with confidence</h1>", unsafe_allow_html=True)
    # The space here is now controlled by the CSS margin-bottom in h1
    st.markdown("<p style='text-align: center; color: #666; font-size: 19px;'>AI-powered highlights, personalised risk analysis, and guided <br> negotiation messaging.</p>", unsafe_allow_html=True)

    st.markdown("<div style='margin: 35px;'></div>", unsafe_allow_html=True)

    # --- Feature Cards aligned to the middle ---
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
            <div class="feature-card">
                <h2 style="font-size: 45px; margin-bottom: 15px !important;">⚙️</h2>
                <h4 style="color: #333 !important; font-weight: 600;">Preferences setup</h4>
                <p style="color: #666; font-size: 15px; margin-top: 10px;">Tell us what matters so the AI can personalize the review</p>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
            <div class="feature-card">
                <h2 style="font-size: 45px; margin-bottom: 15px !important;">📄</h2>
                <h4 style="color: #333 !important; font-weight: 600;">Contract upload</h4>
                <p style="color: #666; font-size: 15px; margin-top: 10px;">We analyse risks, mismatches, and unclear terms</p>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
            <div class="feature-card">
                <h2 style="font-size: 45px; margin-bottom: 15px !important;">👁️</h2>
                <h4 style="color: #333 !important; font-weight: 600;">Review & negotiation</h4>
                <p style="color: #666; font-size: 15px; margin-top: 10px;">See AI-highlighted clauses and draft your message</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin: 40px;'></div>", unsafe_allow_html=True)

    # --- Centered Green Start Button ---
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
    # --- Standardized Header Layout (Matching Page 1) ---
    header_left, header_right = st.columns([9, 1])
    with header_left:
        col_icon, col_brand = st.columns([0.05, 0.94], gap="small")
        with col_icon: st.image("icon_page.svg", width=45)
        with col_brand: st.markdown("<h2 class='brand-text' style='font-size: 32px; font-weight: 700;'>RightRent</h2>",
                                    unsafe_allow_html=True)
    with header_right:
        st.empty()

    # Title and Centered Gray Subtitle
    st.markdown("<h1 style='text-align: center;'>Tell us what matters to you</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; color: gray; font-size: 17px; margin-top: -10px; margin-bottom: 45px;'>"
        "Your preferences help identify clauses that may not match your needs.</p>",
        unsafe_allow_html=True)

    # --- Main Selection Area (Symmetrical Layout) ---
    # We use [1.2, 1, 0.3] to push both sections slightly to the left
    # col_ratings, col_budget, col_spacer = st.columns([1.2, 1, 0.3], gap="large")
    col_p_l, col_ratings, col_gap, col_budget, col_p_r = st.columns([0.1, 1.4, 0.1, 0.7, 0.1])

    with col_ratings:
        # Professional Underlined Header
        st.markdown("<div class='section-header'>Importance ratings</div>", unsafe_allow_html=True)

        rent_inc = importance_row(
            "📈 Rent increase limitations", "rent_inc", "rent_increase",
            "<b>How important is price stability?</b><br> <b>🔴High:</b> if you need the rent to stay fixed.<br> <b>🟢Low:</b> if you are okay with price adjustments."
        )

        termination = importance_row(
            "🕒 Early termination flexibility", "term", "termination",
            "<b>Do you need an exit strategy?</b><br><b>🔴High:</b> if plans might change. <b>🟢Low:</b> if you commit to the full period."
        )

        repairs = importance_row(
            "🔧 Repairs responsibility", "repairs", "repairs",
            "<b>Avoid maintenance headaches?</b><br> <b>🔴High:</b> landlord handles everything. <b>🟢Low:</b> you fix minor things."
        )

        pets = importance_row(
            "🐾 Pets policy", "pets", "pets",
            "<b>Moving with a pet?</b><br> <b>🔴High:</b> 'no pets' is a deal-breaker. <b>🟢Low:</b> this doesn't apply."
        )

        subletting = importance_row(
            "👥 Subletting permissions", "sublet", "subletting",
            "<b>Need flexibility to share space?</b><br><b>🔴High:</b> might need a roommate or to sublet. <b>🟢Low:</b> sole resident."
        )

        deposit = importance_row(
            "🛡️ Deposit & guarantees", "deposit", "deposit",
            "<b>Limited upfront budget?</b><br> <b>🔴High:</b> cannot provide high guarantees. <b>🟢Low:</b> you have liquidity."
        )

    with col_budget:
        # Professional Underlined Header for Budget
        st.markdown("<div class='section-header'>Budget</div>", unsafe_allow_html=True)
        st.markdown(
            "<p style='color: gray; font-size: 14px; margin-top: -15px; margin-bottom: 25px;'>Maximum monthly rent</p>",
            unsafe_allow_html=True)

        # Budget Input Box
        budget = st.number_input(
            "Budget",
            min_value=0,
            step=100,
            value=st.session_state.user_prefs.get("budget", 0),
            label_visibility="collapsed"
        )
        st.markdown("<p style='color: gray; font-size: 12px; margin-top: -5px;'>Max amount in ₪ (NIS)</p>",
                    unsafe_allow_html=True)

    # --- Navigation Buttons ---
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    # Aligning buttons with the main content area
    b_left, b_mid, b_right, b_spacer = st.columns([0.4, 1.8, 0.4, 0.1])

    with b_left:
        if st.button("Back", use_container_width=True):
            go_to_step(1)

    with b_right:
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
    # --- Standardized Header Logic ---
    # --- Standardized Header Layout (Matching Page 1 positioning without the button) ---
    # We keep [9, 1] to ensure the logo doesn't shift when the button is removed
    header_left, header_right = st.columns([9, 1])

    with header_left:
        # Exact same 0.05 / 0.94 ratio from Page 1
        col_icon, col_brand = st.columns([0.05, 0.94], gap="small")
        with col_icon:
            st.image("icon_page.svg", width=45)
        with col_brand:
            # Using the brand-text class and the same alignment from Page 1
            st.markdown(
                "<h2 class='brand-text' style='font-size: 32px; font-weight: 700; height: 45px; display: flex; align-items: center;'>RightRent</h2>",
                unsafe_allow_html=True)

    with header_right:
        # We leave this empty to keep the logo in its exact position
        st.empty()

    st.markdown("<h1 style='text-align: center; font-size: 38px; font-weight: 700;'>Upload your rental contract</h1>",
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
    # --- CSS for a clean "Popup" look without breaking widgets ---
    st.markdown("""
        <style>
        .negotiation-box {
            background-color: #f9f9f9;
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #308C14;
            margin-top: 20px;
        }
        .whatsapp-btn {
            background-color: #25D366;
            color: white !important;
            padding: 12px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
            display: block;
            text-decoration: none;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- Standardized Header Logic ---
    # --- Standardized Header Layout (Matching Page 1 positioning without the button) ---
    # We keep [9, 1] to ensure the logo doesn't shift when the button is removed
    header_left, header_right = st.columns([9, 1])

    with header_left:
        # Exact same 0.05 / 0.94 ratio from Page 1
        col_icon, col_brand = st.columns([0.05, 0.94], gap="small")
        with col_icon:
            st.image("icon_page.svg", width=45)
        with col_brand:
            # Using the brand-text class and the same alignment from Page 1
            st.markdown(
                "<h2 class='brand-text' style='font-size: 32px; font-weight: 700; height: 45px; display: flex; align-items: center;'>RightRent</h2>",
                unsafe_allow_html=True)

    with header_right:
        # We leave this empty to keep the logo in its exact position
        st.empty()

    st.markdown("<h1 style='text-align: center;'>Your rental contract - reviewed</h1>", unsafe_allow_html=True)

    # 1. Show PDF and Justifications first
    if "highlighted_pdf" in st.session_state:
        pdf_viewer(st.session_state.highlighted_pdf, height=500)

    st.markdown("---")
    st.markdown("### 🔍 Clause Justifications (Explainable AI)")

    import json

    clean_json = st.session_state.analysis_results.replace("```json", "").replace("```", "").strip()
    analysis_data = json.loads(clean_json)

    for item in analysis_data:
        is_violation = item.get("is_legal_violation", False)
        icon = "🔴" if (is_violation or item.get("preference_category") == "budget") else "🟡"
        with st.expander(f"{icon} {item.get('issue_name')}"):
            st.write(f"**Justification:** {item.get('explanation')}")
            st.write(f"**Negotiation Tip:** {item.get('negotiation_tip')}")

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Handle the "Generate Message" Workflow
    if not st.session_state.get('show_popup', False):
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            if st.button("Generate message to landlord", type="primary", use_container_width=True):
                st.session_state.show_popup = True
                st.rerun()
    else:
        # --- THIS IS THE "POPUP" SECTION ---
        st.markdown("<div class='negotiation-box'>", unsafe_allow_html=True)
        st.subheader("✉️ Draft Negotiation Message")

        # CLOSE BUTTON
        if st.button("✖️ Close"):
            st.session_state.show_popup = False
            st.session_state.pop_generated_msg = ""
            st.rerun()

        st.write("---")

        # PHASE 1: PREFERENCES
        st.write("**1. Choose which issues to include:**")
        selected_items = []
        c1, c2 = st.columns(2)
        for idx, item in enumerate(analysis_data):
            target_col = c1 if idx % 2 == 0 else c2
            with target_col:
                if st.checkbox(item['issue_name'], value=True, key=f"sel_{idx}"):
                    selected_items.append(item)

        st.write("**2. Choose tone:**")
        chosen_tone = st.radio("Tone:", ["Polite", "Neutral", "Firm"], horizontal=True, key="tone_sel")

        # PHASE 2: GENERATION
        if st.button("Generate/Update Draft ✨", use_container_width=True):
            if not selected_items:
                st.error("Please select at least one issue to negotiate.")
            else:
                with st.spinner("AI is writing..."):
                    new_draft = generate_negotiation_message(selected_items, chosen_tone)
                    st.session_state.pop_generated_msg = new_draft
                    st.session_state.negotiation_text = new_draft
                    # Reset confirmation status when a new draft is made
                    st.session_state.is_confirmed = False
                    st.rerun()

        # PHASE 3: EDITING & CONFIRMING
        if st.session_state.get("pop_generated_msg"):
            st.markdown("---")
            st.write("**3. Review and edit your message:**")

            # Use a key to track manual edits in session state
            st.text_area("Final Message:", height=200, key="negotiation_text")

            # The NEW Confirm Button
            if st.button("✅ Confirm My Edits", use_container_width=True):
                # Save the current state of the text area into a 'confirmed' variable
                st.session_state.confirmed_final_msg = st.session_state.negotiation_text
                st.session_state.is_confirmed = True
                st.success("Edits confirmed! Click below to send via WhatsApp.")

            # PHASE 4: SENDING (Only visible after confirmation)
            if st.session_state.get("is_confirmed", False):
                import urllib.parse

                # Pull the strictly confirmed message
                final_to_send = st.session_state.confirmed_final_msg
                encoded_msg = urllib.parse.quote(final_to_send)
                whatsapp_url = f"https://wa.me/?text={encoded_msg}"

                st.markdown(
                    f'<a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">'
                    f'Send via WhatsApp</a>',
                    unsafe_allow_html=True
                )

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Back"):
        go_to_step(3)