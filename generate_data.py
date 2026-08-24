import csv
import random
from datetime import datetime, timedelta

def generate_synthetic_data(num_records=60):
    ledger_data = []
    bank_data = []
    
    start_date = datetime(2024, 8, 1)
    
    names = ["Rahul Kumar", "Priya Sharma", "Amit Singh", "Neha Gupta", "Vikram Patel", 
             "Sneha Reddy", "Arjun Das", "Pooja Joshi", "Karan Malhotra", "Riya Desai"]

    for i in range(1, num_records + 1):
       
        ledger_id = f"INV-{1000 + i}"
        customer = random.choice(names)
        base_amount = round(random.uniform(500.0, 10000.0), 2)
        tx_date = start_date + timedelta(days=random.randint(0, 10))
        date_str = tx_date.strftime("%Y-%m-%d")
        
       
        ledger_data.append({
            "invoice_id": ledger_id,
            "date": date_str,
            "customer_name": customer,
            "expected_amount": base_amount,
            "status": "pending"
        })

        
        scenario = random.choices(
            ["perfect", "fee_deducted", "fuzzy_name", "delayed", "true_exception", "missing"], 
            weights=[50, 15, 15, 10, 5, 5], 
            k=1
        )[0]

        bank_ref = f"UTR{random.randint(10000000, 99999999)}"
        bank_date = tx_date
        bank_desc = f"UPI/{ledger_id}/{customer}"
        bank_amount = base_amount

        if scenario == "missing":
            continue 
            
        elif scenario == "fee_deducted":
            
            bank_amount = round(base_amount * 0.98, 2)
            bank_desc = f"RAZORPAY SETTLEMENT {ledger_id}"
            
        elif scenario == "fuzzy_name":
            
            vowels = "aeiouAEIOU"
            messed_up_name = "".join([c for c in customer if c not in vowels])
            bank_desc = f"NEFT/{messed_up_name}/TXN"
            
        elif scenario == "delayed":
           
            bank_date = tx_date + timedelta(days=2)
            
        elif scenario == "true_exception":
           
            bank_amount = round(base_amount * random.uniform(0.1, 0.5), 2)
            bank_desc = f"PARTIAL {customer}"

        
        bank_data.append({
            "bank_ref_number": bank_ref,
            "settlement_date": bank_date.strftime("%Y-%m-%d"),
            "description": bank_desc,
            "settled_amount": bank_amount
        })

   
    random.shuffle(bank_data)

    
    with open('internal_ledger.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["invoice_id", "date", "customer_name", "expected_amount", "status"])
        writer.writeheader()
        writer.writerows(ledger_data)

    
    with open('bank_statement.csv', 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["bank_ref_number", "settlement_date", "description", "settled_amount"])
        writer.writeheader()
        writer.writerows(bank_data)

    print(f" Generated internal_ledger.csv ({len(ledger_data)} records)")
    print(f" Generated bank_statement.csv ({len(bank_data)} records)")
    print("Ready for Phase 2!")

if __name__ == "__main__":
    generate_synthetic_data()

