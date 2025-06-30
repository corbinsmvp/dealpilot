
import streamlit as st

st.set_page_config(page_title="DealPilot - F&I Deal Assistant", layout="centered")

st.title("🚗 DealPilot – F&I Deal Assistant (MVP)")
st.markdown("Use this tool to test deal structures, match lenders, and analyze deal metrics like DTI, PTI, and LTV.")

st.header("📋 Deal Information")
income = st.number_input("Gross Monthly Income ($)", min_value=0)
new_payment = st.number_input("Proposed New Vehicle Payment ($)", min_value=0)
current_obligations = st.number_input("Total Current Installment Obligations ($)", min_value=0)
trade_payment = st.number_input("Trade-in Vehicle Payment (if applicable) ($)", min_value=0)

if st.button("Calculate DTI"):
    dti = ((current_obligations - trade_payment + new_payment) / income) * 100 if income else 0
    st.success(f"Estimated DTI: {dti:.2f}%")

# Placeholder sections for PTI, LTV, and lender logic
st.header("📊 Additional Calculators (Coming Soon)")
st.markdown("- PTI calculator")
st.markdown("- LTV calculator")
st.markdown("- Smart alerts and lender matching")
