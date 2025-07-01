
import streamlit as st, json, datetime, os

# ---------- CONFIG ----------
ADMIN_PASS = st.secrets.get("ADMIN_PASS", "dealpilot")  # simple pwd gate
RULES_PATH = "lender_rules.json"

DEFAULT_RULES = {
    "SSFCU": {"max_ltv": 134.99, "max_pti": 15, "auto_ltv": 100, "auto_score": 700,
              "backend_base": "Invoice", "bureau": "TU", "checklist": ["Member addendum","CUDL credit app"]},
    "BOA":   {"max_ltv": 140, "max_pti": 18, "auto_ltv": 105, "auto_score": 680,
              "backend_base": "Invoice", "bureau": "EX", "checklist": ["Driver's license","Credit app"]},
    "TD":    {"max_ltv": 125, "max_pti": 14, "auto_ltv": 95,  "auto_score": 720,
              "backend_base": "Invoice", "bureau": "TU", "checklist": ["Proof of insurance"]},
    "GTCU":  {"max_ltv": 135, "max_pti": 17, "auto_ltv": 100, "auto_score": 690,
              "backend_base": "Invoice", "bureau": "EQ", "checklist": ["Proof of membership"]}
}

# Load / save lender rules ----------------------------------
def load_rules():
    if os.path.exists(RULES_PATH):
        with open(RULES_PATH) as f:
            return json.load(f)
    return DEFAULT_RULES

def save_rules(rules):
    with open(RULES_PATH, "w") as f:
        json.dump(rules, f, indent=2)

lender_rules = load_rules()

# ---------- UI ----------
st.set_page_config(page_title="DealPilot – F&I MVP", layout="wide")
tabs = st.tabs(["Deal Builder", "Deal Assistant", "Admin ▸ Lender Rules"])

