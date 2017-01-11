'''
Created on Jan 10, 2017

from https://github.com/nchah/github-traffic-stats.git

'''
import csv
from collections import OrderedDict
import datetime
import string

def json_to_table(repo, period, json_response, fieldName='clones'):
    """Parse traffic stats in JSON and format into a table
    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :return: table: str - for printing on command line
    """
    repo_name = repo[:-4] if repo.endswith('.git') else repo
    total_views = str(json_response['count'])
    total_uniques = str(json_response['uniques'])

    dates_and_views = OrderedDict()
    detailed_views = json_response[fieldName]
    fieldDisplayName = string.capwords(fieldName)
    for row in detailed_views:
        # utc_date = timestamp_to_utc(int(row['timestamp']))
        utc_date = str(row['timestamp'][0:10])
        dates_and_views[utc_date] = (period, str(row['count']), str(row['uniques']))

    """Table template
    repo_name
    Date        Views   Unique visitors
    Totals      #       #
    date        #       #
    ...         ...     ...
    """
    table_alt = repo_name + '\n' +\
            '# Total ' + fieldDisplayName + ':\t' + total_views + '\n' + '# Total Unique:' + '\t' + total_uniques + '\n' +\
            'Date' + '\t\t' + fieldDisplayName + '\t' + 'Unique ' + fieldDisplayName + '\n'

    table = repo_name + '\n' +\
            'Date' + '\t\t' + 'period' + '\t' + fieldDisplayName + '\t' + 'Unique ' + fieldDisplayName + '\n' +\
            'Totals' + '\t\t\t' + total_views + '\t' + total_uniques + '\n'
    for row in dates_and_views:
        table += row + '\t' + dates_and_views[row][0] + '\t' + dates_and_views[row][1] + '\t' + dates_and_views[row][2] + '\n'

    return table


def store_csv(csv_file_name, repo, period, json_response, fieldName='clones'):
    """Store the traffic stats as a CSV, with schema:
    repo_name, date, views, unique_visitors

    :param repo: str - the GitHub repository name
    :param json_response: json - the json input
    :return:
    """
    repo_name = repo[:-4] if repo.endswith('.git') else repo
    # # Not writing Totals stats into the CSV to maintain normalization
    # total_views = str(json_response['count'])
    # total_uniques = str(json_response['uniques'])

    dates_and_views = OrderedDict()
    detailed_views = json_response[fieldName]
    fieldDisplayName = string.capwords(fieldName)
    for row in detailed_views:
        # utc_date = timestamp_to_utc(int(row['timestamp']))
        utc_date = str(row['timestamp'][0:10])
        dates_and_views[utc_date] = (period, str(row['count']), str(row['uniques']))

    # Starting up the CSV, writing the headers in a first pass
    # Check if existing CSV
    delimiter = '\t'
    quotechar = '"'
    try:
        csv_file = open(csv_file_name).readlines()
        if csv_file:
            for i in dates_and_views:
                row = [repo_name, i, dates_and_views[i][0], dates_and_views[i][1], dates_and_views[i][2]]
                with open(csv_file_name, 'a') as csvfile:
                    csv_writer = csv.writer(csvfile, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
                    csv_writer.writerow(row)
    except IOError:
        headers = ['repository_name', 'date', 'period', fieldName, 'unique ' + fieldName]
        with open(csv_file_name, 'a') as csvfile:
            csv_writer = csv.writer(csvfile, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(headers)

        for i in dates_and_views:
            row = [repo_name, i, dates_and_views[i][0], dates_and_views[i][1], dates_and_views[i][2]]
            with open(csv_file_name, 'a') as csvfile:
                csv_writer = csv.writer(csvfile, delimiter=delimiter, quotechar=quotechar, quoting=csv.QUOTE_MINIMAL)
                csv_writer.writerow(row)

    return ''
