# Search Sampler

This is a package for collecting and analyzing Google Health API data using a large, rolling sample, which can be beneficial when making precise calculations. Instead of taking just one sample of all data points, this package gives users the option of retrieving several samples for each data point, which can later be computed as a single data point. It is a modified version of the script researchers used to collect data for Pew Research Center's [report](http://www.journalism.org/essay/searching-for-news/) on the Flint water crisis, published on April 27, 2017. For more information on using this tool, see [this post](https://medium.com/pew-research-center-decoded/sharing-the-code-we-used-to-study-the-publics-interest-in-the-flint-water-crisis-66215382b194).

## About the Report

This repository contains a generalized version of code used for collecting and analyzing data from the Google Health API for Pew Research Center's project, "[Searching for News: The Flint Water Crisis](http://www.journalism.org/essay/searching-for-news/)", published on April 27, 2017.

The project explored what aggregated search behavior can tell us about how news spreads and how public attention shifts in today's fractured information environment, using the water crisis in Flint, Michigan, as a case study.

The study delves into the kinds of searches that were most prevalent as a proxy for public interest, concerns and intentions about the crisis, and tracks the way search activity ebbed and flowed alongside real world events and their associated news coverage.

Researchers collected the data via Google's Health API, to which the Center requested and gained special access for this project. For more information, read our [Medium post](https://medium.com/@pewresearch/using-google-trends-data-for-research-here-are-6-questions-to-ask-a7097f5fb526) on how we used Google Trends data to conduct our research. Note that this requires access to the Health API; to apply, click [here](https://docs.google.com/forms/d/e/1FAIpQLSdZbYbCeULxWAFHsMRgKQ6Q1aFvOwLauVF8kuk5W_HOTrSq2A/viewform?visit_id=1-636281495024829628-2992692443&amp;rd=1).

## Requirements

