# ✅ RightRent: AI-Powered Decision Support for Renters

### Description
**RightRent** is an AI-powered decision-support system that helps tenants understand and act on residential rental contracts before signing. 
Grounded in the **Israeli Fair Rental Law (2017)**, the system transforms dense legal jargon into a personalized, accessible, and actionable analysis. 
Rather than offering a generic overview, RightRent identifies legally problematic clauses, risky terms, and mismatches with user priorities directly within the original contract. 
To bridge the power imbalance between landlords and tenants, the system also surfaces missing protections as recommendations and generates professional, tone-adjusted negotiation drafts for **WhatsApp**.


**Developed by:** **Malak Atshy** & **Noor Shahin**

🚀 **[Live Demo: RightRent on Streamlit](https://right-rent.streamlit.app/)**

---

### ⚠️ Important Notes

> [!IMPORTANT]
> **Hosting Policy:** Due to Streamlit's hosting policy, the app may enter **"Sleep Mode"** if inactive. Please click **"Yes, get this app back up"** to reactivate RightRent within seconds.

* **Display Settings:** For the best user experience, please set the Streamlit theme to **"Light Mode"** (Settings > Theme > Light).

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

**Make sure you have Python installed**
```bash
pip install -r requirements.txt
```

**3. Configure API Key: Since our API keys are kept private for security, you need to create a local secrets file.**

> [!IMPORTANT]
>
> Replace "your_key" with the actual API key provided in the `Evaluation_Secrets.txt` file included in our Moodle submission.

```bash
mkdir .streamlit
echo DEEPSEEK_API_KEY = "your_key" > .streamlit/secrets.toml
```

**4. Run the app:**
```bash
streamlit run app.py
```


