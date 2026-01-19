#import matplotlib.pyplot as plt
import seaborn as sns

def get_boxplot(df, columns: list):
    sns.set_theme(style="whitegrid")
    ax = sns.boxplot(x=columns[0], y=columns[1], data=df)
    return ax
