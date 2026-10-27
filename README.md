# CRYSTAL Quotation Automation

Six-page Word quotation automation system for **ARMATECH ASSOCIATES**.

## Overview
This application automates the generation of professional commercial quotations. It generates a formatted six-page Word document (and PDF) including technical specifications, commercial pricing, terms and conditions, and standard free inclusions based on selected machine models.

## Company Information

**ARMATECH ASSOCIATES**  
W-174A, 'S' Block, M.I.D.C.,  
Bhosari Industrial Estate,  
PUNE - 411 026. (INDIA)

- **Phone:** +91 7020991684 / +91 9699820070
- **Email:** armatech@gmail.com
- **Website:** [www.armatechassociates.com](http://www.armatechassociates.com)

## Key Features
- **Automated Quotation Generation:** Generates a complete 6-page commercial quotation in `.docx` format.
- **VMM & Crystal Modules:** Separate workflows for Video Measuring Machines (VMM) and Crystal products.
- **Default Inclusions:** Automatically includes standard free accessories (e.g., Vision Measuring Software, Optics Calibration kit) on the commercial page.
- **GST & Tax Calculations:** Automatically calculates CGST, SGST, and IGST based on configuration.
- **PDF Export:** Integrated LibreOffice conversion to generate final PDF versions.
- **Quotation History & Customer Database:** Keeps track of previous quotes and customer details.

## Tech Stack
- **Language:** Python 3
- **GUI:** CustomTkinter / Tkinter
- **Document Generation:** `python-docx`
- **PDF Conversion:** LibreOffice Headless / `docx2pdf`
- **Build System:** PyInstaller

## Getting Started

### Prerequisites
Make sure you have Python installed. It is recommended to use a virtual environment.

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/Mayur180/Crystal_quotation_Automation.git
   cd Crystal_quotation_Automation
