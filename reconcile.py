import csv
import json
import requests

def load_data():
    ledger, bank = [], []
    with open('internal_ledger.csv', 'r') as f:
        ledger = list(csv.DictReader(f))
    with open('bank_statement.csv', 'r') as f:
        bank = list(csv.DictReader(f))
    return ledger, bank



def deterministic_match(ledger, bank):
    matched, unmatched_ledger = [], []
    unmatched_bank = bank.copy()

    for invoice in ledger:
        match_found = False
        for tx in unmatched_bank:
            if float(invoice['expected_amount']) == float(tx['settled_amount']) and invoice['invoice_id'] in tx['description']:
                matched.append({
                    "invoice_id": invoice['invoice_id'],
                    "bank_ref": tx['bank_ref_number'],
                    "match_type": "Deterministic Rule",
                    "reason": "Exact match"
                })
                unmatched_bank.remove(tx)
                match_found = True
                break
        if not match_found:
            unmatched_ledger.append(invoice)

    return matched, unmatched_ledger, unmatched_bank




def ai_match(unmatched_ledger, unmatched_bank, api_key):
    print("\n Calling Mistral AI (via Direct API) to reconcile the messy records...")
    

    sorted_ledger = sorted(unmatched_ledger, key=lambda x: float(x['expected_amount']))
    sorted_bank = sorted(unmatched_bank, key=lambda x: float(x['settled_amount']))
    

    for item in sorted_ledger:
        item['expected_amount_after_fee'] = round(float(item['expected_amount']) * 0.98, 2)
    
    prompt = f"""
    You are an AI Finance Controller. Reconcile these remaining unmatched records.
    
    Rules for matching:
    1. 2% Payment Gateway Fee: The bank amount might be exactly 2% less than the expected ledger amount. (Check the pre-calculated 'expected_amount_after_fee' field).
    2. Fuzzy Names: The bank description might have typos or missing vowels (including 'y' treated as a vowel) compared to the ledger customer name (e.g., "Pooja Joshi" -> "Pj Jsh", "Riya Desai" -> "Ry Ds").
    3. Delayed Settlement: The bank date might be 1-2 days after the ledger date.
    4. STRICT PARTIAL PAYMENT RULE: If the bank amount is significantly less than the ledger amount (and it is NOT just a 2% fee), it is a Partial Payment. DO NOT match it. It MUST go to the exceptions list so a human can investigate the missing money.
    
    CRITICAL INSTRUCTION FOR OUTPUT:
    You are receiving exactly {len(sorted_ledger)} unmatched ledger records. 
    Every single record MUST be placed into EXACTLY ONE of the arrays below.
    - If it matches a bank record, put it ONLY in "ai_matched".
    - If it fails to match or breaks a rule, put it ONLY in "exceptions".
    - DO NOT put the same invoice in both lists. 
    - The total number of items in ai_matched + exceptions MUST equal exactly {len(sorted_ledger)}.
    
    Unmatched Ledger Records: {json.dumps(sorted_ledger)}
    Unmatched Bank Records: {json.dumps(sorted_bank)}
    
    Return ONLY a JSON object with this exact structure:
    {{
        "ai_matched": [
            {{"invoice_id": "...", "bank_ref": "...", "reason": "..."}}
        ],
        "exceptions": [
            {{"invoice_id": "...", "reason": "..."}}
        ]
    }}
    """
    
    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "open-mistral-nemo",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"} ,
        "temperature": 0.0 ,
        "random_seed": 123 
    }
    
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code != 200:
        raise Exception(f"API Error {response.status_code}: {response.text}")
        
    result_json = response.json()
    raw_ai_results = json.loads(result_json['choices'][0]['message']['content'])
    
   
    clean_ai_matched = []
    clean_exceptions = []
    processed_ids = set()
    
  
    ledger_amounts = {item['invoice_id']: float(item['expected_amount']) for item in unmatched_ledger}
    bank_amounts = {item['bank_ref_number']: float(item['settled_amount']) for item in unmatched_bank}
    
    
    for match in raw_ai_results.get('ai_matched', []):
        if match['invoice_id'] not in processed_ids:
           
            b_ref = str(match.get('bank_ref', '')).strip()
            inv_id = match['invoice_id']
            
            if b_ref.lower() in ['', 'none', 'null', 'n/a'] or b_ref not in bank_amounts or inv_id not in ledger_amounts:
                
                clean_exceptions.append({
                    "invoice_id": inv_id,
                    "reason": match.get('reason', 'Moved to exceptions by System: AI provided invalid or hallucinated bank_ref.')
                })
            else:
               
                expected = ledger_amounts[inv_id]
                settled = bank_amounts[b_ref]
                
                is_exact = abs(expected - settled) < 0.01
                is_fee = abs(expected * 0.98 - settled) < 0.01
                
                if not (is_exact or is_fee):
                    clean_exceptions.append({
                        "invoice_id": inv_id,
                        "reason": f"System Guardrail: Rejected AI Match to {b_ref}. Partial payment or hallucination (Expected {expected}, Settled {settled})."
                    })
                else:
                  
                    clean_ai_matched.append(match)
                
            processed_ids.add(inv_id)
            
   
    for exc in raw_ai_results.get('exceptions', []):
        if exc['invoice_id'] not in processed_ids:
            clean_exceptions.append(exc)
            processed_ids.add(exc['invoice_id'])
            
   
    for invoice in unmatched_ledger:
        if invoice['invoice_id'] not in processed_ids:
            clean_exceptions.append({
                "invoice_id": invoice['invoice_id'],
                "reason": "System Error: AI failed to evaluate this record."
            })
            
    return {
        "ai_matched": clean_ai_matched,
        "exceptions": clean_exceptions
    }



if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY not found in .env file")
    
    print(" Starting AI Finance Controller...")
    ledger_data, bank_data = load_data()
    total_records = len(ledger_data)
    
    
    matched, unmatched_ledger, unmatched_bank = deterministic_match(ledger_data, bank_data)
    
    try:
      
        ai_results = ai_match(unmatched_ledger, unmatched_bank, MISTRAL_API_KEY)
        
        final_matched_count = len(matched) + len(ai_results['ai_matched'])
        
       
        print("\n" + "="*50)
        print(" FINANCE CONTROLLER RECONCILIATION REPORT")
        print("="*50)
        print(f"Total Ledger Invoices Processed : {total_records}")
        print(f"Total Successfully Reconciled   : {final_matched_count}")
        print(f"Overall Match Rate              : {(final_matched_count/total_records)*100:.1f}%")
        print("-"*50)
        print(f"Fast Rule Matches               : {len(matched)}")
        print(f"Mistral AI Matches              : {len(ai_results['ai_matched'])}")
        
        print("\n  AI REASONING HIGHLIGHTS:")
        for match in ai_results['ai_matched'][:3]:
            print(f" -> Matched {match['invoice_id']} to {match['bank_ref']} | Reason: {match['reason']}")
            
        print("\n HONEST EXCEPTION LIST (Requires Human Review):")
        for exc in ai_results['exceptions']:
            print(f" -> {exc['invoice_id']} | Why it failed: {exc['reason']}")
            
        print("="*50)

    except Exception as e:
        print(f"\n An error occurred with the AI layer: {e}")