- Python 2.7.x
- See [requirements.txt](https://github.com/pewresearch/search_sampler/blob/master/requirements.txt) for required pip packages.

## Installation

Install via pip:

    pip install search_sampler

## Instructions

**NOTE:** Use of this tool requires an API key from Google, with special access for the Health API. To request access, please contact the Google News Lab via this [form](https://docs.google.com/forms/d/e/1FAIpQLSdZbYbCeULxWAFHsMRgKQ6Q1aFvOwLauVF8kuk5W_HOTrSq2A/viewform?visit_id=1-636281495024829628-2992692443&amp;rd=1).

### Initialization

To use this tool, initialize the class with the API Key and a set of search parameters, which include the search term, region, start and end of the search period, and the unit of time to search for (day, week, month). Every search also requires a name (search_name), which is used as a suffix to output files. Using the same search_name multiple times can let you concatenate new results to existing output when you call the save function.

Search parameters should be passed as a dictionary. For example:

    apikey = ''

    output_path = '' # Folder name in your current directory to save results. This will be created.

    # search params
    params = {
        # Can be any number of search terms, using boolean logic. See report methodology for more info.
        'search_term':['cough'],

        # Can be country, state, or DMA. States are US-CA. DMA are a 3 digit code; see Nielsen for info.
        'region':'US-DC',

        # Must be in format YYYY-MM-DD
        'period_start':'2014-01-01',
        'period_end':'2014-02-15',

        # Options are day, week, month. WARNING: This has been extensively tested with week only.
        'period_length':'week'
    }

    sample = SearchSampler(apikey, search_name, params, output_path=output_path)

### Getting Data

This package provides either a single sample of data or a set of rolling window samples (see [Medium post](https://medium.com/@pewresearch/using-google-trends-data-for-research-here-are-6-questions-to-ask-a7097f5fb526) for details).

To retrieve a single sample:

    df_results = sample.pull_data_from_api()

To retrieve a rolling set of samples:

    df_results = sample.pull_rolling_window(num_samples=num_samples)

### Saving Results

To save results, run the built-in save command:

    sample.save_file(df_results)

SearchSampler also allows you to run the same search multiple times. When done on different days, the Health API returns a slightly different sample, giving you more observations and increasing your analytical power (see this [Medium post](https://medium.com/@pewresearch/using-google-trends-data-for-research-here-are-6-questions-to-ask-a7097f5fb526) for more information). These new results can then be appended to any previously saved results by adding the append parameter to save\_file. If append is not set to True, existing results will be overwritten.

    sample.save_file(df_results, append=True)

### Output

The results are saved in a CSV format in the folder in the output path/region specified. The file name reflects the region and the specified search name. For example, if the output path is 'data', the region is 'US-CA', and the search name is 'flu', the file will be found in 'data/US-CA/US-CA-flu.csv.' This file can be opened by spreadsheet programs like Microsoft Excel and a range of statistical and computational tools. Note that if opened in Excel, the date fields may not be recognized, but this should not be a problem in statistical or computational tools, such as R or Python's pandas. Fields in the output file are:

- **query_time**: time query was run
- **sample**: the number of this individual sample. Zero-indexed.
- **term**: the list of terms searched on
- **timestamp**: the specific period being searched
- **value**: the value from the Health API

## Methodological Note

This project, the first foray by the Center into the Google Health API, was as much an exploration of how analyses of search data can shed light on the public's response to news and events as it was a study of the Flint water crisis. The detailed [methodology](http://www.journalism.org/2017/04/27/google-flint-methodology/) is an effort to openly share what we learned through this process.

## Acknowledgments

This report was made possible by The Pew Charitable Trusts. Pew Research Center is a subsidiary of The Pew Charitable Trusts, its primary funder. This report is a collaborative effort based on the input and analysis of [a number of individuals and experts at Pew Research Center](http://www.journalism.org/2017/04/27/google-flint-acknowledgments/). Google's data experts provided valuable input during the course of the project, from assistance in understanding the structure of the data to consultation on methodological decisions. While the analysis was guided by our consultations with the advisers, Pew Research Center is solely responsible for the interpretation and reporting of the data.

## Use Policy

In addition to the [license](https://github.com/pewresearch/search_sampler/blob/master/LICENSE), Users must abide by the following conditions:

- User may not use the Center's logo
- User may not use the Center's name in any advertising, marketing or promotional materials.
- User may not use the licensed materials in any manner that implies, suggests, or could otherwise be perceived as attributing a particular policy or lobbying objective or opinion to the Center, or as a Center endorsement of a cause, candidate, issue, party, product, business, organization, religion or viewpoint.

### Recommended Report Citation

Pew Research Center, April, 2017, "Searching for News: The Flint Water Crisis"
 
### Recommended Package Citation

Pew Research Center, September 2018, "Search Sampler" Available at: github.com/pewresearch/search_sampler

### Related Pew Research Center Publications

- September 13, 2018 "[Sharing the code we used to study the public's interest in the Flint water crisis](https://medium.com/pew-research-center-decoded/sharing-the-code-we-used-to-study-the-publics-interest-in-the-flint-water-crisis-66215382b194)"

- April 27, 2017  "[Searching for News: The Flint Water Crisis](http://www.journalism.org/essay/searching-for-news/)"

- April 27, 2017  "[Using Google Trends data for research? Here are 6 questions to ask](https://medium.com/@pewresearch/using-google-trends-data-for-research-here-are-6-questions-to-ask-a7097f5fb526)"

- April 27, 2017  "[Q&A: Using Google search data to study public interest in the Flint water crisis](http://www.pewresearch.org/fact-tank/2017/04/27/flint-water-crisis-study-qa/)"

## Issues and Pull Requests

This code is provided as-is for use in your own projects.  You are free to submit issues and pull requests with any questions or suggestions you may have. We will do our best to respond within a 30-day time period.

# About Pew Research Center

Pew Research Center is a nonpartisan fact tank that informs the public about the issues, attitudes and trends shaping the world. It does not take policy positions. The Center conducts public opinion polling, demographic research, content analysis and other data-driven social science research. It studies U.S. politics and policy; journalism and media; internet, science and technology; religion and public life; Hispanic trends; global attitudes and trends; and U.S. social and demographic trends. All of the Center's reports are available at [www.pewresearch.org](http://www.pewresearch.org). Pew Research Center is a subsidiary of The Pew Charitable Trusts, its primary funder.

## Contact

For all inquiries, please email info@pewresearch.org. Please be sure to specify your deadline, and we will get back to you as soon as possible. This email account is monitored regularly by Pew Research Center Communications staff.
