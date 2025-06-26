
import streamlit as st

st.set_page_config(page_title="DealPilot MVP", layout="wide")

st.title("🚗 DealPilot - F&I Deal Assistant (MVP)")
st.markdown("Welcome to the DealPilot MVP! Use this tool to test deal structures, match lenders, and analyze DTI.")

with st.form("deal_input"):
    st.subheader("🔍 Deal Information")

    income = st.number_input("Gross Monthly Income ($)", min_value=0)
    new_payment = st.number_input("Proposed New Vehicle Payment ($)", min_value=0)
    existing_installments = st.number_input("Total Current Installment Obligations ($)", min_value=0)
    trade_in_payment = st.number_input("Trade-in Vehicle Payment (if applicable) ($)", min_value=0)

    submitted = st.form_submit_button("Calculate DTI")

    if submitted:
        adjusted_debt = new_payment - trade_in_payment
        total_monthly_debt = existing_installments + max(adjusted_debt, 0)
        if income > 0:
            dti = (total_monthly_debt / income) * 100
            st.metric(label="Estimated DTI (%)", value=f"{dti:.2f}%")
        else:
            st.error("Please enter a valid gross monthly income.")
