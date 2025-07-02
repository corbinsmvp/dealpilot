
import streamlit as st, os, json, datetime

# ----------------- Configuration -----------------
ADMIN_PASS = st.secrets.get("ADMIN_PASS", "dealpilot")
RULES_FILE = "lender_rules.json"
DEFAULT_RULES = {
    "SSFCU":{"max_ltv":134.99,"max_pti":15,"auto_ltv":100,"auto_score":700,"backend_base":"Invoice","bureau":"TU","checklist":["Member addendum","CUDL credit app"]},
    "BOA":  {"max_ltv":140,"max_pti":18,"auto_ltv":105,"auto_score":680,"backend_base":"Invoice","bureau":"EX","checklist":["DL copy","Credit app"]},
    "TD":   {"max_ltv":125,"max_pti":14,"auto_ltv":95, "auto_score":720,"backend_base":"Invoice","bureau":"TU","checklist":["Proof of insurance"]},
    "GTCU": {"max_ltv":135,"max_pti":17,"auto_ltv":100,"auto_score":690,"backend_base":"Invoice","bureau":"EQ","checklist":["Membership proof"]}
}
def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE) as f: return json.load(f)
    return DEFAULT_RULES
def save_rules(r):
    with open(RULES_FILE,"w") as f: json.dump(r,f,indent=2)
lender_rules = load_rules()

# ----------------- Page Layout -----------------
st.set_page_config(page_title="DealPilot F&I MVP", layout="wide")
tabs = st.tabs(["Deal Builder","Deal Assistant","Admin ▸ Lender Rules"])

