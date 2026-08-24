# 📊 AI Finance Controller 
**Razorpay Buildathon - Track 4 Submission**

An automated multi-source reconciliation agent that closes the finance-ops loop. Built to solve the "verification capacity" bottleneck, this project combines the speed of deterministic code with the reasoning power of Generative AI, protected by strict mathematical guardrails to eliminate hallucinations.

---

## 🎯 The Problem
Reconciliation is a massive bottleneck for finance teams. Traditional software fails when names are misspelled or when payment gateways deduct hidden fees. However, trusting an AI to handle money blindly is dangerous because AI models often "hallucinate" math or force fake matches across large datasets.

## 🚀 Our Solution
We built an **Automated Multi-source Reconciliation Dashboard**. It features a highly robust, dual-layer architecture designed to gracefully fail on unresolvable discrepancies, ensuring no money is ever misallocated.

Crucially, it is built with an **"Honest Exception List"** protocol. We mathematically bound the AI to prevent hallucinations, proving that the system knows exactly when to ask a human for help.

---

## 🧠 Technical Architecture (The 3-Layer Pipeline)

### Layer 1: The Deterministic Engine (Speed & Cost)
Instead of sending every transaction to an expensive LLM, Python parses the data and instantly matches records that have exact amounts and exact Invoice IDs.
* **Result:** High throughput, zero API costs, and 100% accuracy for standard transactions.

### Layer 2: Mistral AI Reasoning Engine (Fuzzy Logic)
The messy, unmatched records are pre-sorted and sent to `mistral-large-latest`. The AI is given strict business rules to act as a human accountant:
* It identifies 2% Payment Gateway Fees.
* It resolves Fuzzy Names (e.g., matching "Pooja Joshi" to bank abbreviations like "Pj Jsh").
* It handles Delayed Settlements (payments clearing 1-2 days late).

### Layer 3: Python Sanity Check (The Safety Net)
LLMs are notoriously bad at arithmetic and can occasionally hallucinate fake matches. We built a final Python guardrail that intercepts the AI's output and **mathematically verifies** its work.
* If the AI claims a match, Python checks if the amounts perfectly align (or exactly match the 2% fee rule). 
* If the AI hallucinates, Python aggressively rejects it. All rejected records, partial payments, and missing transactions are securely pushed to the **Honest Exception List** for manual human review.

---

## 💻 Key Features
* **Custom CSV Uploads:** Users can drag-and-drop their own Ledger and Bank Statement CSVs directly into the web app.
* **Audit Trail (Reasoning Highlights):** The AI provides a plain-English explanation for why it matched a fuzzy record, proving it did the math.
* **Streamlit UI:** A clean, professional dashboard providing instant metrics on Total Invoices, Fast Matches, AI Matches, and Overall Match Rate.
* **100% Deterministic AI Output:** Through data pre-sorting and compute-offloading, the AI's attention mechanism is stabilized, guaranteeing perfectly consistent results on every run.

---

## 🛠️ Setup & Installation

**1. Clone the repository**
```bash
git clone https://github.com/RachitSrivas/AI-Finance-Controller
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Add your API Key**
Create a `.env` file in the root directory and add your Mistral API key:
```text
MISTRAL_API_KEY="your_api_key_here"
```

---

## 🚀 How to Run

**Run the Streamlit Dashboard (Recommended)**
Provides a beautiful, interactive web UI.
```bash
streamlit run app.py
```

**Run in the Terminal (Headless Mode)**
For backend testing and quick reporting.
```bash
python reconcile.py
```

**Generate fresh synthetic data**
If you want to test the agent against a brand new batch of 60 records with randomized typos and missing payments.
```bash
python generate_data.py
```
