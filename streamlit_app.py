
import streamlit as st, json, datetime, os

st.set_page_config(page_title="DealPilot – F&I MVP", layout="wide")

# ----------------- Config -----------------
ADMIN_PASS = "dealpilot"
RULES_PATH = "lender_rules.json"
DEFAULT_RULES = {
    "SSFCU":{"max_ltv":134.99,"max_pti":15,"auto_ltv":100,"auto_score":700,
             "backend_base":"Invoice","bureau":"TU","checklist":["Member addendum","CUDL credit app"]},
    "BOA":{"max_ltv":140,"max_pti":18,"auto_ltv":105,"auto_score":680,
            "backend_base":"Invoice","bureau":"EX","checklist":["Driver's license","Credit app"]},
    "TD":{"max_ltv":125,"max_pti":14,"auto_ltv":95,"auto_score":720,
          "backend_base":"Invoice","bureau":"TU","checklist":["Proof of insurance"]},
    "GTCU":{"max_ltv":135,"max_pti":17,"auto_ltv":100,"auto_score":690,
            "backend_base":"Invoice","bureau":"EQ","checklist":["Proof of membership"]}
}
def load_rules():
    if os.path.exists(RULES_PATH):
        with open(RULES_PATH) as f: return json.load(f)
    return DEFAULT_RULES.copy()
def save_rules(r): open(RULES_PATH,"w").write(json.dumps(r,indent=2))

rules = load_rules()
# --------------- Tabs -------------------
tabs = st.tabs(["Deal Builder","Deal Assistant","Admin ▸ Lender Rules"])

with tabs[0]:
    st.header("Deal Builder")
    col0,col1=st.columns([1,3])
    with col0:
        cond=st.radio("Vehicle Condition",["New","Used"])
        vin=st.text_input("VIN (optional)")
        zipc=st.text_input("Customer ZIP")
    with col1:
        amt=st.number_input("Amount Financed ($)",0.0,step=100.0,value=35000.0)
        msrp=st.number_input("MSRP (New) / Retail (Used) ($)",0.0,step=100.0,value=40000.0)
        inv=st.number_input("Invoice (New) / Book (Used) ($)",0.0,step=100.0,value=37000.0)
        term=st.number_input("Loan Term (months)",1,120,value=72)
        rate=st.number_input("Est. Rate %",0.0,20.0,value=8.5,step=0.1)
    # scores
    col_tu,col_ex,col_eq=st.columns(3)
    tu=col_tu.number_input("TU Score",300,900,value=700,step=1,format="%d")
    ex=col_ex.number_input("EX Score",300,900,value=700,step=1,format="%d")
    eq=col_eq.number_input("EQ Score",300,900,value=700,step=1,format="%d")
    income=st.number_input("Gross Monthly Income ($)",0.0,step=100.0,value=6000.0)
    trade_pmt=st.number_input("Payment on Auto Being Replaced ($)",0.0,step=50.0,value=0.0)
    exist=st.number_input("Current Installment Obligations ($)",0.0,step=50.0,value=500.0)
    net_inst=exist-trade_pmt
    if net_inst<0: net_inst=0
    payment=(amt*(1+(rate/100)*(term/12)))/term if term else 0
    dti= (net_inst+payment)/income*100 if income else 0
    pti= payment/income*100 if income else 0
    ltv= amt/inv*100 if inv else 0
    st.metric("Estimated Payment", f"${payment:,.2f}")
    st.metric("DTI %", f"{dti:.2f}")
    st.metric("PTI %", f"{pti:.2f}")
    st.metric("LTV %", f"{ltv:.2f}")
    st.caption("ⓘ DTI = (All monthly debts incl. new payment) ÷ Gross income")

    st.subheader("Lender Matches")
    matches=[]
    alerts=[]
    best_score=max(s for s in [tu,ex,eq] if s>300) if any(s>300 for s in [tu,ex,eq]) else 0
    for name,r in rules.items():
        use_score={"TU":tu,"EX":ex,"EQ":eq}[r["bureau"]]
        if ltv<=r["max_ltv"] and pti<=r["max_pti"]:
            matches.append(name)
        if use_score>=r["auto_score"]:
            delta=ltv - r["auto_ltv"]
            if 0<delta<=5:
                alerts.append(f"{name}: Reduce LTV by {delta:.2f}% (~${delta/100*inv:,.0f}) for instant auto-approval")
    if matches: st.success(", ".join(matches))
    else: st.error("No lender matched.")
    if alerts: st.warning("\n".join(alerts))

    st.subheader("Funding Checklist")
    lender_sel=st.selectbox("Select lender",[""]+list(rules.keys()))
    if lender_sel:
        st.info("Required docs: "+", ".join(rules[lender_sel]["checklist"]))
    st.caption("Last updated "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

with tabs[1]:
    st.header("Deal Assistant (Q&A prototype)")
    q=st.text_input("Ask a lender rule question")
    if st.button("Answer"):
        st.write("Placeholder: rules-based answers coming soon.")

with tabs[2]:
    st.header("Admin ▸ Lender Rules")
    if "auth" not in st.session_state:
        pw=st.text_input("Pass-code",type="password")
        if st.button("Login"):
            st.session_state["auth"]= pw==ADMIN_PASS
        st.stop()
    st.success("Admin mode")
    for name in list(rules.keys()):
        exp=st.expander(name)
        with exp:
            r=rules[name]
            r["max_ltv"]=st.number_input("Max LTV",value=float(r["max_ltv"]),key=name+"ltv")
            r["max_pti"]=st.number_input("Max PTI",value=float(r["max_pti"]),key=name+"pti")
            r["auto_ltv"]=st.number_input("Auto LTV",value=float(r["auto_ltv"]),key=name+"aut")
            r["auto_score"]=st.number_input("Auto Score",value=int(r["auto_score"]),key=name+"score")
            r["backend_base"]=st.selectbox("Backend base",["Invoice","MSRP","Book"],index=["Invoice","MSRP","Book"].index(r["backend_base"]),key=name+"base")
            r["bureau"]=st.selectbox("Preferred bureau",["TU","EX","EQ"],index=["TU","EX","EQ"].index(r["bureau"]),key=name+"bur")
            checklist_str=st.text_area("Checklist (comma)",value=", ".join(r["checklist"]),key=name+"docs")
            r["checklist"]=[d.strip() for d in checklist_str.split(",") if d.strip()]
            if st.button(f"Delete {name}",key=name+"del"):
                del rules[name]
                st.experimental_rerun()
    if st.button("Add Lender"):
        rules["NEWLENDER"]={"max_ltv":130,"max_pti":15,"auto_ltv":100,"auto_score":700,"backend_base":"Invoice","bureau":"TU","checklist":[]}
    if st.button("Save Changes"):
        save_rules(rules)
        st.success("Saved.")
