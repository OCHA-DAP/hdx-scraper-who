#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
WHO:
------------

Reads WHO JSON and creates datasets.

"""
import logging

from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from slugify import slugify
from tabulator.exceptions import TabulatorException

logger = logging.getLogger(__name__)


def get_indicators_and_tags(base_url, downloader, indicator_list):
    indicators = list()
    tags = list()
    response = downloader.download('%sGHO?format=json' % base_url)
    json = response.json()
    result = json['dimension'][0]['code']

    def clean_tag(tag):
        tag = tag.replace('(', '')
        tag = tag.replace(')', '')
        tag = tag.replace('/', ' ')
        return tag

    for indicator in result:
        indicator_code = indicator['label']
        if indicator_code in indicator_list:
            indicators.append((indicator_code, indicator['display'], indicator['url']))
            for attr in indicator['attr']:
                if attr['category'] == 'CATEGORY':
                    tag_name = attr['value']
                    if ' and ' in tag_name:
                        tag_names = tag_name.split(' and ')
                        for tag_name in tag_names:
                            tags.append(clean_tag(tag_name.strip()))
                    else:
                        tags.append(clean_tag(tag_name.strip()))
    return indicators, tags


def get_countriesdata(base_url, downloader):
    response = downloader.download('%sCOUNTRY?format=json' % base_url)
    json = response.json()
    return json['dimension'][0]['code']


def generate_dataset(base_url, streamcls, countrydata, indicators):
    """
    # http://apps.who.int/gho/athena/api/GHO/WHOSIS_000001.csv?filter=COUNTRY:BWA&profile=verbose
    """
    countryname = countrydata['display']
    title = '%s - Health Indicators' % countryname
    logger.info('Creating dataset: %s' % title)
    slugified_name = slugify('WHO data for %s' % countryname).lower()
    countryiso = countrydata['label']
    for attr in countrydata['attr']:
        if attr['category'] == 'ISO':
            countryiso = attr['value']
    dataset = Dataset({
        'name': slugified_name,
        'title': title,
    })
    dataset.set_maintainer('196196be-6037-4488-8b71-d786adf4c081')
    dataset.set_organization('hdx')
    dataset.set_expected_update_frequency('Every year')
    try:
        dataset.add_country_location(countryiso)
    except HDXError as e:
        logger.exception('%s has a problem! %s' % (countryname, e))
        return None
    dataset.add_tags(['indicators', 'World Health Organization'])

    earliest_year = 10000
    latest_year = 0
    for indicator_code, indicator_name, indicator_url in indicators:
        no_rows = 0
        url = '%sGHO/%s.csv?filter=COUNTRY:%s&profile=verbose' % (base_url, indicator_code, countryiso)
        try:
            stream = streamcls(url, headers=1)
            stream.open()
            for row in stream.iter(keyed=True):
                no_rows += 1
                year = row['YEAR (CODE)']
                if '-' in year:
                    years = year.split('-')
                else:
                    years = [year]
                for year in years:
                    year = int(year)
                    if year < earliest_year:
                        earliest_year = year
                    if year > latest_year:
                        latest_year = year
            stream.close()
        except TabulatorException:
            continue
        if no_rows == 0:
            continue
        resource = {
            'name': indicator_name,
            'description': '[Indicator metadata](%s)' % indicator_url,
            'format': 'csv',
            'url': url
        }
        dataset.add_update_resource(resource)
    if len(dataset.get_resources()) == 0:
        return None
    dataset.set_dataset_year_range(earliest_year, latest_year)
    return dataset
