import streamlit as st

# --- Page Configuration ---
# Using the requested icon file
st.set_page_config(page_title="RightRent - Rental Agreement Analysis", page_icon="icon_page.png")

# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.step = 1  # Start at Step 1

if 'user_prefs' not in st.session_state:
    st.session_state.user_prefs = {}

# --- Navigation Functions ---
def go_to_step(step_number):
    st.session_state.step = step_number

# ==========================================
# Step 1: Welcome & Homepage (Mockup Design)
# ==========================================
if st.session_state.step == 1:
    # --- Top Navigation Bar ---
    nav_col1, nav_col2 = st.columns([8, 2])
    with nav_col1:
        # Display logo and text inline
        col_logo, col_text = st.columns([1, 10])
        with col_logo:
            st.image("icon_page.png", width=40)
        with col_text:
            st.markdown("<h3 style='color: #2E7D32; margin-top: -5px;'>RightRent</h3>", unsafe_allow_html=True)
    with nav_col2:
        st.write("About / Help")

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Main Hero Section ---
    st.markdown("<h1 style='text-align: center;'>Understand your rental <br> contract with confidence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; font-size: 18px;'>AI-powered highlights, personalised risk analysis, and guided <br> negotiation messaging.</p>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # --- Feature Cards ---
    card1, card2, card3 = st.columns(3)
    
    with card1:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("⚙️", unsafe_allow_html=True) # Gear Icon
        st.markdown("**Preferences setup**")
        st.markdown("<p style='font-size: 14px; color: #555;'>Tell us what matters so the AI can personalize the review</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with card2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("📄", unsafe_allow_html=True) # Document Icon
        st.markdown("**Contract upload**")
        st.markdown("<p style='font-size: 14px; color: #555;'>We analyse risks, mismatches, and unclear terms</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with card3:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("👁️", unsafe_allow_html=True) # Eye Icon
        st.markdown("**Review & negotiation**")
        st.markdown("<p style='font-size: 14px; color: #555;'>See AI-highlighted clauses and draft your message to the landlord</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Centered Start Button ---
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("Start now", use_container_width=True, type="primary"):
            go_to_step(2)

    # Disclaimer (Keeping it at the bottom for Guideline 1 Compliance)
    st.markdown("<br><hr>", unsafe_allow_html=True)
    st.caption("Note: RightRent is an AI support tool and does not provide binding legal advice.")
# ==========================================
# Step 2: Personal Preferences (Onboarding)
# ==========================================
elif st.session_state.step == 2:
    st.title("What matters to you? 📝")
    st.write("Select the themes that are important to you to personalize the analysis:")
    
    # User Preferences (Personalization Layer)
    pets = st.checkbox("I have pets (or plan to have them)")
    sublet = st.checkbox("I want the option to sublet the apartment")
    exit_option = st.checkbox("An early exit/termination clause is important to me")
    repairs = st.checkbox("I want to ensure wear-and-tear repairs are the landlord's duty")
    
    # Saving data
    if st.button("Continue to Upload ➔"):
        st.session_state.user_prefs = {
            "pets": pets,
            "sublet": sublet,
            "exit_option": exit_option,
            "repairs": repairs
        }
        go_to_step(3)
    
    if st.button("⬅ Back"):
        go_to_step(1)

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
