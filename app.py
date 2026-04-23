import streamlit as st
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from io import BytesIO
import os

# Page config
st.set_page_config(page_title="HR Payroll Tool", layout="wide")

st.title("💼 Nigerian Payroll Calculator (Compliant PAYE)")

# Sidebar settings
st.sidebar.header("⚙️ Statutory Rates")

pension_rate = st.sidebar.number_input("Pension (%)", value=8.0) / 100
nhf_rate = st.sidebar.number_input("NHF (%)", value=2.5) / 100
nhia_rate = st.sidebar.number_input("NHIA (%)", value=5.0) / 100
itf_rate = st.sidebar.number_input("ITF (%)", value=1.0) / 100
nsitf_rate = st.sidebar.number_input("NSITF (%)", value=1.0) / 100


# ✅ PAYE CALCULATION (COMPLIANT)
def calculate_paye(taxable_income):
    bands = [
        (300000, 0.07),
        (300000, 0.11),
        (500000, 0.15),
        (500000, 0.19),
        (1600000, 0.21),
        (float("inf"), 0.24),
    ]

    tax = 0
    remaining = taxable_income

    for limit, rate in bands:
        amount = min(remaining, limit)
        tax += amount * rate
        remaining -= amount
        if remaining <= 0:
            break

    return tax


# ✅ FULL PAYROLL CALCULATION
def calculate_payroll(monthly_salary):
    annual_salary = monthly_salary * 12

    pension = annual_salary * pension_rate
    nhf = annual_salary * nhf_rate

    # CRA (Consolidated Relief Allowance)
    cra = max(200000, 0.01 * annual_salary) + 0.20 * annual_salary

    taxable_income = annual_salary - (pension + nhf + cra)
    taxable_income = max(0, taxable_income)

    paye = calculate_paye(taxable_income)

    # Other deductions
    nhia = annual_salary * nhia_rate
    itf = annual_salary * itf_rate
    nsitf = annual_salary * nsitf_rate

    total_deductions = pension + nhf + nhia + itf + nsitf + paye

    net_annual = annual_salary - total_deductions
    net_monthly = net_annual / 12

    return {
        "Annual Salary": annual_salary,
        "Pension": pension,
        "NHF": nhf,
        "CRA": cra,
        "Taxable Income": taxable_income,
        "PAYE": paye,
        "NHIA": nhia,
        "ITF": itf,
        "NSITF": nsitf,
        "Total Deductions": total_deductions,
        "Net Annual Salary": net_annual,
        "Net Monthly Salary": net_monthly
    }


# PDF Generator
def generate_pdf(name, result):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    elements = []

    if os.path.exists("logo.png"):
        logo = Image("logo.png", width=60, height=60)
        elements.append(logo)
        elements.append(Spacer(1, 10))

    elements.append(Paragraph("Employee Payslip", styles["Title"]))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Name:</b> {name}", styles["Normal"]))
    elements.append(Spacer(1, 10))

    data = [
        ["Description", "Amount (₦)"],
        ["Annual Salary", f"{result['Annual Salary']:,.2f}"],
        ["Pension", f"{result['Pension']:,.2f}"],
        ["NHF", f"{result['NHF']:,.2f}"],
        ["CRA", f"{result['CRA']:,.2f}"],
        ["Taxable Income", f"{result['Taxable Income']:,.2f}"],
        ["PAYE", f"{result['PAYE']:,.2f}"],
        ["NHIA", f"{result['NHIA']:,.2f}"],
        ["ITF", f"{result['ITF']:,.2f}"],
        ["NSITF", f"{result['NSITF']:,.2f}"],
        ["Total Deductions", f"{result['Total Deductions']:,.2f}"],
        ["Net Monthly Salary", f"{result['Net Monthly Salary']:,.2f}"],
    ]

    table = Table(data, colWidths=[260, 180])

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)
    return buffer


# UI
name = st.text_input("Employee Name")
monthly_salary = st.number_input("Monthly Salary (₦)", min_value=0.0)

if st.button("Calculate"):
    result = calculate_payroll(monthly_salary)

    st.success(f"Net Monthly Salary: ₦{result['Net Monthly Salary']:,.2f}")

    pdf = generate_pdf(name or "Employee", result)

    st.download_button(
        label="⬇️ Download Payslip",
        data=pdf,
        file_name="payslip.pdf",
        mime="application/pdf"
    )
