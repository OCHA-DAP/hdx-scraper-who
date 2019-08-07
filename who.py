#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
WHO:
------------

Reads WHO JSON and creates datasets.

"""
import logging
from collections import OrderedDict
from urllib.parse import quote_plus

from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from hdx.data.showcase import Showcase
from hdx.data.vocabulary import Vocabulary
from slugify import slugify

logger = logging.getLogger(__name__)

hxlate = '&tagger-match-all=on&tagger-01-header=gho+%28code%29&tagger-01-tag=%23indicator%2Bcode&tagger-02-header=gho+%28display%29&tagger-02-tag=%23indicator%2Bname&tagger-03-header=gho+%28url%29&tagger-03-tag=%23indicator%2Burl&tagger-05-header=datasource+%28display%29&tagger-05-tag=%23meta%2Bsource&tagger-07-header=publishstate+%28code%29&tagger-07-tag=%23status%2Bcode&tagger-08-header=publishstate+%28display%29&tagger-08-tag=%23status%2Bname&tagger-11-header=year+%28display%29&tagger-11-tag=%23date%2Byear&tagger-13-header=region+%28code%29&tagger-13-tag=%23region%2Bcode&tagger-14-header=region+%28display%29&tagger-14-tag=%23region%2Bname&tagger-16-header=country+%28code%29&tagger-16-tag=%23country%2Bcode&tagger-17-header=country+%28display%29&tagger-17-tag=%23country%2Bname&tagger-19-header=sex+%28code%29&tagger-19-tag=%23sex%2Bcode&tagger-20-header=sex+%28display%29&tagger-20-tag=%23sex%2Bname&tagger-23-header=numeric&tagger-23-tag=%23indicator%2Bvalue%2Bnum&header-row=1'


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
    indicators = list(OrderedDict.fromkeys(indicators).keys())
    tags = list(OrderedDict.fromkeys(tags).keys())
    tags, _ = Vocabulary.get_mapped_tags(tags)
    return indicators, tags


def get_countriesdata(base_url, downloader):
    response = downloader.download('%sCOUNTRY?format=json' % base_url)
    json = response.json()
    return json['dimension'][0]['code']


def generate_dataset_and_showcase(base_url, hxlproxy_url, downloader, countrydata, indicators):
    """
    http://apps.who.int/gho/athena/api/GHO/WHOSIS_000001.csv?filter=COUNTRY:BWA&profile=verbose
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
    try:
        dataset.add_country_location(countryiso)
    except HDXError as e:
        logger.exception('%s has a problem! %s' % (countryname, e))
        return None, None
    dataset.set_maintainer('196196be-6037-4488-8b71-d786adf4c081')
    dataset.set_organization('hdx')
    dataset.set_expected_update_frequency('Every year')
    dataset.set_subnational(False)
    tags = ['hxl']
    dataset.add_tags(tags)
    earliest_year = 10000
    latest_year = 0
    for indicator_code, indicator_name, indicator_url in indicators:
        no_rows = 0
        who_url = '%sGHO/%s.csv?filter=COUNTRY:%s&profile=verbose' % (base_url, indicator_code, countryiso)

        try:
            for row in downloader.get_tabular_rows(who_url, dict_rows=True, headers=1):
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
        except Exception:
            continue
        if no_rows == 0:
            continue
        url = '%surl=%s%s' % (hxlproxy_url, quote_plus(who_url), hxlate)
        resource = {
            'name': indicator_name,
            'description': '[Indicator metadata](%s)' % indicator_url,
            'format': 'csv',
            'url': url
        }
        dataset.add_update_resource(resource)
    if len(dataset.get_resources()) == 0:
        logger.exception('%s has no data!' % countryname)
        return None, None
    dataset.set_dataset_year_range(earliest_year, latest_year)

    isolower = countryiso.lower()
    showcase = Showcase({
        'name': '%s-showcase' % slugified_name,
        'title': 'Indicators for %s' % countryname,
        'notes': 'Health indicators for %s' % countryname,
        'url': 'http://www.who.int/countries/%s/en/' % isolower,
        'image_url': 'http://www.who.int/sysmedia/images/countries/%s.gif' % isolower
    })
    showcase.add_tags(tags)
    return dataset, showcase
