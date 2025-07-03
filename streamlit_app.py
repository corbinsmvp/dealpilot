
import streamlit as st, json, datetime, os
ADMIN_PASS = st.secrets.get("ADMIN_PASS","dealpilot")
RULES_PATH = "lender_rules.json"
DEFAULT_RULES = {
    "SSFCU":{"max_ltv":134.99,"max_pti":15,"auto_ltv":100,"auto_score":700,"backend_base":"Invoice","bureau":"TU","checklist":["Member addendum","CUDL credit app"]},
    "BOA":{"max_ltv":140,"max_pti":18,"auto_ltv":105,"auto_score":680,"backend_base":"Invoice","bureau":"EX","checklist":["Driver's license","Credit app"]},
    "TD":{"max_ltv":125,"max_pti":14,"auto_ltv":95,"auto_score":720,"backend_base":"Invoice","bureau":"TU","checklist":["Proof of insurance"]},
    "GTCU":{"max_ltv":135,"max_pti":17,"auto_ltv":100,"auto_score":690,"backend_base":"Invoice","bureau":"EQ","checklist":["Proof of membership"]}
}
def load_rules():
    if os.path.exists(RULES_PATH):
        with open(RULES_PATH) as f:
            return json.load(f)
    return DEFAULT_RULES
def save_rules(r):
    with open(RULES_PATH,"w") as f:
        json.dump(r,f,indent=2)
rules = load_rules()
st.set_page_config(page_title="DealPilot – F&I MVP", layout="wide")
tabs = st.tabs(["Deal Builder","Deal Assistant","Admin ▸ Lender Rules"])
# ----- Deal Builder -----
with tabs[0]:
    st.title("Deal Builder")
    colL,colR = st.columns([1,3])
    with colL:
        condition = st.radio("Vehicle Condition",["New","Used"], index=0)
        vin = st.text_input("VIN (optional)")
        cust_zip = st.text_input("Customer ZIP")
    with colR:
        amt_fin = st.number_input("Amount Financed ($)",0.0,step=100.0,value=35000.0)
        msrp_retail = st.number_input("MSRP (New) / Retail (Used) ($)",0.0,step=100.0,value=40000.0)
        inv_book = st.number_input("Invoice (New) / Book (Used) ($)",0.0,step=100.0,value=37000.0)
        term = st.number_input("Loan Term (months)",1,120,value=72)
        rate = st.number_input("Est. Rate %",0.0,step=0.1,value=8.5)
    st.markdown("### Credit Scores (leave blank if not pulled)")
    c1,c2,c3 = st.columns(3)
    def _parse(s):
        s=s.strip()
        return int(s) if s.isdigit() and 300<=int(s)<=900 else None
    tu=_parse(c1.text_input("TU Score",""))
    ex=_parse(c2.text_input("EX Score",""))
    eq=_parse(c3.text_input("EQ Score",""))
    income = st.number_input("Gross Monthly Income ($)",0.0,step=100.0,value=6000.0)
    trade_pmt = st.number_input("Payment on Auto Being Replaced ($)",0.0,step=50.0,value=0.0)
    curr_inst = st.number_input("Current Installment Obligations ($)",0.0,step=50.0,value=500.0)
    payment_est = (amt_fin*(1+(rate/100)*(term/12)))/term if term else 0
    st.write(f"**Estimated Payment:** ${payment_est:,.2f}")
    dti = ((curr_inst-trade_pmt+payment_est)/income*100) if income else 0
    pti = (payment_est/income*100) if income else 0
    ltv = (amt_fin/inv_book*100) if inv_book else 0
    m1,m2,m3 = st.columns(3)
    m1.metric("DTI %",f"{dti:.2f}",help="(Current obligations - trade payment + new payment) / income")
    m2.metric("PTI %",f"{pti:.2f}",help="New payment / income")
    m3.metric("LTV %",f"{ltv:.2f}",help="Amount financed / Invoice or Book")
    st.subheader("Lender Matches")
    matches=[]; alerts=[]
    best_score=max([s for s in (tu,ex,eq) if s] or [0])
    for name,r in rules.items():
        score = {"TU":tu,"EX":ex,"EQ":eq}.get(r["bureau"]) or best_score
        if score and ltv<=r["max_ltv"] and pti<=r["max_pti"]:
            matches.append(name)
        if score and score>=r["auto_score"]:
            delta=ltv-r["auto_ltv"]
            if 0<delta<=5:
                alerts.append(f"{name}: Lower LTV by {delta:.2f}% (~${delta/100*inv_book:,.0f}) for auto-approval")
    st.success(", ".join(matches) if matches else "No lenders matched.")
    st.subheader("Smart Alerts")
    st.warning("\n".join(alerts) if alerts else "No Smart Alerts.")
    chosen = st.selectbox("Funding Checklist",[""]+list(rules.keys()))
    if chosen:
        st.info("Docs: "+", ".join(rules[chosen]["checklist"]))
    st.caption("Updated "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
# ----- Admin -----
with tabs[2]:
    st.title("Admin ▸ Lender Rules")
    if "auth" not in st.session_state:
        if st.text_input("Pass-code",type="password")==ADMIN_PASS:
            st.session_state["auth"]=True
        else:
            st.stop()
    for ln in list(rules.keys()):
        with st.expander(ln):
            rules[ln]["max_ltv"]=st.number_input("Max LTV",value=float(rules[ln]["max_ltv"]),key=ln+"_ltv")
            rules[ln]["max_pti"]=st.number_input("Max PTI",value=float(rules[ln]["max_pti"]),key=ln+"_pti")
            rules[ln]["auto_ltv"]=st.number_input("Auto LTV",value=float(rules[ln]["auto_ltv"]),key=ln+"_alv")
            rules[ln]["auto_score"]=st.number_input("Auto Score",value=int(rules[ln]["auto_score"]),key=ln+"_as")
            rules[ln]["backend_base"]=st.selectbox("Backend base",["Invoice","MSRP","Book"],index=["Invoice","MSRP","Book"].index(rules[ln]["backend_base"]),key=ln+"_bb")
            rules[ln]["bureau"]=st.selectbox("Pref Bureau",["TU","EX","EQ"],index=["TU","EX","EQ"].index(rules[ln]["bureau"]),key=ln+"_br")
            rules[ln]["checklist"]=st.text_area("Checklist (comma separated)",value=", ".join(rules[ln]["checklist"]),key=ln+"_cl").split(",")
            if st.button(f"Delete {ln}",key=ln+"_del"):
                del rules[ln]
                st.experimental_rerun()
    if st.button("Add Lender"):
        rules["NEW_LENDER"]={"max_ltv":130,"max_pti":15,"auto_ltv":100,"auto_score":700,"backend_base":"Invoice","bureau":"TU","checklist":[]}
    if st.button("Save All"):
        save_rules(rules)
        st.success("Saved!")