# ============ Deal Builder =====================
with tabs[0]:
    st.title("Deal Builder")
    # Vehicle details
    col_cond, col_vin = st.columns([1,3])
    with col_cond:
        condition = st.radio("Vehicle Condition", ["New","Used"], index=0)
    with col_vin:
        vin = st.text_input("VIN (optional)")
    cust_zip = st.text_input("Customer ZIP", max_chars=10)
    # Amounts
    amt_fin = st.number_input("Amount Financed ($)", min_value=0.0, value=35000.0, step=100.0, help="Total amount the customer will finance")
    msrp_retail = st.number_input("MSRP (New) / Retail (Used) ($)", min_value=0.0, value=40000.0, step=100.0, help="Sticker price for new vehicles or retail book for used")
    inv_book = st.number_input("Invoice (New) / Book (Used) ($)", min_value=0.0, value=37000.0, step=100.0, help="Dealer invoice on new or book value on used")
    term = st.number_input("Loan Term (months)", min_value=1, max_value=120, value=72, help="Enter any term up to 120 months")
    rate_est = st.number_input("Est. Rate %", min_value=0.0, value=8.5, step=0.1)
    # Bureau scores (optional)
    col_tu, col_ex, col_eq = st.columns(3)
    tu = col_tu.number_input("TU Score", min_value=300, max_value=900, value=0, help="Leave blank if not pulled")
    ex = col_ex.number_input("EX Score", min_value=300, max_value=900, value=0)
    eq = col_eq.number_input("EQ Score", min_value=300, max_value=900, value=0)
    # Income & debts
    inc = st.number_input("Gross Monthly Income ($)", min_value=0.0, value=6000.0, step=100.0)
    exist_inst = st.number_input("Current Installment Obligations ($)", min_value=0.0, value=500.0, step=50.0, help="All monthly installments on bureau")
    trade_pmt = st.number_input("Payment on Auto Being Replaced ($)", min_value=0.0, value=0.0, step=50.0, help="Payment that will be removed from bureau")
    # Simple payment estimate
    monthly_pmt = (amt_fin * (1 + (rate_est/100)*(term/12))) / term if term else 0
    st.metric("Estimated Payment", f"${monthly_pmt:,.2f}")
    # Metrics
    net_install = exist_inst - trade_pmt
    if net_install <0: net_install =0
    dti = ((net_install+monthly_pmt)/inc*100) if inc else 0
    pti = (monthly_pmt/inc*100) if inc else 0
    ltv = (amt_fin/inv_book*100) if inv_book else 0
    col1,col2,col3 = st.columns(3)
    col1.metric("DTI %", f"{dti:.2f}", help="(Existing debt minus trade-in) + new payment ÷ income")
    col2.metric("PTI %", f"{pti:.2f}", help="New payment ÷ income")
    col3.metric("LTV %", f"{ltv:.2f}", help="Amount financed ÷ invoice/book")
    # Lender match & alerts
    st.subheader("Lender Matches")
    best_score = max(tu, ex, eq)
    if best_score==0: best_score = max(tu,ex,eq) # all zero maybe
    matches = []
    alerts=[]
    for name, rule in lender_rules.items():
        score_used = {"TU":tu,"EX":ex,"EQ":eq}[rule["bureau"]]
        if score_used==0: score_used = best_score
        if ltv<=rule["max_ltv"] and pti<=rule["max_pti"]:
            matches.append(name)
        if score_used>=rule["auto_score"]:
            diff = ltv - rule["auto_ltv"]
            if 0<diff<=5:
                alerts.append(f"{name}: Reduce LTV by {diff:.2f}% (~${diff/100*inv_book:,.0f}) to hit auto-approval")
    if matches:
        st.success("Matched lenders: "+", ".join(matches))
    else:
        st.error("No lenders matched.")
    st.subheader("Smart Alerts")
    if alerts:
        for a in alerts: st.warning(a)
    else:
        st.info("No alerts")
    # Funding checklist
    sel = st.selectbox("Select lender to view funding checklist", [""]+list(lender_rules.keys()))
    if sel:
        st.info("Required docs: "+", ".join(lender_rules[sel]["checklist"]))
    st.caption("Updated "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# =========== Deal Assistant (stub) ==============
with tabs[1]:
    st.title("Deal Assistant Q&A (beta)")
    q = st.text_input("Ask a lender/process question")
    if st.button("Ask"):
        st.write("Placeholder answer — detailed Q&A coming soon")

# =========== Admin Tab ==========================
with tabs[2]:
    st.title("Admin ▸ Lender Rules")
    if "auth" not in st.session_state:
        pwd = st.text_input("Pass-code", type="password")
        if st.button("Login") and pwd==ADMIN_PASS:
            st.session_state["auth"]=True
        st.stop()
    st.success("Admin mode")
    for lender in list(lender_rules.keys()):
        exp=st.expander(lender)
        with exp:
            lender_rules[lender]["max_ltv"] = st.number_input("Max LTV", value=float(lender_rules[lender]["max_ltv"]), key=lender+"ltv")
            lender_rules[lender]["max_pti"] = st.number_input("Max PTI", value=float(lender_rules[lender]["max_pti"]), key=lender+"pti")
            lender_rules[lender]["auto_ltv"] = st.number_input("Auto LTV", value=float(lender_rules[lender]["auto_ltv"]), key=lender+"autoltv")
            lender_rules[lender]["auto_score"] = st.number_input("Auto Score", value=int(lender_rules[lender]["auto_score"]), key=lender+"autoscore")
            lender_rules[lender]["backend_base"] = st.selectbox("Backend base", ["Invoice","MSRP","Book"], index=["Invoice","MSRP","Book"].index(lender_rules[lender]["backend_base"]), key=lender+"bb")
            lender_rules[lender]["bureau"] = st.selectbox("Preferred bureau", ["TU","EX","EQ"], index=["TU","EX","EQ"].index(lender_rules[lender]["bureau"]), key=lender+"bur")
            docs = st.text_area("Checklist (comma separated)", value=", ".join(lender_rules[lender]["checklist"]), key=lender+"docs")
            lender_rules[lender]["checklist"] = [d.strip() for d in docs.split(",") if d.strip()]
            if st.button(f"Remove {lender}", key=lender+"del"):
                del lender_rules[lender]
                st.experimental_rerun()
    if st.button("Add Lender"):
        lender_rules["NEW_LENDER"] = {"max_ltv":130,"max_pti":15,"auto_ltv":100,"auto_score":700,"backend_base":"Invoice","bureau":"TU","checklist":[]}
    if st.button("Save All"):
        save_rules(lender_rules)
        st.success("Saved")
