from search_sampler import SearchSampler

##############################
## SET THESE BEFORE RUNNING ##
##############################
params = { # search params
    'search_term': ['cough', 'sneeze', 'fever'],
    'region': 'US-DC',
    'period_start': '2017-01-01',
    'period_end': '2017-02-01',
    'period_length': 'week'
}
apikey = "<PUT KEY HERE>"
search_name = "flu_symptoms"
output_path = "data"
num_samples = 5

##############################


def run_pull():

    """
    Runs the actual analysis.
    """

    # Create sampling object
    sample = SearchSampler(apikey, search_name, params, output_path=output_path)

    # Option 1: Pull just a single sample
    df_results = sample.pull_data_from_api(format="dataframe")

    # Option 2: Pull a rolling window
    df_results = sample.pull_rolling_window(num_samples=num_samples)

    # Save
    sample.save_file(df_results, append=True)

if __name__ == '__main__':
    run_pull()