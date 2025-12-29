import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="RightRent - Rental Agreement Analysis", 
    page_icon="icon_page.png",
    layout="wide" # Using wide layout for better spacing of the 3 cards
)

# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.step = 1

if 'user_prefs' not in st.session_state:
    st.session_state.user_prefs = {}

# --- Navigation Functions ---
def go_to_step(step_number):
    st.session_state.step = step_number
    st.rerun() # 👈 This fix ensures one-click navigation

# ==========================================
# Step 1: Welcome & Homepage (Mockup Design)
# ==========================================
if st.session_state.step == 1:
    # --- Header Navigation ---
    header_left, header_right = st.columns([8, 2])
    with header_left:
        # Display logo and brand name inline
        col_icon, col_brand = st.columns([0.5, 10])
        with col_icon:
            st.image("icon_page.png", width=35)
        with col_brand:
            st.markdown("<h3 style='color: #2E7D32; margin-top: -5px; font-weight: 600;'>RightRent</h3>", unsafe_allow_html=True)
    with header_right:
        st.markdown("<p style='text-align: right; color: black; font-weight: 500;'>About / Help</p>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Hero Section ---
    st.markdown("<h1 style='text-align: center; font-size: 50px; font-weight: 700;'>Understand your rental <br> contract with confidence</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666; font-size: 20px;'>AI-powered highlights, personalised risk analysis, and guided <br> negotiation messaging.</p>", unsafe_allow_html=True)
    
    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Feature Cards Layout ---
    # Centering the cards by using empty columns on sides
    c_pad1, c1, c2, c3, c_pad2 = st.columns([1, 3, 3, 3, 1])
    
    with c1:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>⚙️</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Preferences setup</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666;'>Tell us what matters so the AI can personalize the review</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>📄</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Contract upload</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666;'>We analyse risks, mismatches, and unclear terms</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c3:
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='margin-bottom: 0;'>👁️</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='margin-top: 5px;'>Review & negotiation</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666;'>See AI-highlighted clauses and draft your message to the landlord</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    # --- Centered Start Button ---
    b_left, b_center, b_right = st.columns([2, 1, 2])
    with b_center:
        if st.button("Start now", use_container_width=True, type="primary"):
            go_to_step(2)

    # Legal Disclaimer (HAI Guideline compliance)
    st.markdown("<br><br><br><hr>", unsafe_allow_html=True)
    st.caption("RightRent is an AI-powered assistant. It does not provide legal advice. Always review your final contract with a professional.")
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
