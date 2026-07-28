# Multi-Source Data ETL Pipeline
 
A Python (pandas) ETL pipeline that cleans, transforms, and merges three
disparate government datasets into a single unified, analysis-ready dataset.
Built for an ISQS group project.
 
## Source Datasets
 
1. **NY Fed** — Student Loan Debt Per Capita by State (2003-2025)
2. **BEA** — Regional Price Parities by State (2008-2024)
3. **Federal Student Aid** — Loan Portfolio by Location (2025 snapshot)
Each source arrives in a different shape: different header offsets, sheet
names, column layouts, and inconsistent formatting (mixed state abbreviations
vs. full names, embedded footnote rows, wide quarterly columns, etc.).
 
## What the Pipeline Does
 
- **Extract** — reads each dataset from its raw Excel format via `pandas.read_excel`,
  handling per-source header rows and sheet names
- **Transform**
  - Maps state abbreviations to full state names
  - Extracts year values from quarterly column headers using regex
  - Reshapes the NY Fed dataset from wide to long format
  - Filters out footnote/junk rows (e.g. `'Other'`, `'Not Reported'`, rows starting with `*`)
  - Coerces and rounds numeric fields, dropping unparseable rows
- **Load** — merges all three datasets (inner join on State + Year for the first
  two, left join to add the FSA snapshot) and exports a single clean CSV
## Pipeline Output
 
Running `etl_pipeline.py` produces:
 
```
NY Fed:  1,196 rows | 52 states | 2003-2025
BEA RPP: 867 rows   | 51 states | 2008-2024
FSA:     51 rows    | 51 states | snapshot 2025
 
Merged (NY Fed + BEA):  867 rows | 51 states | 2008-2024
Final (+ FSA snapshot): 867 rows | 51 states
```
 
Final output: [`output/student_loan_final.csv`](./output/student_loan_final.csv)
 
## Project Structure
 
```
multi-source-data-etl-pipeline/
├── etl_pipeline.py       # main ETL script
├── data/                 # raw source files
│   ├── area_report_by_year.xlsx
│   ├── BEA_RPP_by_State_Year.xlsx
│   └── Dataset_3_cleaned_Federal_Student_Aid.xlsx
├── output/
│   └── student_loan_final.csv
└── README.md
```
 
## Running It
 
```bash
pip install pandas openpyxl
python etl_pipeline.py
```
 
## Tools Used
Python, pandas, openpyxl
