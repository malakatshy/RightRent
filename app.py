import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="RightRent - Rental Agreement Analysis", 
    page_icon="icon_page.png",
    layout="wide" 
)

# --- Subtle CSS for Single-Page Fit ---
st.markdown("""
    <style>
        /* Moderate reduction of top padding */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 1rem;
        }
        /* Tighten the gap between headers and text */
        h1 { margin-top: 0px !important; padding-top: 10px; }
        h3 { margin-bottom: 5px !important; }
        /* Reduce the default vertical gap between streamlit elements */
        [data-testid="stVerticalBlock"] {
            gap: 0.8rem;
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
# Step 1: Welcome & Homepage (Balanced Spacing)
# ==========================================
if st.session_state.step == 1:
    # --- Top Navigation Bar ---
    header_left, header_right = st.columns([8, 2])
    with header_left:
        col_icon, col_brand = st.columns([0.5, 10])
        with col_icon:
            st.image("icon_page.png", width=35)
        with col_brand:
            st.markdown("<h3 style='color: #2E7D32; margin-top: -5px; font-weight: 600;'>RightRent</h3>", unsafe_allow_html=True)
    with header_right:
        st.markdown("<p style='text-align: right; color: black; font-weight: 500;'>About / Help</p>", unsafe_allow_html=True)

    # --- Hero Section (Slightly reduced font to save vertical space) ---
    st.markdown("<h1 style='text-align: center; font-size: 42px; font-weight: 700;'>Understand your rental <br> contract with confidence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; font-size: 19px;'>AI-powered highlights, personalised risk analysis, and guided <br> negotiation messaging.</p>", unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 15px;'></div>", unsafe_allow_html=True)

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

    st.markdown("<div style='margin: 20px;'></div>", unsafe_allow_html=True)

    # --- Centered Start Button ---
    b_left, b_center, b_right = st.columns([2, 1, 2])
    with b_center:
        if st.button("Start now", use_container_width=True, type="primary"):
            go_to_step(2)

    # Disclaimer - Complies with Guideline 1
    st.markdown("<div style='margin-top: 30px;'><hr></div>", unsafe_allow_html=True)
    st.caption("RightRent is an AI tool and does not provide legal advice. Always review your final contract with a professional.")

# ==========================================
# Step 2: Personal Preferences (Refined Spacing)
# ==========================================
elif st.session_state.step == 2:
    # Header
    header_left, header_right = st.columns([8, 2])
    with header_left:
        col_icon, col_brand = st.columns([0.5, 10])
        with col_icon: st.image("icon_page.png", width=35)
        with col_brand: st.markdown("<h3 style='color: #2E7D32; margin-top: -5px; font-weight: 600;'>RightRent</h3>", unsafe_allow_html=True)

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
        st.markdown("<p style='color: gray; font-size: 12px; margin-top: -10px;'>Max amount in $</p>", unsafe_allow_html=True)

    # Footer
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
    f_left, f_mid, f_right = st.columns([1, 4, 1])
    with f_left:
        if st.button("Back", use_container_width=True): go_to_step(1)
    with f_right:
        if st.button("Next", use_container_width=True, type="primary"):
            st.session_state.user_prefs = {"budget": budget} # Simplified for now
            go_to_step(3)
# ==========================================
# Step 3: Contract Upload
# ==========================================
elif st.session_state.step == 3:
    st.title("Upload Rental Agreement 📂")
    st.write("Please upload your contract in PDF format:")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        st.success("File uploaded successfully! ✔️")
        
        # Placeholder for Step 4 (Analysis Logic)
        if st.button("Analyze My Contract 🧠"):
            st.write("Processing... (AI analysis will be integrated here)")
            # go_to_step(4)
            
    if st.button("⬅ Back to Preferences"):
        go_to_step(2)
