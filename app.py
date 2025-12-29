import streamlit as st

# --- Page Configuration ---
st.set_page_config(page_title="RightRent - Rental Agreement Analysis", page_icon="🏠")

# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.step = 1  # Start at Step 1

if 'user_prefs' not in st.session_state:
    st.session_state.user_prefs = {}

# --- Navigation Functions ---
def go_to_step(step_number):
    st.session_state.step = step_number

# ==========================================
# Step 1: Welcome & Disclaimer
# ==========================================
if st.session_state.step == 1:
    st.title("RightRent 🏠")
    st.subheader("Analyze your rental agreement in minutes")
    
    st.write("""
    Welcome! Our system helps you understand your rental contract, 
    identify potential risks, and align the terms with your personal needs.
    """)
    
    # Disclaimer - Based on HAI Guideline 1 (Expectations)
    st.info("""
    **Important Note:** This system is powered by AI and is intended as a support tool only. 
    The information provided does **not** constitute binding legal advice. 
    In case of doubt, we strongly recommend consulting a lawyer.
    """)
    
    if st.button("Let's Get Started! 🚀"):
        go_to_step(2)

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
