from itertools import combinations
import pandas as pd
from math import factorial
import logging
from tqdm import tqdm
from math import factorial
from multiprocessing import Pool, cpu_count
pd.options.mode.chained_assignment = None


def process_combinations(args):
    dataframe, columns, i, aggregations, att = args
    groups = list(combinations(columns, i))
    return find_msu(dataframe, groups, aggregations, att)

def find_msu(dataframe, groups, aggregations, att, wildcard_value=-999):
    """
    Find and score each Minimal Sample Unique (MSU) within the dataframe
    for the specified groups, filtering out rows where more than one third 
    of the columns contain a wildcard value.
    
    :param dataframe: the complete dataframe of data to score
    :param groups: an array of arrays for each group of columns to test for uniqueness
    :param aggregations: an array of aggregation methods to use for the results
    :param att: the total number of attributes (QIDs) in the dataset
    :param wildcard_value: the value used to identify wildcards/unknown values (e.g., -999)
    :return: dataframe with MSU and SUDA values computed

    Copyright © 2021 Jisc (https://jisc.ac.uk)

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:
    
    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.
    """
    
    # Wildcard row removal logic 
    # Count the total number of columns
    total_columns = len(dataframe.columns)
    
    # Count the number of wildcard values in each row
    wildcard_counts = (dataframe == wildcard_value).sum(axis=1)
    
    # Determine the threshold (more than one third of the total columns)
    threshold = total_columns / 2
    
    # Filter out rows where the number of wildcards exceeds the threshold
    dataframe = dataframe[wildcard_counts <= threshold]
    
    # --- MSU calculation ---
    df_copy = dataframe.copy()
    
    # Prepare to store updates
    df_updates = []
    
    # Iterate through each group (subset of columns)
    for nple in groups:
        nple = list(nple)
        cols = nple.copy()
        
        # Calculate the unique value counts (fK)
        cols.append('fK')
        value_counts = df_copy[nple].groupby(nple, sort=False).size()

        if 1 in value_counts.values:
            df_value_counts = pd.DataFrame(value_counts)
            df_value_counts = df_value_counts.reset_index()
            # Change the column names
            df_value_counts.columns = cols

            # Add values for fM, MSU, and SUDA
            df_value_counts['fM'] = 0
            df_value_counts['suda'] = 0
            df_value_counts.loc[df_value_counts['fK'] == 1, ['fM', 'msu', 'suda']] = \
                [1, len(nple), factorial(att - len(nple))]

            # Merge results back into the main dataframe
            df_update = pd.merge(df_copy, df_value_counts, on=nple, how='left')
            df_updates.append(df_update)

    # Return the concatenated result
    if len(df_updates) > 0:
        df_updates = pd.concat(df_updates)
    
    return df_updates

pd.set_option('display.float_format', '{:.6f}'.format)

def suda_calculation(dataframe, max_msu=2, dis=0.1, columns=None):
    """
    Special Uniqueness Detection Algorithm (SUDA)
    :param dataframe:
    :param max_msu:
    :param dis:
    :param columns: the set of columns to apply SUDA to. Defaults to None (all columns)
    :return:
    """
    logger = logging.getLogger("suda")
    logging.basicConfig()

    # Get the set of columns
    if columns is None:
        columns = dataframe.columns

    for col in columns:
        if dataframe[col].nunique() < 600:
            # Use .loc to avoid SettingWithCopyWarning
            dataframe.loc[:, col] = dataframe[col].astype(pd.CategoricalDtype(ordered=True))

    att = len(columns)
    if att > 20:
        logger.warning("More than 20 columns presented; setting ATT to max of 20")
        att = 20

    # Construct the aggregation array
    aggregations = {'msu': 'min', 'suda': 'sum', 'fK': 'min', 'fM': 'sum'}
    for column in dataframe.columns:
        aggregations[column] = 'max'

    # Use multiprocessing to parallelize the processing of combinations
    results = []
    with Pool(processes=cpu_count()) as pool:
        # Pass all necessary arguments to the process_combinations function
        results = pool.map(process_combinations, [(dataframe, columns, i, aggregations, att) for i in range(1, max_msu + 1)])

    # Filter out empty results
    results = [result for result in results if len(result) != 0]

    if len(results) == 0:
        logger.info("No special uniques found")
        dataframe["suda"] = 0
        dataframe["msu"] = None
        dataframe['fK'] = None
        dataframe['fM'] = None
        return dataframe

    # Domain completion
    for result in results:
        if 'fM' not in result.columns:
            result['fM'] = 0
            result['suda'] = 0
    dataframe.loc[:, 'fM'] = 0
    dataframe['suda'] = 0

    # Concatenate all results
    results.append(dataframe)
    results = pd.concat(results).groupby(level=0).agg(aggregations)

    results['dis-suda'] = 0
    dis_value = dis / results.suda.sum()

    results.loc[dataframe['suda'] > 0, 'dis-suda'] = results.suda * dis_value
    results['dis-suda'] = results.suda * dis_value
    
   
    return results
