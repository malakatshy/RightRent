# ✅ RightRent: AI-Powered Decision Support for Renters

### Description
**RightRent** is an AI-powered decision-support system that helps tenants understand and act on residential rental contracts before signing. 
Grounded in the **Israeli Fair Rental Law (2017)**, the system transforms dense legal jargon into a personalized, accessible, and actionable analysis. 
Rather than offering a generic overview, RightRent identifies legally problematic clauses, risky terms, and mismatches with user priorities directly within the original contract. 
To bridge the power imbalance between landlords and tenants, the system also surfaces missing protections as recommendations and generates professional, tone-adjusted negotiation drafts for **WhatsApp**.


**Developed by:** **Malak Atshy** & **Noor Shahin**

---
**[🚀Live Demo: RightRent on Streamlit](https://right-rent.streamlit.app/)** [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://right-rent.streamlit.app/)

**[📄 Download Sample Contract (PDF)](./test.pdf)**  *for System Evaluation*

---

### ⚠️ Important Notes

> [!IMPORTANT]
> **Hosting Policy:** Due to Streamlit's hosting policy, the app may enter **"Sleep Mode"** if inactive. Please click **"Yes, get this app back up"** to reactivate RightRent within seconds.

* **Display Settings:** This app is optimized for **Light Mode**. Please make sure your **system or browser theme** is set to **Light**. If your system is currently in Dark Mode, you can manually override it within the app via **Settings > Theme > Light**.

---

### 💡 Key Features
* **Legal Grounding (RAG):** Context-injected grounding in Israeli rental law to prevent AI hallucinations.
* **Hybrid Architecture:** Uses semantic LLM reasoning for text interpretation and deterministic logic for 100% accurate budget and preference filtering.
* **Interactive XAI:** Features a color-coded PDF viewer that explains *why* a clause is risky, bridging the gap between raw data and user understanding.
* **Negotiation Module:** Generates context-aware WhatsApp drafts based on identified risks, allowing users to choose between *Polite, Neutral,* or *Firm* tones.

---

## 🏗️ System Overview

RightRent employs a **Hybrid Intelligence architecture** that balances human preferences with automated legal reasoning:

- **Knowledge Base:**  
  The system is grounded in the *Israeli Fair Rental Law (2017)*, which serves as the “source of truth” to minimize AI hallucinations.

- **Analysis Engine:**  
  A Retrieval-Augmented Generation (RAG) workflow. The system extracts contract text using *PyMuPDF*, matches it against legal constraints, and uses the *DeepSeek LLM* to interpret semantic risks.

- **Decision Logic:**  
  Uses **Deterministic Filtering** to compare the extracted contract data against the user’s specific budget and priorities (e.g., maintenance responsibilities).

- **Human-in-the-Loop:**  
  Instead of a simple “yes/no” output, the system provides **Explainable AI (XAI)** highlights, allowing the user to make the final informed decision.

- **Actionable Negotiation Support:**  
  Bridges the gap between insight and action by generating context-aware **WhatsApp drafts**. The system adjusts the negotiation tone (*Polite, Neutral,* or *Firm*) based on the identified risks and user preferences.


---

### 🛠️ Technology Stack
* **Frontend/Deployment:** Streamlit
* **LLM Engine:** DeepSeek (via API)
* **Logic & Processing:** Python (PyMuPDF, JSON-Strict output)
* **Architecture:** Hybrid Intelligence (Semantic + Deterministic)

---

### 📋 How It Works
1. **Preference Setup:** Define your monthly budget and weight legal safeguards from Low to High importance to synchronize the analysis with your specific needs.
2. **Contract Upload:** Upload your rental contract in PDF format.
3. **Intelligent Analysis:** The system performs **Context-Injected Grounding** to identify legal and personal risks.
4. **Actionable Output:** Review highlighted risks directly on the PDF, accompanied by detailed explanations of why each clause is problematic. Once informed, generate a professional, tone-adjusted negotiation message for your landlord.

---

### 💻 Local Installation

#### 🔧 Prerequisites
Before running the project, make sure you have:

- **Python 3.8 or higher**
- **A valid DeepSeek API Key** (provided in our submission)
- **An active internet connection** (required for API calls and Streamlit)

---

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


> [!WARNING] 
> 
> **3. Configure API Key: Since our API keys are kept private for security, you need to create a local secrets file.**

>
> Replace `echo DEEPSEEK_API_KEY = "your_key" > .streamlit/secrets.toml` with the full line provided in the `Evaluation_Secrets.txt` file included in our **Moodle submission**.
> This line already contains the **actual API key** required for RightRent to function, so you can simply copy and paste it directly into your terminal without any manual changes.

```bash
mkdir .streamlit
```
```bash
echo DEEPSEEK_API_KEY = "your_key" > .streamlit/secrets.toml
```

**4. Run the app:**
```bash
streamlit run app.py
```


