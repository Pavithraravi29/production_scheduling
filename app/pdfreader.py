import fitz  # PyMuPDF
import pandas as pd
import re


def extract_data_from_pdf(pdf_path):
    pdf_document = fitz.open(pdf_path)
    data = []
    pattern = re.compile(
        r'(\d+)\s+(\w+(?:-\w+)*)\s+([\w\s-]+)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+)\s+(\d+)\s+(\d+\.\d+)\s+(\d+)')

    for page_num in range(len(pdf_document)):
        page = pdf_document.load_page(page_num)
        text = page.get_text()

        matches = pattern.findall(text)
        for match in matches:
            operation = ' '.join(match[2].split())  # Clean up extra spaces
            row = list(match[:2]) + [operation] + list(match[3:])
            if len(row) == 9:  # Ensure we have 9 columns (Confirm No. might be missing)
                row.append('')  # Add empty string for missing Confirm No.
            data.append(row)

    pdf_document.close()
    return data


def save_to_excel(data, output_path):
    columns = ["Oprn No.", "Wc/Plant", "Operation", "SetUp Time Hrs",
               "Per Pc Time Hrs", "Jmp Qty", "Tot Qty", "Allowed time Hrs",
               "Confirm No:","Actual Time Hrs"]

    df = pd.DataFrame(data, columns=columns)
    df.to_excel(output_path, index=False)
    print(f"Data saved to {output_path}")


# Path to your PDF file
pdf_path = "C:\\Users\\SDC-03\\Desktop\\Pavithra\\ProductionModule\\code\\app\\OARC.pdf"
data = extract_data_from_pdf(pdf_path)

# Save the extracted data to an Excel file
output_excel_path = "C:\\Users\\SDC-03\\Desktop\\Pavithra\\ProductionModule\\code\\app\\OARC_extracted_data.xlsx"
save_to_excel(data, output_excel_path)