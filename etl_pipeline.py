"""
Multi-Source Data ETL Pipeline
ISQS Group Project

Cleans, transforms, and merges three government datasets into a single
analysis-ready dataset:
  1. NY Fed — Student Loan Debt Per Capita by State (2003-2025)
  2. BEA — Regional Price Parities by State (2008-2024)
  3. Federal Student Aid — Portfolio by Location (2025 snapshot)

Author: Aniston Guy
"""

import pandas as pd

# ─────────────────────────────────────────────────────────────────────
# DATASET 1: NY Fed — Student Loan Debt Per Capita by State
# ─────────────────────────────────────────────────────────────────────

def load_nyfed(filepath):
    state_map = {
        'AK':'Alaska','AL':'Alabama','AR':'Arkansas','AZ':'Arizona',
        'CA':'California','CO':'Colorado','CT':'Connecticut',
        'DC':'District of Columbia','DE':'Delaware','FL':'Florida',
        'GA':'Georgia','HI':'Hawaii','IA':'Iowa','ID':'Idaho',
        'IL':'Illinois','IN':'Indiana','KS':'Kansas','KY':'Kentucky',
        'LA':'Louisiana','MA':'Massachusetts','MD':'Maryland','ME':'Maine',
        'MI':'Michigan','MN':'Minnesota','MO':'Missouri','MS':'Mississippi',
        'MT':'Montana','NC':'North Carolina','ND':'North Dakota',
        'NE':'Nebraska','NH':'New Hampshire','NJ':'New Jersey',
        'NM':'New Mexico','NV':'Nevada','NY':'New York','OH':'Ohio',
        'OK':'Oklahoma','OR':'Oregon','PA':'Pennsylvania','PR':'Puerto Rico',
        'RI':'Rhode Island','SC':'South Carolina','SD':'South Dakota',
        'TN':'Tennessee','TX':'Texas','UT':'Utah','VA':'Virginia',
        'VT':'Vermont','WA':'Washington','WI':'Wisconsin',
        'WV':'West Virginia','WY':'Wyoming'
    }
    df = pd.read_excel(filepath, sheet_name='studentloan', header=8)
    df = df.dropna(subset=['state'])
    df = df[df['state'].str.len() == 2].copy()
    year_cols = [c for c in df.columns if str(c).startswith('Q4_')]
    df_long = df[['state'] + year_cols].melt(
        id_vars='state',
        var_name='Quarter',
        value_name='StudentLoan_PerCapita_USD'
    )
    df_long['Year'] = df_long['Quarter'].str.extract(r'Q4_(\d{4})').astype(int)
    df_long['State'] = df_long['state'].map(state_map)
    df_long = df_long.dropna(subset=['State'])
    df_long = df_long[['Year', 'State', 'StudentLoan_PerCapita_USD']]
    df_long = df_long.sort_values(['State', 'Year']).reset_index(drop=True)
    return df_long


# ─────────────────────────────────────────────────────────────────────
# DATASET 2: BEA — Regional Price Parities by State
# ─────────────────────────────────────────────────────────────────────

def load_bea(filepath):
    df = pd.read_excel(filepath, sheet_name='BEA_RPP_by_State_Year', skiprows=1)
    df = df.rename(columns={'RPP All Items (Index, US Avg = 100)': 'RPP_AllItems'})
    df['Year'] = df['Year'].astype(int)
    df['RPP_AllItems'] = pd.to_numeric(df['RPP_AllItems'], errors='coerce').round(3)
    df['State'] = df['State'].astype(str).str.strip()
    df = df.dropna(subset=['State', 'RPP_AllItems'])
    df = df.sort_values(['State', 'Year']).reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────
# DATASET 3: Federal Student Aid — Portfolio by Location
# ─────────────────────────────────────────────────────────────────────

def load_fsa(filepath):
    df = pd.read_excel(filepath, sheet_name=0, header=None, skiprows=2)
    df.columns = ['Year', 'State', 'Balance_Billions', 'Borrowers_Thousands']
    df = df[pd.to_numeric(df['Year'], errors='coerce') == 2025]
    df = df.dropna(subset=['State'])
    df['State'] = df['State'].astype(str).str.strip()
    df = df[~df['State'].isin(['Other', 'Not Reported', 'nan'])]
    df = df[~df['State'].str.startswith('*')]
    df['Balance_Billions'] = pd.to_numeric(df['Balance_Billions'], errors='coerce').round(2)
    df['Borrowers_Thousands'] = pd.to_numeric(df['Borrowers_Thousands'], errors='coerce').round(1)
    df['Year'] = 2025
    df = df[['Year', 'State', 'Balance_Billions', 'Borrowers_Thousands']]
    df = df.sort_values('State').reset_index(drop=True)
    return df


# ─────────────────────────────────────────────────────────────────────
# MERGE 1: NY Fed + BEA (joined on State + Year, 2008-2024)
# ─────────────────────────────────────────────────────────────────────

def merge_nyfed_bea(df_nyfed, df_bea):
    df_merged = pd.merge(
        df_nyfed,
        df_bea,
        on=['Year', 'State'],
        how='inner'
    )
    df_merged = df_merged.sort_values(['State', 'Year']).reset_index(drop=True)
    return df_merged


# ─────────────────────────────────────────────────────────────────────
# MERGE 2: Add FSA snapshot (joined on State only)
# ─────────────────────────────────────────────────────────────────────

def merge_all(df_merged, df_fsa):
    df_final = pd.merge(
        df_merged,
        df_fsa[['State', 'Balance_Billions', 'Borrowers_Thousands']],
        on='State',
        how='left'
    )
    df_final = df_final.sort_values(['State', 'Year']).reset_index(drop=True)
    return df_final


# ─────────────────────────────────────────────────────────────────────
# RUN PIPELINE
# ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    NYFED_PATH = 'data/area_report_by_year.xlsx'
    BEA_PATH   = 'data/BEA_RPP_by_State_Year.xlsx'
    FSA_PATH   = 'data/Dataset_3_cleaned_Federal_Student_Aid.xlsx'
    OUTPUT_PATH = 'output/student_loan_final.csv'

    print("Loading datasets...")
    df_nyfed = load_nyfed(NYFED_PATH)
    df_bea   = load_bea(BEA_PATH)
    df_fsa   = load_fsa(FSA_PATH)

    print(f"  NY Fed:  {len(df_nyfed):,} rows | {df_nyfed.State.nunique()} states | {df_nyfed.Year.min()}-{df_nyfed.Year.max()}")
    print(f"  BEA RPP: {len(df_bea):,} rows  | {df_bea.State.nunique()} states | {df_bea.Year.min()}-{df_bea.Year.max()}")
    print(f"  FSA:     {len(df_fsa):,} rows  | {df_fsa.State.nunique()} states | snapshot {df_fsa['Year'].iloc[0]}")

    print("\nMerging NY Fed + BEA on State + Year...")
    df_merged = merge_nyfed_bea(df_nyfed, df_bea)
    print(f"  Merged:  {len(df_merged):,} rows | {df_merged.State.nunique()} states | {df_merged.Year.min()}-{df_merged.Year.max()}")

    print("\nMerging FSA snapshot into final dataset...")
    df_final = merge_all(df_merged, df_fsa)
    print(f"  Final:   {len(df_final):,} rows | {df_final.State.nunique()} states")

    print("\nPreview of final dataset:")
    print(df_final.head(10).to_string(index=False))

    df_final.to_csv(OUTPUT_PATH, index=False)
    print(f"\nFile saved: {OUTPUT_PATH}")
