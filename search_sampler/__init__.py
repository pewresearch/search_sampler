import os
import pandas
import time

from datetime import datetime, timedelta
from collections import defaultdict
from copy import deepcopy

from googleapiclient.discovery import build

"""
All functions that are used for querying, processing, and saving
the data are located here.
"""

VALID_PERIOD_LENGTHS = ["day", "week", "month"]


class SearchSampler(object):
    """
    TrendsSampler contains all functions required to sample the Google Health API

    :param api_key: The API key you received from Google
    :param search_name: A suffix for your output file.  It will be placed in the `{output_path}/{region}`\
    folder with the filename `{region}-{search_name}.csv`.
    :param search_params: A dictionary containing parameters. Must contain keys with:\
    `search_term, region, period_start, period_end, period_length`\
    Example: {\
        "region": "US-DC",\
        "search_term": "test",\
        "period_start": "2017-01-01",\
        "period_end": "2017-01-31",\
        "period_length": "week"\
    }\
    The `search_term` can be a single string, or a list of strings.  It can also include Boolean logic.\
    See the report methodology for more details.  The `region` can be a country, state, or DMA.\
    States are formatted like `US-CA`, DMAs are a 3-digit code (see Nielsen for info).\
    The `period_start` and `period_end` parameters need to be in the format `YYYY-MM-DD`.\
    The `period_length` can be "day", "week", or "month" - but we have only tested this extensively\
    with week.
    :param server: The endpoint to which requests will be made (default is "https://www.googleapis.com")
    :param version: The API version to use (default is `v1beta`)
    :param output_path: The path to the folder where query results will be saved (folder will be created\
    if it doesn't already exist.)

    :Example:

    >>> params = {
        'search_term': ['cough', 'sneeze', 'fever'],
        'region': 'US-DC',
        'period_start': '2017-01-01',
        'period_end': '2017-02-01',
        'period_length': 'week'
    }
    >>> search_name = "flu_symptoms"
    >>> output_path = "data"
    >>> num_samples = 5
    >>> from SearchSampler.sampler import SearchSampler
    >>> sampler = SearchSampler(api_key, search_name, params, output_path=output_path)
    >>> df_results = sampler.pull_rolling_window(num_samples=num_samples)
    >>> sampler.save_file(df_results, append=True)

    """

    def __init__(
            self,
            api_key,
            search_name,
            search_params,
            server="https://www.googleapis.com",
            version="v1beta",
            output_path="data"
    ):

        # Basic variables
        if not api_key:
            raise SystemError('ERROR: Must provide an api_key as the first parameter')
        self._search_name = search_name
        self._server = server
        self._version = version
        self.service = self._get_service(api_key)

        # Below exception is to ensure that people actually provide something for an output_path
        if output_path == "":
            raise ValueError("Please provide an output path")

        self.output_path = output_path

        ## Search parameters
        # Initialize a dictionary with default parameters
        self.params = {
            "search_term": None,
            "region": None,
            "period_start": None,
            "period_end": None,
            "period_length": "week"
        }
        # Force search_term to be a dictionary
        if not isinstance(search_params, dict):
            raise ValueError('ERROR: search_params needs to be a dictionary')
        if type(search_params.get("search_term", None)) == str:
            search_params["search_term"] = [search_params["search_term"]]
        self.params.update(search_params)
        for k, v in self.params.items():
            if not v:
                raise SystemError('ERROR: Must provide a {}'.format(k))

        # Check that start date is before end date
        if self.params['period_end'] < self.params['period_start']:
            raise ValueError('ERROR: start of period must be before end of period')

    def _get_service(self, api_key):

        """
        Sets up the connection to the Google Trends Health API

        :param api_key: API Key
        :return: Properly configured API object

        """

        url = "/".join([
            str(self._server),
            'discovery/v1/apis/trends',
            str(self._version),
            "rest"
        ])
        service = build(
            'trends',
            self._version,
            developerKey=api_key,
            discoveryServiceUrl=url
        )

        return service

    def _get_file_path(self):

        """
        :return: 2-tuple containing the file path and file name

        """

        str_path = os.path.join(str(self.output_path), str(self.params["region"]))
        str_file_name = '{region}-{identifier}.csv'.format(
            region=self.params['region'],
            identifier=self._search_name
        )
        return (str_path, str_file_name)

    def load_file(self):

        """
        Loads a csv file for later analysis, based on naming scheme used within class

        :return: Pandas dataframe

        """

        load_path, load_filename = self._get_file_path()
        full_file_path = os.path.join(str(load_path), str(load_filename))
        print('Attempting to load local file: {}'.format(full_file_path))
        return pandas.read_csv(full_file_path)

    def save_file(self, df, append=True):

        """
        Saves data in df to folder, based on the following structure\:
        `{output_path}/{region}/{region}-{search_identifier}.csv`

        :param df: Dataframe to save. Expects format\: Period, value (though names don't matter)
        :param append: Whether or not to add the new results to an existing file with the same name.\
        Setting this to `False` will overwrite any existing file.
        :return: None

        """
        # set up paths and file name
        load_path, load_filename = self._get_file_path()

        # Verify the directory exists; if not, create
        if not os.path.exists(load_path):
            os.makedirs(load_path)
        # If appending results, load previous results and join
        else:
            if append:
                try:
                    df_prev_results = self.load_file()
                except FileNotFoundError:
                    print('No previous data found. Will save to new file')
                else:
                    df = pandas.concat([df_prev_results, df])

        full_file_path = os.path.join(str(load_path), str(load_filename))
        print('Saving local file: {}'.format(full_file_path))
        df.to_csv(full_file_path, encoding='utf-8', index=False)

    def _perform_pull(self, graph_object, attempt=0, sleep_minutes=1, limit=20):

        """
        Given a connection object to the API, return a set of unformatted data. This method
        accommodates API connection problems up to the specified limit (default 20).

        :param graph_object: Properly formatted
        :param attempt: Internal, do not use. Function uses in instances in which the API fails.
        :param sleep_minutes:
        :param limit:
        :return: Unformatted data from API

        """

        # Call API
        # Enclosed in a try/except block because the API will randomly return a Rate Limit exceeded error
        # Usually as an HTTPError

        try:
            response_health = graph_object.execute()
        except Exception as msg:
            attempt += 1
            if attempt <= limit:
                if attempt % 5 == 0:
                    print(
                        'WARNING: Attempt #{}. This may require an extended period. Sleeping for 5 minutes. \
                        Error message:\n {}'.format(attempt, str(msg))
                    )
                    # Sleep for 5 minutes
                    time.sleep(5 * 60)
                else:
                    print(
                        'WARNING: Attempt #{}. Sleeping for just 1 minute. \
                        Error message:\n {}'.format(attempt, str(msg))
                    )
                    # Sleep for 1 minutes
                    time.sleep(sleep_minutes * 60)
                response_health = self._perform_pull(graph_object, attempt)
            else:
                # Give up entirely
                raise SystemError("Attempted query 5 times and couldn't connect")
                response_health = None

        return response_health

    def pull_data_from_api(self, params=None, format='dict'):

        """
        Pulls data from the API given a set of search terms and other restrictions.

        :param params: Set of search parameters. Uses the object-level search params (from __init__) if empty.
        :return: Dataframe with results from API that match parameters.

        """

        # set local parameters to class parameters if necessary
        if not params:
            params = deepcopy(self.params)

        # Check period_length
        if params['period_length'] not in VALID_PERIOD_LENGTHS:
            raise SystemError('Period length {} is of the wrong type.'.format(params['period_length']))

        # Check region type. Because this changes the parameters in the API call, this sets up the API call
        # See the difference between geoRestriction_region, _country, and _dma
        if isinstance(params['region'], list):
            test_region = str(params['region'][0])
            params['region'] = "'{}'".format("', '".join(str(params['region'])))
        else:
            test_region = str(params['region'])

        if test_region[:2] == 'US':
            # nation-wide
            if test_region == 'US':
                graph_health = self.service.getTimelinesForHealth(
                    terms=params['search_term'],
                    geoRestriction_country=params['region'],
                    time_startDate=params['period_start'],
                    time_endDate=params['period_end'],
                    timelineResolution=params['period_length']
                )
            # Can only use multiple values for states and DMAs
            # Cannot mix national, state or DMA in the same call, unfortunately
            # Valid options are ISO-3166-2
            else:
                graph_health = self.service.getTimelinesForHealth(
                    terms=params['search_term'],
                    geoRestriction_region=params['region'],
                    time_startDate=params['period_start'],
                    time_endDate=params['period_end'],
                    timelineResolution=params['period_length']
                )
        else:
            # This assumes a DMA
            # To properly retrieve data, it needs to be a number, so test for this first
            # For more, see: https://support.google.com/richmedia/answer/2745487
            if not isinstance(params['region'], int):
                raise ValueError('Region "{}" is not an integer, but looks like it is meant to be a DMA' \
                                 .format(params['region']))

            # otherwise
            graph_health = self.service.getTimelinesForHealth(
                terms=params['search_term'],
                geoRestriction_dma=params['region'],
                time_startDate=params['period_start'],
                time_endDate=params['period_end'],
                timelineResolution=params['period_length']
            )

        # Now, finally, call the API
        print('INFO: Running period {} - {}'.format(params['period_start'], params['period_end']))
        response_health = self._perform_pull(graph_health)
        if not response_health:
            return None
        else:
            d_results = {}
            for results in response_health['lines']:
                curr_term = results['term']
                df = pandas.DataFrame(results['points'])
                # re-format date into actual date objects
                try:
                    df['period'] = pandas.to_datetime(df.date, format='%b %d %Y')
                except:
                    df['period'] = pandas.to_datetime(df.date, format='%b %Y')
                d_results[curr_term] = df
            if format == 'dataframe':
                # process of saving is slightly different when asking for multiple 
                # search terms than for just one
                # Need to convert from a dictionary of dataframes
                if len(d_results) > 1:                    
                    df = pandas.concat(d_results).reset_index()[['level_0', 'date', 'value', 'period']]
                    df = df.rename(columns={'level_0':'search_term'})                
                else:
                    df = pandas.DataFrame(d_results)
                return df
            elif format == 'dict':                
                return d_results
            else:
                raise ValueError("Please provide a proper format for results. Available options are: dict, dataframe.")

    def _serialize_period_values(self, df, dd_periods=None, lst_periods=None):

        """
        Converts sample into period specific list of values. Assumes dd_periods is a defaultdict

        :param df: Dataframe with sample values. Must at least have the columns [period, value]
        :param dd_periods: A dictionary, with periods as keys and lists of query results as values
        :param lst_periods: A list of valid periods
        :return: dd_periods with added values

        """

        if not lst_periods:
            lst_periods = []
        if not dd_periods:
            dd_periods = defaultdict(list)

        for index, row in df.iterrows():
            # If a list of periods was provided, we only expand dd_periods for the ones that were specified
            if len(lst_periods) > 0:
                if row['period'] in lst_periods:
                    dd_periods[row['period']].append(row['value'])
            else:
                dd_periods[row['period']].append(row['value'])

        return dd_periods

    def pull_rolling_window(self, num_samples=5):

        """
        Separates pull into a rolling set of samples to get multiple samples in the same run.
        This takes advantage of the fact that the API does not cache results if you change the length of time
        in the search

        :param num_samples: Amount of samples to pull
        :return: Dataframe with results from API.  Does not include information about the sample frame.

        """

        query_time = datetime.now()

        # First we run a single query, so we can get the dates for each period from the API.
        # Could do this logic locally, but this is easier
        local_params = deepcopy(self.params)
        local_params['search_term'] = local_params['search_term'][0]

        samples_taken = 0
        d_range_all = self.pull_data_from_api(local_params)

        lst_periods = list(d_range_all.values())[0]['period'].tolist()

        d_periods = {}

        # Next, we pull each week individually. This will always get saved.
        print("INFO: Running Search Term: {}".format(self.params['search_term']))
        for period in lst_periods:

            curr_date = datetime.strftime(period, '%Y-%m-%d')
            local_params = deepcopy(self.params)
            local_params['period_start'] = curr_date
            local_params['period_end'] = curr_date
            d_single = self.pull_data_from_api(local_params)
            if not d_single:
                raise ValueError('Problems with period {}'.format(curr_date))

            for term, result in d_single.items():
                if term in d_periods:
                    d_periods[term] = self._serialize_period_values(result, dd_periods=d_periods[term])
                else:
                    d_periods[term] = self._serialize_period_values(result, dd_periods=defaultdict(list))

        # Increment samples taken by 1 - since each period has been sampled individually
        samples_taken += 1

        # Now do the rolling sample
        # Using some logic to figure out the window size and how far back to go

        # First, we get the window size
        window_size = num_samples - samples_taken
        print("INFO: window_size: {}".format(str(window_size)))

        # If in the above samples we've already gotten all that we've asked for, no need to do the rest
        if window_size > 0:
            # There's a weird race condition in which window_size = 1, but we've already done the single period samples
            # So we just change this to a 2 period window size and they get an extra sample
            if window_size == 1:
                window_size = 2

            # Calculate days before and after, erring on the side of having more periods...
            # So that we have symmetry between sides if there are an odd number of weeks
            local_params = deepcopy(self.params)
            days_diff = window_size * 7

            # Get the starting period, specifying that the first window is window_size before the first date
            starting_period = lst_periods[0] - timedelta(days=days_diff)
            # Get the ending period, specifying that the last window is window_size after the last date
            ending_period = lst_periods[-1] + timedelta(days=days_diff)

            # Set up the loop
            # Initial window is (starting_period) to (starting_period + window_size)
            curr_start = starting_period
            curr_end = curr_start + timedelta(days=days_diff)

            # Loop until each window is done
            while curr_end <= ending_period:
                # Set up query params
                local_params['period_start'] = datetime.strftime(curr_start, '%Y-%m-%d')
                local_params['period_end'] = datetime.strftime(curr_end, '%Y-%m-%d')
                # Call the API
                d_window = self.pull_data_from_api(local_params)
                # Save the results
                for term, result in d_window.items():
                    d_periods[term] = self._serialize_period_values(
                        result,
                        dd_periods=d_periods[term],
                        lst_periods=lst_periods
                    )

                # Increment the window by one week
                curr_start += timedelta(days=7)
                curr_end += timedelta(days=7)

        rows = []
        for term, timestamps in d_periods.items():
            for timestamp, samples in timestamps.items():
                for i, sample in enumerate(samples):
                    if i < num_samples:
                        # Due to the sampling method, we sometimes draw an extra sample
                        # This will skip over that
                        rows.append({
                            "term": term,
                            "timestamp": timestamp,
                            "sample": i,
                            "value": sample,
                            "query_time": query_time
                        })

        return pandas.DataFrame(rows)
