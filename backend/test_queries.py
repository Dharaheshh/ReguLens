import requests

queries = [
    "Explain how Master Cell Banks (MCBs) and Working Cell Banks (WCBs) are used to ensure manufacturing consistency in cultivated meat, and identify the molecular methods used to verify cell line species identity and monitor hazards like genomic instability.",
    "Compare the properties and limitations of animal-derived scaffold biomaterials such as chitosan, collagen, and gelatin in cultured meat, and describe the safety challenges associated with serum-free culture media residues and Certificates of Analysis (CoAs).",
    "What are the regulatory and biosafety considerations regarding genomic stability and tumorigenicity in immortalized cultivated meat cell lines, and what were the patient arrhythmia rates reported in the 2024 Phase III human clinical cardiovascular trials?",
    "Describe the safety risks of culture medium residues remaining in harvested cultivated meat biomass, and provide the European Union customs tariff schedules for lithium-ion battery cold-chain freight containers.",
    "Provide the FDA 510(k) electromagnetic compatibility test results and titanium alloy fatigue limits for implantable cardiac pacemakers."
]

for i, q in enumerate(queries, 1):
    print(f"\n--- Testing Query {i} ---")
    try:
        res = requests.post('http://localhost:8000/api/v1/queries', json={'query_text': q})
        if res.status_code == 200:
            data = res.json()
            print(f"Status: {data.get('sufficiency_status')}")
            if data.get('gap_summary'):
                print(f"Gap: {data['gap_summary'][:150]}...")
        else:
            print(f"Error {res.status_code}: {res.text}")
    except Exception as e:
        print(f"Exception: {e}")