# ==== Deal Builder =========================================
with tabs[0]:
    st.title("Deal Builder")
    col0, colA = st.columns([1,3])
    with col0:
        condition = st.radio("Vehicle Condition", ["New","Used"], index=0)
        vin = st.text_input("VIN (optional)")
        cust_zip = st.text_input("Customer ZIP", max_chars=10)
    with colA:
        amt_fin = st.number_input("Amount Financed ($)", min_value=0.0, value=35000.0, step=100.0)
        msrp_or_retail = st.number_input("MSRP (New) / Retail (Used) ($)", min_value=0.0, value=40000.0, step=100.0)
        inv_or_book  = st.number_input("Invoice (New) / Book (Used) ($)", min_value=0.0, value=37000.0, step=100.0)
        term = st.number_input("Loan Term (months)", min_value=1, max_value=120, value=72)
        rate_guess = st.number_input("Est. Rate %", min_value=0.0, value=8.5, step=0.1)

    # Bureau scores
    colTU, colEX, colEQ = st.columns(3)
    tu = colTU.number_input("TU Score", min_value=300, max_value=900, value=700)
    ex = colEX.number_input("EX Score", min_value=300, max_value=900, value=700)
    eq = colEQ.number_input("EQ Score", min_value=300, max_value=900, value=700)

    # Income and existing obligations
    income = st.number_input("Gross Monthly Income ($)", min_value=0.0, value=6000.0, step=100.0)
    payment_guess = (amt_fin * (1 + (rate_guess/100)*(term/12))) / term if term else 0
    exist_inst = st.number_input("Current Installment Obligations ($)", min_value=0.0, value=500.0, step=50.0)

    st.markdown("**Estimated Payment:** ${:,.2f}".format(payment_guess))

    # Calc metrics
    dti = ((exist_inst + payment_guess) / income * 100) if income else 0
    pti = (payment_guess / income * 100) if income else 0
    ltv = (amt_fin / inv_or_book * 100) if inv_or_book else 0

    st.metric("DTI %", f"{dti:.2f}")
    st.metric("PTI %", f"{pti:.2f}")
    st.metric(f"LTV % vs {'Invoice' if condition=='New' else 'Book'}", f"{ltv:.2f}")

    # Lender match + Smart alert
    st.subheader("Lender Matches")
    matches = []
    alerts = []
    best_score = max(tu, ex, eq)
    for name, rule in lender_rules.items():
        use_score = {"TU": tu, "EX": ex, "EQ": eq}[rule["bureau"]]
        if ltv <= rule["max_ltv"] and pti <= rule["max_pti"]:
            matches.append(name)
        # Smart alert within ±5% LTV of auto_ltv if score high
        if use_score >= rule["auto_score"]:
            delta = ltv - rule["auto_ltv"]
            if 0 < delta <= 5:
                alerts.append(f"{name}: Reduce LTV by {delta:.2f}% (~${delta/100*inv_or_book:,.0f}) to hit auto-approval.")

    if matches:
        st.success("Matched lenders: " + ", ".join(matches))
    else:
        st.error("No lenders matched.")

    if alerts:
        st.warning("\n".join(alerts))

    # Funding checklist on lender select
    chosen = st.selectbox("Select a lender to view funding checklist:", [""] + list(lender_rules.keys()))
    if chosen:
        st.info("Required docs: " + ", ".join(lender_rules[chosen]["checklist"]))

    st.caption("Updated: " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ==== Deal Assistant (placeholder) =========================
with tabs[1]:
    st.title("Deal Assistant (Q&A)")
    st.info("Type lender questions like 'who doesn't require DL?' (beta placeholder).")
    q = st.text_input("Ask:")
    if st.button("Answer"):
        st.write("Placeholder answer. (NLP model forthcoming)")

# ==== Admin Tab ============================================
with tabs[2]:
    st.title("Admin ▸ Lender Rules")
    if "auth" not in st.session_state:
        pwd = st.text_input("Pass-code", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASS:
                st.session_state["auth"] = True
            else:
                st.error("Wrong code.")
        st.stop()

    st.success("Admin mode active")

    # Editable table
    for lender in list(lender_rules.keys()):
        exp = st.expander(lender)
        with exp:
            col1, col2, col3 = st.columns(3)
            lender_rules[lender]["max_ltv"] = col1.number_input("Max LTV", value=float(lender_rules[lender]["max_ltv"]), key=lender+"_ltv")
            lender_rules[lender]["max_pti"] = col2.number_input("Max PTI", value=float(lender_rules[lender]["max_pti"]), key=lender+"_pti")
            lender_rules[lender]["auto_ltv"] = col3.number_input("Auto-approval LTV", value=float(lender_rules[lender]["auto_ltv"]), key=lender+"_autoltv")
            lender_rules[lender]["auto_score"] = st.number_input("Auto-approval Score", value=int(lender_rules[lender]["auto_score"]), key=lender+"_autoscore")
            lender_rules[lender]["backend_base"] = st.selectbox("Backend base", ["Invoice","MSRP","Book"], index=["Invoice","MSRP","Book"].index(lender_rules[lender]["backend_base"]), key=lender+"_base")
            lender_rules[lender]["bureau"] = st.selectbox("Preferred bureau", ["TU","EX","EQ"], index=["TU","EX","EQ"].index(lender_rules[lender]["bureau"]), key=lender+"_bureau")
            docs = st.text_area("Checklist (comma separated)", value=", ".join(lender_rules[lender]["checklist"]), key=lender+"_docs")
            lender_rules[lender]["checklist"] = [d.strip() for d in docs.split(",") if d.strip()]
            if st.button(f"Remove {lender}", key=lender+"_del"):
                del lender_rules[lender]
                st.experimental_rerun()

    if st.button("Add Lender"):
        lender_rules["NEW_LENDER"] = {"max_ltv":130,"max_pti":15,"auto_ltv":100,"auto_score":700,"backend_base":"Invoice","bureau":"TU","checklist":[]}

    if st.button("Save All Changes"):
        save_rules(lender_rules)
        st.success("Rules saved.")
