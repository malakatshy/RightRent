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
    # הגדרת ערכי ברירת מחדל התחלתיים
    st.session_state.user_prefs = {
        "rent_increase": "Low",
        "termination": "Low",
        "repairs": "High",
        "pets": "Low",
        "subletting": "Low",
        "deposit": "High",
        "budget": 2500
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

    col_ratings, col_budget = st.columns([1.6, 1])

    with col_ratings:
        st.markdown(
            "<div style='border: 1px solid #E6E9EF; padding: 15px; border-radius: 10px; background-color: white;'><b>Importance ratings</b></div>",
            unsafe_allow_html=True)


        # פונקציה מעודכנת שזוכרת את הבחירה הקודמת
        def importance_row(label, key, category_name, help_text):
            options = ["Low", "Medium", "High"]
            # מציאת האינדקס של הערך השמור כיום בזיכרון
            current_val = st.session_state.user_prefs.get(category_name, "Medium")
            default_index = options.index(current_val)

            c_label, c_input = st.columns([2, 1])
            with c_label:
                st.markdown(
                    f"<p style='margin-top: 12px; font-size: 15px;'>{label} <span title='{help_text}' style='cursor: help; color: #2E7D32;'>(?)</span></p>",
                    unsafe_allow_html=True)
            with c_input:
                return st.radio(label, options, index=default_index, key=key, horizontal=True,
                                label_visibility="collapsed")


        # קריאה לפונקציות עם מיפוי לקטגוריות הנכונות
        rent_inc = importance_row("📈 Rent increase limitations", "rent_inc", "rent_increase", "Limit rent increases")
        termination = importance_row("🕒 Early termination flexibility", "term", "termination", "Break lease early")
        repairs = importance_row("🔧 Repairs responsibility", "repairs", "repairs", "Landlord covers repairs")
        pets = importance_row("🐾 Pets policy", "pets", "pets", "Pets in property")
        subletting = importance_row("👥 Subletting permissions", "sublet", "subletting", "Renting to rooms")
        deposit = importance_row("🛡️ Deposit & guarantees", "deposit", "deposit", "Security deposit fairness")

    with col_budget:
        st.markdown(
            "<div style='border: 1px solid #E6E9EF; padding: 15px; border-radius: 10px; background-color: white;'><b>Budget</b><br><small style='color:gray;'>Maximum monthly rent</small></div>",
            unsafe_allow_html=True)
        # שימוש בערך השמור בזיכרון כברירת מחדל
        budget = st.number_input("Budget", min_value=0, step=100, value=st.session_state.user_prefs.get("budget", 2500),
                                 label_visibility="collapsed")
        st.markdown("<p style='color: gray; font-size: 12px; margin-top: -5px;'>Max amount in ₪ (NIS)</p>",
                    unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    f_left, f_mid, f_right = st.columns([1, 4, 1])
    with f_left:
        if st.button("Back", use_container_width=True): go_to_step(1)
    with f_right:
        if st.button("Next", use_container_width=True, type="primary"):
            # שמירה סופית לזיכרון לפני מעבר דף
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
    # --- CSS for a clean "Popup" look without breaking widgets ---
    st.markdown("""
        <style>
        .negotiation-box {
            background-color: #f9f9f9;
            padding: 25px;
            border-radius: 15px;
            border: 2px solid #2E7D32;
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

    header_left, header_right = st.columns([8, 2])
    with header_left:
        col_icon, col_brand = st.columns([0.4, 10])
        with col_icon: st.image("icon_page.png", width=35)
        with col_brand: st.markdown("<h3 style='color: #2E7D32; font-weight: 600;'>RightRent</h3>",
                                    unsafe_allow_html=True)

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
                with st.spinner("AI is writing your message..."):
                    # Generate the new message
                    new_draft = generate_negotiation_message(selected_items, chosen_tone)

                    # Store in temporary state
                    st.session_state.pop_generated_msg = new_draft

                    # FORCE the text area to refresh by updating its session state key
                    st.session_state.negotiation_text = new_draft
                    st.rerun()

        # PHASE 3: EDITING & SENDING
        if st.session_state.get("pop_generated_msg"):
            st.markdown("---")
            st.write("**3. Review and edit your message:**")

            # The 'value' is ignored by Streamlit if the 'key' already exists in state,
            # which is why we manually updated the state in Phase 2 above.
            st.text_area(
                "Final Message:",
                height=250,
                key="negotiation_text"
            )

            # Capture the current state of the text area (including user edits)
            final_to_send = st.session_state.negotiation_text

            import urllib.parse

            whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(final_to_send)}"

            st.markdown(
                f'<a href="{whatsapp_url}" target="_blank" class="whatsapp-btn">'
                f'Send via WhatsApp</a>',
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

    if st.button("Back"):
        go_to_step(3)