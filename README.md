# ✅ RightRent: AI-Powered Decision Support for Renters

**RightRent** is an intelligent decision-support system designed to help tenants in Israel navigate complex residential rental contracts. By combining **Large Language Models (DeepSeek)** with **deterministic Python logic**, the system transforms dense legal jargon into personalized, actionable insights.

**Developed by:** Malak Atshy & Noor Shahin

🚀 **[Live Demo: RightRent on Streamlit](https://right-rent.streamlit.app/)**

---

### 💡 Key Features
* **Legal Grounding (RAG):** Analysis is grounded in the *Israeli Fair Rental Law (2017)* through context injection to prevent AI hallucinations.
* **Hybrid Architecture:** Uses semantic LLM reasoning for text interpretation and deterministic logic for 100% accurate budget and preference filtering.
* **Interactive XAI:** Features a color-coded PDF viewer that explains *why* a clause is risky, bridging the gap between raw data and user understanding.
* **Negotiation Module:** Generates context-aware WhatsApp drafts based on identified risks, allowing users to choose between *Polite, Neutral,* or *Firm* tones.

---

### 🛠️ Technology Stack
* **Frontend/Deployment:** Streamlit
* **LLM Engine:** DeepSeek (via API)
* **Logic & Processing:** Python (PyMuPDF, JSON-Strict output)
* **Architecture:** Hybrid Intelligence (Semantic + Deterministic)

---

### ⚠️ Important Notes

> [!IMPORTANT]
> **Hosting Policy:** Due to Streamlit's hosting policy, the app may enter **"Sleep Mode"** if inactive. Please click **"Yes, get this app back up"** to reactivate RightRent within seconds.

* **Display Settings:** For the best user experience, please set the Streamlit theme to **"Light Mode"** (Settings > Theme > Light).

---

### 📋 How It Works
1. **Preference Setup:** Define your monthly budget and set importance levels (Low to High) for various legal categories.
2. **Contract Upload:** Upload your rental contract in PDF format.
3. **Intelligent Analysis:** The system performs **Context-Injected Grounding** to identify legal and personal risks.
4. **Actionable Output:** Review highlighted risks directly on the PDF and generate a professional negotiation message for your landlord.

---

### 💻 Local Installation
To run this project locally, follow these steps:

**1. Clone the repository:**
```bash
git clone https://github.com/malakatshy/RightRent.git
cd RightRent
```

**2. Install dependencies:**
```bash
pip install -r requirements.txt
```

**3. Run the app:**
```bash
streamlit run app.py
```


