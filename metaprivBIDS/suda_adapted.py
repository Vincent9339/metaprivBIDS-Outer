from itertools import combinations
import pandas as pd
from math import factorial
import logging
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
import time
import numpy as np

pd.options.mode.chained_assignment = None


def process_combinations(args):
    """
    Process each combination of columns by finding MSUs and computing SUDA values.

    :param args: Tuple of dataframe, column combinations, aggregation methods, and attributes count.
    :return: Updated dataframe with MSU and SUDA calculations.
    """
    dataframe, columns, i, aggregations, att, factorials = args
    groups = list(combinations(columns, i))
    return find_msu(dataframe, groups, aggregations, att, factorials)


def find_msu(dataframe, groups, aggregations, att, factorials, wildcard_value=-999):
    """
    Find and score each Minimal Sample Unique (MSU) within the dataframe for the specified groups,
    filtering out rows where more than half of the columns contain a wildcard value.

    :param dataframe: the complete dataframe of data to score.
    :param groups: an array of arrays for each group of columns to test for uniqueness.
    :param aggregations: an array of aggregation methods to use for the results.
    :param att: the total number of attributes (QIDs) in the dataset.
    :param factorials: precomputed dictionary of factorials for efficiency.
    :param wildcard_value: the value used to identify wildcards/unknown values (default is -999).
    :return: Dataframe with MSU and SUDA values computed.
    """
    
    # Filter out rows with excessive wildcard values
    total_columns = len(dataframe.columns)
    wildcard_counts = (dataframe == wildcard_value).sum(axis=1)
    threshold = total_columns / 2
    dataframe = dataframe[wildcard_counts <= threshold]

    df_updates = []

    for nple in tqdm(groups, desc="Processing groups", leave=False):
        nple = list(nple)
        cols = nple.copy()
        cols.append('fK')

        # Group by the selected columns and count occurrences
        value_counts = dataframe[nple].groupby(nple, sort=False).size()

        if 1 in value_counts.values:
            df_value_counts = pd.DataFrame(value_counts)
            df_value_counts = df_value_counts.reset_index()
            df_value_counts.columns = cols

            # Compute fM, MSU, and SUDA values
            df_value_counts['fM'] = 0
            df_value_counts['suda'] = 0
            df_value_counts.loc[df_value_counts['fK'] == 1, ['fM', 'msu', 'suda']] = \
                [1, len(nple), factorials[len(nple)]]

            # Merge results back into the main dataframe
            df_update = pd.merge(dataframe, df_value_counts, on=nple, how='left')
            df_updates.append(df_update)

    if df_updates:
        df_updates = pd.concat(df_updates)

    return df_updates


pd.set_option('display.float_format', '{:.6f}'.format)


def suda_calculation(dataframe, max_msu=2, sample_fraction=0.30, columns=None):
    """
    Calculate SUDA scores for the given dataframe.

    :param dataframe: Input dataframe for which SUDA needs to be calculated.
    :param max_msu: Maximum MSU size to consider. Default is 2.
    :param sample_fraction: Fraction of the sample to use for DIS calculation. Default is 0.30.
    :param columns: Optional list of columns to group by. If None, uses all columns.
    :return: Dataframe with SUDA and MSU values.
    """
    logger = logging.getLogger("suda")
    logging.basicConfig()

    # Start total timing
    total_start_time = time.time()

    if columns is None:
        columns = dataframe.columns.tolist()

    logger.info(f"Dataframe columns: {list(dataframe.columns)}")
    logger.info(f"Columns to group by: {columns}")

    missing_columns = [col for col in columns if col not in dataframe.columns]
    if missing_columns:
        logger.error(f"Columns not found in dataframe: {missing_columns}")
        raise ValueError(f"Columns not found in dataframe: {missing_columns}")

    dataframe = dataframe.dropna(subset=columns)

    # Convert columns to categorical where appropriate
    for col in columns:
        if dataframe[col].nunique() < 600:
            dataframe[col] = dataframe[col].astype(pd.CategoricalDtype(ordered=True))

    att = min(len(columns), 20)  # Limit the number of attributes to 20
    aggregations = {'msu': 'min', 'suda': 'sum', 'fK': 'min', 'fM': 'sum'}
    for column in dataframe.columns:
        aggregations[column] = 'max'

    # Precompute factorial values for efficiency
    factorial_start_time = time.time()
    factorials = {i: factorial(att - i) for i in range(1, max_msu + 1)}
    print(f"Factorial precomputation time: {time.time() - factorial_start_time:.2f} seconds")

    # Parallel processing with tqdm progress bar
    parallel_start_time = time.time()
    with Pool(processes=cpu_count()) as pool:
        results = list(tqdm(pool.imap_unordered(process_combinations, [
            (dataframe, columns, i, aggregations, att, factorials) for i in range(1, max_msu + 1)
        ]), total=max_msu, desc="Processing combinations"))
    print(f"Parallel processing time: {time.time() - parallel_start_time:.2f} seconds")

    results = [result for result in results if len(result) != 0]

    if not results:
        logger.info("No special uniques found")
        dataframe["suda"] = 0
        dataframe["msu"] = None
        dataframe['fK'] = None
        dataframe['fM'] = None
        print(f"Total calculation time: {time.time() - total_start_time:.2f} seconds")
        return dataframe

    # Ensure fM and SUDA columns exist and merge results
    for result in results:
        if 'fM' not in result.columns:
            result['fM'] = 0
            result['suda'] = 0

    dataframe['fM'] = 0
    dataframe['suda'] = 0

    # Concatenation with tqdm progress bar
    concat_start_time = time.time()
    results.append(dataframe)
    results = pd.concat(results).groupby(level=0).agg(aggregations)
    print(f"Concatenation and aggregation time: {time.time() - concat_start_time:.2f} seconds")

    # Vectorized DIS-SUDA calculation (with batching and progress bar)
    dis_start_time = time.time()
    tqdm.write("Calculating DIS-SUDA in batches...")

    # Calculate DIS
    value_counts = dataframe[columns].value_counts(dropna=False)
    num_unique_rows = len(value_counts[value_counts == 1])
    U = num_unique_rows

    duplicates = dataframe.duplicated(keep=False)
    P = dataframe[duplicates].shape[0]

    DIS = (U * sample_fraction) / (U * sample_fraction + P * (1 - sample_fraction))

    # Set initial DIS-SUDA to 0
    results['dis-suda'] = 0

    # Calculate the dis_value
    dis_value = DIS / results.suda.sum()

    # Apply the DIS-SUDA calculation in batches to avoid memory issues
    batch_size = 10000  # Adjust the batch size depending on your available memory
    suda_positive_index = results[results['suda'] > 0].index
    num_batches = int(np.ceil(len(suda_positive_index) / batch_size))

    # Progress bar for batching
    for i in tqdm(range(num_batches), desc="Batching DIS-SUDA calculation"):
        batch_index = suda_positive_index[i * batch_size:(i + 1) * batch_size]
        results.loc[batch_index, 'dis-suda'] = results.loc[batch_index, 'suda'] * dis_value

    print(f"DIS-SUDA calculation time: {time.time() - dis_start_time:.2f} seconds")

    # End total timing
    print(f"Total calculation time: {time.time() - total_start_time:.2f} seconds")

    return results
