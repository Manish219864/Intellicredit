# IntelliCredit
live project url:- "https://intellicredit-gmcbtyhacq6ozughqosgyo.streamlit.app/"

**AI-Powered Credit Appraisal Assistant**
IntelliCredit is an advanced, AI-driven automation tool designed to streamline and enhance the credit appraisal process. By integrating multiple Large Language Models (LLMs) and specialized agents, IntelliCredit extracts crucial financial data from documents, performs compliance checks, calculates credit scores, and automatically generates comprehensive Credit Appraisal Memos (CAMs) tailored to the Five Cs of Credit.
---
##  Features
IntelliCredit operates through five seamlessly integrated phases:
1. ** Upload & Extract (Phase 1)**
   - Upload PDF annual reports or financial statements.
   - Text extraction powered by OCR (Tesseract) and `pdfplumber`.
   - AI Agent (powered by Groq / Llama 3) automatically parses financial KPIs, revenue, net profit, promoters, and risk factors.
2. **🇮🇳 India-Specific Checks (Phase 2)**
   - **GST Mismatch Analysis:** Compares GSTR-3B vs. GSTR-2A to detect discrepancies.
   - **Bank Statement Check:** Upload bank CSVs to detect potential circular trading and verify turnover.
   - **CIBIL Score Analysis:** Pulls mock/API CIBIL data for credit health checks.
3. **Web Research & Sentiment Analysis (Phase 3)**
   - Fetches the latest web news for the company and its sector using **SerpAPI**.
   - Runs AI sentiment analysis to categorize news into Positive/Neutral/Negative impact and identifies key market risks.
4. ** Score & Insights (Phase 4)**
   - Proprietary weighted scoring model evaluating Financial Health, GST Compliance, CIBIL Legal, Web Sentiment, and Analyst Primary Insight.
   - Computes a final Credit Score (Out of 100) and provides a **Credit Decision / Verdict** (Approval/Rejection).
   - Suggests an **Approved Limit** and **Pricing** (Interest Rate bucket).
   - Generates interactive Plotly Waterfall charts explaining the exact score breakdown.
5. ** Generate CAM (Phase 5)**
   - Compiles all insights into a professional, formatted Word Document (`.docx`).
   - Allows users to override/manual inputs for loan amount, purpose, and collateral details before exporting.
---
##  Tech Stack
- **Frontend & UI:** Streamlit
- **AI & Agents:** LangChain, Groq (Llama 3 Models), OpenAI
- **Data & Visualization:** Pandas, NumPy, Plotly
- **Document Processing:** `pdfplumber`, `pytesseract` (OCR), `pdf2image`, `python-docx`
- **Search Integrations:** Google Search Results (SerpAPI)
---
##  Getting Started
### Prerequisites
Ensure you have Python 3.9+ installed on your system. 
You will also need the following system packages installed for PDF scanning and OCR to work properly:
- `tesseract-ocr`
- `poppler-utils`
#### On Ubuntu / Debian / WSL:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr poppler-utils
On macOS (Using Homebrew):
bash
brew install tesseract poppler
On Windows:
You can download the Windows installers for Tesseract OCR and Poppler. Remember to add them to your System PATH!

Installation & Local Setup
Clone the repository

bash
git clone https://github.com/your-username/intelli-credit.git
cd intelli-credit
Create and activate a virtual environment

bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
Install dependencies

bash
pip install -r requirements.txt
Environment Variables Configuration Create a 

.env
 file in the root directory (you can copy 

.env.example
) and add your API keys:

env
GROQ_API_KEY=your_groq_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_KEY=your_serpapi_key_here
Run the Streamlit app

bash
streamlit run app.py
Deployment on Streamlit Community Cloud
This app is production-ready for Streamlit Cloud!

Push your code to a public/private GitHub repository.
Ensure you have the 

packages.txt
 file at the root of your repository containing:
text
tesseract-ocr
poppler-utils
Streamlit Cloud uses this to auto-install your Debian system dependencies.
Go to share.streamlit.io and create a new app.
Set your repository, branch, and main file path to 

app.py
.
Under Advanced settings, securely add your Secrets (equivalent to your .env variables):
toml
GROQ_API_KEY = "your_key"
SERPAPI_KEY  = "your_key"
# ...
Click Deploy!

 Project Structure
intelli-credit/
├── .streamlit/             # Streamlit specific configurations / secrets
├── agents/                 # Intelligent langChain + Groq/OpenAI Agents
│   ├── cam_agent.py        # logic for `.docx` CAM generation
│   ├── extraction_agent.py # PDF to JSON data extraction
│   ├── gst_agent.py        # Statutory check logics
│   ├── scoring_agent.py    # Scoring weights and waterfall chart logic
│   └── web_research_agent.py # SerpAPI News Sentiment checks
├── data/                   # Demo/sample documents, JSON, and CSVs
├── templates/              # Base .docx templates for CAM generation
├── utils/                  # Helper utilities, PDF parsing, Bank processing
├── app.py                  # Main Entry Streamlit App
├── packages.txt            # OS-level apt packages required
├── requirements.txt        # Python pip dependencies
└── README.md

 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page

Let me know if you would like me to adjust any of the sections, such as adding a specific license or your name/project URL to it!
