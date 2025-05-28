import streamlit as st
import pandas as pd
import datetime
from fpdf import FPDF
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import zipfile
import base64
import traceback
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Streamlit app setup
st.set_page_config(page_title="Trainer Invoice Generator")
st.title("📄 Trainer Invoice Generator")

# Input billing date
billing_date = st.text_input("Enter Billing Date (dd-mm-yyyy):")

if billing_date:
    try:
        # Parse and format date
        selected_date = billing_date.replace("/", "-").strip()
        target_date = datetime.datetime.strptime(selected_date, "%d-%m-%Y")

        # Credentials dictionary from environment variables
        creds_dict = {
            "type": os.getenv("TYPE"),
            "project_id": os.getenv("PROJECT_ID"),
            "private_key_id": os.getenv("PRIVATE_KEY_ID"),
            "private_key": os.getenv("PRIVATE_KEY").replace("\\n", "\n"),  # 🔥 THIS LINE IS CRUCIAL
            "client_email": os.getenv("CLIENT_EMAIL"),
            "client_id": os.getenv("CLIENT_ID"),
            "auth_uri": os.getenv("AUTH_URI"),
            "token_uri": os.getenv("TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("UNIVERSE_DOMAIN"),
        }

        # Save credentials to a temporary JSON file
        with open("temp_creds.json", "w") as f:
            json.dump(creds_dict, f)

        # Authorize access
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("temp_creds.json", scope)
        client = gspread.authorize(creds)

        # Read data from Google Sheet
        sheet = client.open("Calendar CDB").worksheet("Trainer Bills")
        df = pd.DataFrame(sheet.get_all_records())
        df["Billing Date"] = pd.to_datetime(df["Billing Date"], dayfirst=True, errors='coerce')

        st.write("Selected Billing Date:", target_date.strftime("%Y-%m-%d"))
        st.write("Available Billing Dates in Sheet:", df["Billing Date"].dt.strftime("%Y-%m-%d").unique())

        filtered_df = df[df["Billing Date"] == target_date]

        if filtered_df.empty:
            st.warning("❌ No billing records found for that date.")
        else:
            output_folder = "invoices"
            os.makedirs(output_folder, exist_ok=True)
            pdf_files = []

            for index, row in filtered_df.iterrows():
                bill_no = f"{row['Sr No']}_{target_date.strftime('%d%m%Y')}"
                trainer_name = row["Name of the Trainer"]
                project_code = row["Project Code"]
                domain = row["Domain"]
                topic = row["Topic"]
                from_date = row["From Date"]
                to_date = row["End date"]
                charges_per_hour = row["Charges/ Hour"]
                charges_per_day = row["Charges/ Day"]
                hours = row["No of Hours"]
                days = row["No of Days"]
                food_and_lodging = row["Food and Lodging"]
                travel = row["Travel"]
                tds = row["TDS Deduction"]
                adhoc = row["Adhoc Addition/Deduction"]
                net_payment = row["Net Payment"]
                total_cost = row["Total"]
                total_training = row["Total Training Charges"]
                bank_name = row["Bank Name"]
                account_no = row["Account Number"]
                ifsc = row["IFSC Code"]
                pan = row["PAN Card"]
                name_in_bank = row["Name in Bank"]
                no_of_sessions = row["No of Sessions"]
                no_of_students = row["No of Students"]

                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)

                watermark_path = "logo-1.png"
                if os.path.exists(watermark_path):
                    watermark_width = 70
                    watermark_height = 30
                    x_center = (210 - watermark_width) / 2
                    y_center = (297 - watermark_height) / 2
                    pdf.image(watermark_path, x=x_center, y=y_center, w=watermark_width, h=watermark_height)

                # Header
                pdf.set_fill_color(200, 200, 200)
                pdf.rect(x=0, y=10, w=210, h=15, style='F')
                if os.path.exists(watermark_path):
                    pdf.image(watermark_path, x=10, y=10, w=30, h=15)
                pdf.set_font("Arial", "B", 16)
                pdf.set_xy(0, 10)
                pdf.cell(210, 15, "Trainer Invoice", ln=True, align="C")
                pdf.ln(10)

                # Addresses
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 8, "To", ln=True)
                pdf.multi_cell(0, 5, "Gryphon Academy\n9th Floor, Olympia Business House (Achalare)\nNext to Supreme HQ, Mum - Pune Highway, Baner\nPune, MH - 411045")
                pdf.ln(2)
                pdf.cell(0, 8, "From", ln=True)
                pdf.multi_cell(0, 5, f"{trainer_name}")
                pdf.ln(3)

                # Bill & bank details
                pdf.set_font("Arial", "B", 10)
                pdf.cell(90, 8, "Bill Details", 1)
                pdf.cell(0, 8, "Account Details of Trainer", 1, ln=True)
                pdf.set_font("Arial", "", 9)
                pdf.cell(90, 6, f"Bill Number: {bill_no}", 1)
                pdf.cell(0, 6, f"Name in Bank: {name_in_bank}", 1, ln=True)
                pdf.cell(90, 6, f"Project Code: {project_code}", 1)
                pdf.cell(0, 6, f"Bank Name: {bank_name}", 1, ln=True)
                pdf.cell(90, 6, f"Domain: {domain}", 1)
                pdf.cell(0, 6, f"Bank Account No: {account_no}", 1, ln=True)
                pdf.cell(90, 6, f"Topic: {topic}", 1)
                pdf.cell(0, 6, f"IFSC Code: {ifsc}", 1, ln=True)
                pdf.cell(90, 6, f"From: {from_date}", 1)
                pdf.cell(0, 6, f"PAN Card: {pan}", 1, ln=True)
                pdf.cell(90, 6, f"To: {to_date}", 1)
                pdf.cell(0, 6, f"Billing Date: {selected_date}", 1, ln=True)

                # Charges Table
                pdf.ln(5)
                pdf.set_font("Arial", "B", 10)
                pdf.cell(60, 8, "Charges", 1)
                pdf.cell(40, 8, "Rate", 1)
                pdf.cell(40, 8, "Total Hrs/Days", 1)
                pdf.cell(0, 8, "Total Amount", 1, ln=True)

                pdf.set_font("Arial", "", 9)
                pdf.cell(60, 6, "Training Charges per Hour", 1)
                pdf.cell(40, 6, f"Rs. {charges_per_hour}", 1)
                pdf.cell(40, 6, f"{hours}", 1)
                pdf.cell(0, 6, f"Rs. {total_training}", 1, ln=True)

                pdf.cell(60, 6, "Training Charges per Day", 1)
                pdf.cell(40, 6, f"Rs. {charges_per_day}", 1)
                pdf.cell(40, 6, f"{days}", 1)
                try:
                    pdf.cell(0, 6, f"Rs. {int(days) * float(charges_per_day)}", 1, ln=True)
                except:
                    pdf.cell(0, 6, f"Rs. -", 1, ln=True)

                pdf.cell(60, 6, "Food and Lodging", 1)
                pdf.cell(40, 6, "", 1)
                pdf.cell(40, 6, "", 1)
                pdf.cell(0, 6, f"Rs. {food_and_lodging}", 1, ln=True)

                pdf.cell(60, 6, "Travel", 1)
                pdf.cell(40, 6, "", 1)
                pdf.cell(40, 6, "", 1)
                pdf.cell(0, 6, f"Rs. {travel}", 1, ln=True)

                # Totals
                pdf.set_font("Arial", "B", 10)
                pdf.cell(140, 6, "Total Amount", 1)
                pdf.cell(0, 6, f"Rs. {total_cost}", 1, ln=True)
                pdf.cell(140, 6, "Adhoc Addition/Deduction", 1)
                pdf.cell(0, 6, f"Rs. {adhoc}", 1, ln=True)
                pdf.cell(140, 6, "Less (TDS)", 1)
                pdf.cell(0, 6, f"Rs. {tds}", 1, ln=True)
                pdf.cell(140, 6, "Net Payment", 1)
                pdf.cell(0, 6, f"Rs. {net_payment}", 1, ln=True)

                # Summary
                pdf.ln(5)
                pdf.set_font("Arial", "B", 10)
                pdf.cell(0, 8, "Summary of Training", 1, ln=True)
                pdf.set_font("Arial", "", 9)
                pdf.cell(70, 6, "No of Sessions", 1)
                pdf.cell(0, 6, f"{no_of_sessions}", 1, ln=True)
                pdf.cell(70, 6, "No of Hours", 1)
                pdf.cell(0, 6, f"{hours}", 1, ln=True)
                pdf.cell(70, 6, "No of Attendees", 1)
                pdf.cell(0, 6, f"{no_of_students}", 1, ln=True)
                pdf.cell(70, 6, "Average Students/ Batch", 1)
                pdf.cell(0, 6, "-", 1, ln=True)

                # Footer
                pdf.ln(10)
                col_width = 38
                left_margin = (210 - (col_width * 5)) / 2
                pdf.set_x(left_margin)
                pdf.set_font("Arial", "", 9)
                pdf.cell(col_width, 6, "L & D Manager", 1, 0, 'C')
                pdf.cell(col_width, 6, "Co-founder", 1, 0, 'C')
                pdf.cell(col_width, 6, "Paid By", 1, 0, 'C')
                pdf.cell(col_width, 6, "Date/Stamp", 1, 0, 'C')
                pdf.cell(col_width, 6, "Ref. ID", 1, 1, 'C')
                pdf.set_x(left_margin)
                for _ in range(5):
                    pdf.cell(col_width, 12, "", 1, 0, 'C')
                pdf.ln()

                # Save the PDF
                filepath = os.path.join(output_folder, f"Trainer_Invoice_{bill_no}.pdf")
                pdf.output(filepath)
                pdf_files.append(filepath)

            # ZIP the PDFs
            zip_filename = "Trainer_Invoices.zip"
            zip_path = os.path.join(output_folder, zip_filename)
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for pdf_file in pdf_files:
                    zipf.write(pdf_file, os.path.basename(pdf_file))

            # Download link
            with open(zip_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
                href = f'<a href="data:application/zip;base64,{b64}" download="{zip_filename}">📥 Download ZIP of Invoices</a>'
                st.markdown(href, unsafe_allow_html=True)

        # Remove temporary credentials
        os.remove("temp_creds.json")

    except Exception as e:
        st.error("❌ An unexpected error occurred.")
        st.code(traceback.format_exc())
