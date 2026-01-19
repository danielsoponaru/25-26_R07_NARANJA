import pandas as pd

def read_data(filename):
    return pd.read_csv(filename, index_col = [0])

def remove_column(df, colnames):
    return df.drop(columns=colnames)

def remove_rows_with_nas(df, colnames):
    return df[df[colnames].notna()]

def save_clean_data(df, file):
    df.to_csv(file)
    return None