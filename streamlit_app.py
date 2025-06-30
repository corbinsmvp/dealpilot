
import streamlit as st

st.set_page_config(page_title="DealPilot – F&I Deal Assistant (MVP)", layout="wide")

# --------------------------
# Fake lender program rules
# --------------------------
lender_rules = {
    "SSFCU": {"max_ltv": 130, "max_pti": 15, "auto_ltv": 100, "auto_score": 700, "checklist": ["Member addendum", "CUDL credit app"]},
    "BOA":   {"max_ltv": 140, "max_pti": 18, "auto_ltv": 105, "auto_score": 680, "checklist": ["Driver's license copy", "Credit app"]},
    "TD":    {"max_ltv": 125, "max_pti": 14, "auto_ltv": 95,  "auto_score": 720, "checklist": ["Stips as requested"]},
    "GTCU":  {"max_ltv": 135, "max_pti": 17, "auto_ltv": 100, "auto_score": 690, "checklist": ["Proof of insurance"]},
}

# --------------------------
st.title("🚗 DealPilot – F&I Deal Assistant (MVP)")

st.markdown(
    "Use this prototype to test deal structures, calculate DTI / PTI / LTV, match lenders, "
    "see smart‐approval alerts, and view funding check‑lists."
)

# ---- Deal inputs ----
st.header("📋 Deal Inputs")

col1, col2, col3 = st.columns(3)
with col1:
    income = st.number_input("Gross Monthly Income ($)", min_value=0, value=6000)
    credit_score = st.number_input("Credit Score (TU / best bureau)", min_value=300, max_value=900, value=700)
with col2:
    price = st.number_input("Vehicle Price ($)", min_value=0, value=35000)
    msrp  = st.number_input("MSRP ($)", min_value=0, value=40000)
with col3:
    term  = st.selectbox("Loan Term (months)", [36, 48, 60, 72, 84], index=2)
    rate  = st.number_input("Rate % (estimate)", min_value=0.0, value=8.5)

trade_payment   = st.number_input("Trade‐in Payment ($)", min_value=0, value=0)
curr_install    = st.number_input("Current Installment Obligations ($)", min_value=0, value=500)

# Payment estimate (very simple)
monthly_pmt = (price * (1 + (rate/100) * (term/12))) / term if term else 0

# ---- Calculations ----
st.subheader("📊 Results")

dti = ((curr_install - trade_payment + monthly_pmt) / income) * 100 if income else 0
pti = (monthly_pmt / income) * 100 if income else 0
ltv = (price / msrp) * 100 if msrp else 0

st.write(f"**Estimated Monthly Payment:** ${monthly_pmt:,.2f}")
st.write(f"**DTI:** {dti:.2f}% &nbsp; | &nbsp; **PTI:** {pti:.2f}% &nbsp; | &nbsp; **LTV:** {ltv:.2f}%")

# ---- Lender match ----
st.subheader("🏦 Lender Matches")

matches = []
for lender, rule in lender_rules.items():
    if ltv <= rule["max_ltv"] and pti <= rule["max_pti"]:
        matches.append(lender)

if matches:
    st.success("Matched Lenders: " + ", ".join(matches))
else:
    st.error("No lenders matched given current rules.")

# ---- Smart alerts ----
st.subheader("💡 Smart Alerts")

for lender, rule in lender_rules.items():
    if credit_score >= rule["auto_score"]:
        delta_ltv = ltv - rule["auto_ltv"]
        if delta_ltv > 0 and delta_ltv <= 5:
            st.warning(f"{lender}: Reduce LTV by {delta_ltv:.2f}% (~${(delta_ltv/100)*price:,.0f}) to hit auto‐approval range.")

# ---- Funding checklist ----
st.subheader("📑 Funding Checklist")
chosen = st.selectbox("Select a lender to view checklist:", [""] + list(lender_rules.keys()))
if chosen:
    st.info(f"Required docs for **{chosen}**:")
    for item in lender_rules[chosen]["checklist"]:
        st.write("• " + item)

st.caption("Last updated: " + str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M')))
