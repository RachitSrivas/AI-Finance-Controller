import streamlit as st
import pandas as pd
import io
import csv
import os
from dotenv import load_dotenv
from reconcile import load_data, deterministic_match, ai_match



load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
if not MISTRAL_API_KEY:
    st.error("MISTRAL_API_KEY not found in .env file")
    st.stop()


st.set_page_config(layout="wide", page_title="AI Finance Controller")
st.title(" AI Finance Controller")
st.markdown("Automated Multi-source Reconciliation Dashboard")


st.sidebar.markdown("## Action Panel")
st.sidebar.markdown("Click below to start the automated reconciliation process.")
run_btn = st.sidebar.button(" Run Reconciliation", type="primary", use_container_width=True)



st.sidebar.markdown("---")
st.sidebar.subheader(" Upload Custom Data (Optional)")
uploaded_ledger = st.sidebar.file_uploader("Upload Internal Ledger (CSV)", type="csv")
uploaded_bank = st.sidebar.file_uploader("Upload Bank Statement (CSV)", type="csv")



if uploaded_ledger is not None and uploaded_bank is not None:
   
    ledger_text = uploaded_ledger.read().decode('utf-8')
    bank_text = uploaded_bank.read().decode('utf-8')
    
    ledger_data = list(csv.DictReader(io.StringIO(ledger_text)))
    bank_data = list(csv.DictReader(io.StringIO(bank_text)))
    st.sidebar.success("Using your uploaded CSVs!")
else:
    
    ledger_data, bank_data = load_data()
    st.sidebar.info(" Using default synthetic data. Upload files on the left to override.")


if not run_btn:
    st.info(" Click 'Run Reconciliation' in the sidebar to begin.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Internal Ledger (Raw Data)")
        st.dataframe(pd.DataFrame(ledger_data))
    with col2:
        st.subheader("Bank Statement (Raw Data)")
        st.dataframe(pd.DataFrame(bank_data))


if run_btn:
    
    with st.spinner(" Running deterministic rules..."):
        matched, unmatched_ledger, unmatched_bank = deterministic_match(ledger_data, bank_data)
    
   
    with st.spinner(f" Sending {len(unmatched_ledger)} complex records to Mistral AI..."):
        try:
            
            ai_results = ai_match(unmatched_ledger, unmatched_bank, MISTRAL_API_KEY)
            
           
            total_records = len(ledger_data)
            final_matched = len(matched) + len(ai_results['ai_matched'])
            match_rate = (final_matched / total_records) * 100
            
            st.success(" Reconciliation Complete!")
            
            
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Invoices", total_records)
            m2.metric("Fast Rule Matches", len(matched))
            m3.metric("AI Matches", len(ai_results['ai_matched']))
            m4.metric("Overall Match Rate", f"{match_rate:.1f}%")
            
            st.divider()
            
            
            st.subheader(" AI Reasoning Highlights")
            st.markdown("Records matched using fuzzy logic, 2% fee deductions, or date flexibility.")
            if len(ai_results['ai_matched']) > 0:
                ai_df = pd.DataFrame(ai_results['ai_matched'])
                st.dataframe(ai_df, use_container_width=True)
            else:
                st.info("No AI matches found.")
            
            st.divider()
            
           
            st.subheader(" Honest Exception List (Manual Review Required)")
            st.markdown("Records the AI refused to match due to unresolvable discrepancies.")
            if len(ai_results['exceptions']) > 0:
                
                exc_df = pd.DataFrame(ai_results['exceptions'])
                st.dataframe(exc_df.style.map(lambda _: 'background-color: #ffcccc; color: black'), use_container_width=True)
            else:
                st.success("No exceptions! 100% matched.")

        except Exception as e:
            st.error(f"Something went wrong with the AI call: {e}")