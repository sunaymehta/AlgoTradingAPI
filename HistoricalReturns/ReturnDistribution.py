import pandas as pd
import json
import matplotlib.pyplot as plt


with open('./DataDumpParams.json') as json_file:
    datadumpparams = json.load(json_file)

df = pd.read_csv('./RawData/'+datadumpparams['returns']['asset'])

def compute_shifted_returns_single(df, price_col='close', shift_n=1, return_col_prefix='Return'):

    col_name = f"{return_col_prefix}_{shift_n}d_%"
    
    # Calculate shifted percentage return
    df[col_name] = (df[price_col] / df[price_col].shift(shift_n) - 1) * 100
    
    return df

def create_frequency_table(df):
    # Define bins and labels as per the refined requirement
    bins = [-float('inf'), -3, -2.5, -2, -1.5, -1, -0.75, -0.5, -0.25, 0, 
            0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, float('inf')]
    
    labels = ['< -3%', '-3% to -2.5%', '-2.5% to -2%', '-2% to -1.5%', '-1.5% to -1%',
              '-1% to -0.75%', '-0.75% to -0.5%', '-0.5% to -0.25%', '-0.25% to 0%', 
              '0% to 0.25%', '0.25% to 0.5%', '0.5% to 0.75%', '0.75% to 1%', 
              '1% to 1.5%', '1.5% to 2%', '2% to 2.5%', '2.5% to 3%', '> 3%']

    # Assign bucket labels based on 'Return_1d_%' values
    df['Return_Bucket'] = pd.cut(df['Return_1d_%'], bins=bins, labels=labels, right=False)
    
    # Create frequency table
    freq_table = df['Return_Bucket'].value_counts().sort_index()

    # Convert to DataFrame
    freq_df = freq_table.reset_index().rename(columns={'index': 'Return_Bucket', 'Return_Bucket': 'Frequency'})
    
    return freq_df

# Example usage
# df = pd.read_csv("your_data.csv")  # Load your actual DataFrame
df = compute_shifted_returns_single(df)
freq_table_df = create_frequency_table(df)
print(freq_table_df)

def plot_return_distribution(freq_df):
    """
    Plots a histogram for return buckets with frequency.

    Parameters:
    freq_df (DataFrame): A DataFrame containing return buckets and their corresponding frequencies.
    """
    # Creating the plot
    fig, ax = plt.subplots(figsize=(12, 6))

    # Bar plot centered around 0
    ax.bar(freq_df['Frequency'], freq_df['count'], align='center')

    # Formatting the x-axis for better visibility
    ax.set_xticks(range(len(freq_df['Frequency'])))
    ax.set_xticklabels(freq_df['Frequency'], rotation=45, ha='right')

    # Adding labels and title
    ax.set_xlabel('Return Buckets (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('Distribution of Daily Returns')

    # Adding grid for readability
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    latest_value = df['Return_1d_%'].iloc[-1]
    latest_bucket = df['Return_Bucket'].iloc[-1]

    ax.scatter(latest_bucket, latest_value, 
               color='red', zorder=3, s=100, label='Latest Value')

    # Displaying the plot
    plt.savefig('./Plots/'+datadumpparams['returns']['asset'][:-4]+'_Returns_Distribution.png', dpi=300, bbox_inches='tight')

    plt.show()

    print ('Nifty last recorded close of ', round(latest_value, 2), '% as of date ', df['timestamp'].iloc[-1])

# Example usage
# freq_table_df = create_frequency_table(df)  # Assuming `df` is already populated with data
plot_return_distribution(freq_table_df)



