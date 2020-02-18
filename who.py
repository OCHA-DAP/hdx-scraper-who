#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
WHO:
------------

Reads WHO API and creates datasets

"""
import logging
from collections import OrderedDict
from itertools import chain

from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from hdx.data.showcase import Showcase
from hdx.data.vocabulary import Vocabulary
from hdx.utilities.dictandlist import dict_of_lists_add
from hdx.utilities.text import multiple_replace
from slugify import slugify

logger = logging.getLogger(__name__)

hxlate = '&header-row=1&tagger-match-all=on&tagger-01-header=gho+%28code%29&tagger-01-tag=%23indicator%2Bcode&tagger-02-header=gho+%28display%29&tagger-02-tag=%23indicator%2Bname&tagger-03-header=gho+%28url%29&tagger-03-tag=%23indicator%2Burl&tagger-05-header=datasource+%28display%29&tagger-05-tag=%23meta%2Bsource&tagger-07-header=publishstate+%28code%29&tagger-07-tag=%23status%2Bcode&tagger-08-header=publishstate+%28display%29&tagger-08-tag=%23status%2Bname&tagger-11-header=year+%28display%29&tagger-11-tag=%23date%2Byear&tagger-13-header=region+%28code%29&tagger-13-tag=%23region%2Bcode&tagger-14-header=region+%28display%29&tagger-14-tag=%23region%2Bname&tagger-16-header=country+%28code%29&tagger-16-tag=%23country%2Bcode&tagger-17-header=country+%28display%29&tagger-17-tag=%23country%2Bname&tagger-19-header=sex+%28code%29&tagger-19-tag=%23sex%2Bcode&tagger-20-header=sex+%28display%29&tagger-20-tag=%23sex%2Bname&tagger-23-header=numeric&tagger-23-tag=%23indicator%2Bvalue%2Bnum&filter01=sort&sort-tags01=%23indicator%2Bcode%2C%23date%2Byear%2C%23sex%2Bcode'
hxltags = {'GHO (CODE)': '#indicator+code', 'GHO (DISPLAY)': '#indicator+name', 'GHO (URL)': '#indicator+url', 'DATASOURCE (DISPLAY)': '#meta+source', 'PUBLISHSTATE (CODE)': '#status+code', 'PUBLISHSTATE (DISPLAY)': '#status+name', 'YEAR (DISPLAY)': '#date+year', 'REGION (CODE)': '#region+code', 'REGION (DISPLAY)': '#region+name', 'COUNTRY (CODE)': '#country+code', 'COUNTRY (DISPLAY)': '#country+name', 'SEX (CODE)': '#sex+code', 'SEX (DISPLAY)': '#sex+name', 'Numeric': '#indicator+value+num'}
indicator_limit = 500


def get_indicators_and_tags(base_url, downloader):
    indicators = OrderedDict()
    tags = list()
    response = downloader.download('%sapi/GHO?format=json' % base_url)
    json = response.json()
    result = json['dimension'][0]['code']

    replacements = {'(': '', ')': '', '/': ''}
    for indicator in result:
        indicator_code = indicator['label']
        if indicator_code[-9:] == '_ARCHIVED':
            continue
        category = None
        for attr in indicator['attr']:
            if attr['category'] == 'CATEGORY':
                category = attr['value']
        if category is None:
            continue
        dict_of_lists_add(indicators, category, (indicator_code, indicator['display'], indicator['url']))
        if ' and ' in category:
            tag_names = category.split(' and ')
            for tag_name in tag_names:
                tags.append(multiple_replace(tag_name.strip(), replacements))
        else:
            tags.append(multiple_replace(category.strip(), replacements))
    for category in indicators:
        indicators[category] = list(OrderedDict.fromkeys(indicators[category]).keys())
    tags = list(OrderedDict.fromkeys(tags).keys())
    tags, _ = Vocabulary.get_mapped_tags(tags)
    return indicators, tags


def get_countries(base_url, downloader):
    response = downloader.download('%sapi/COUNTRY?format=json' % base_url)
    json = response.json()
    return json['dimension'][0]['code']


def generate_dataset_and_showcase(base_url, folder, country, indicators,
                                  tags, downloadclass):
    """
    http://apps.who.int/gho/athena/api/GHO/WHOSIS_000001.csv?filter=COUNTRY:BWA&profile=verbose
    """
    countryname = country['display']
    title = '%s - Health Indicators' % countryname
    logger.info('Creating dataset: %s' % title)
    slugified_name = slugify('WHO data for %s' % countryname).lower()
    countryiso = country['label']
    for attr in country['attr']:
        if attr['category'] == 'ISO':
            countryiso = attr['value']
    cat_str = ', '.join(indicators)
    dataset = Dataset({
        'name': slugified_name,
        'notes': "Contains data from World Health Organization's [data portal](http://www.who.int/gho/en/) covering the following categories:  \n"
                 "%s  \n  \nFor links to individual indicator metadata, see resource descriptions." % cat_str,
        'title': title
    })
    try:
        dataset.add_country_location(countryiso)
    except HDXError as e:
        logger.exception('%s has a problem! %s' % (countryname, e))
        return None, None, None
    dataset.set_maintainer('35f7bb2c-4ab6-4796-8334-525b30a94c89')
    dataset.set_organization('c021f6be-3598-418e-8f7f-c7a799194dba')
    dataset.set_expected_update_frequency('Every year')
    dataset.set_subnational(False)
    alltags = ['hxl', 'indicators']
    alltags.extend(tags)
    dataset.add_tags(alltags)

    def process_row(_, row):
        if 'VOID' in row['PUBLISHSTATE (CODE)']:
            return None
        return row

    all_rows = list()
    quickcharts = {'hashtag': '#indicator+code', 'values': ['WHOSIS_000001', 'WHS7_104', 'MDG_0000000001']}
    headers = None
    bites_disabled = [True, True, True]
    for category in indicators:
        logger.info('Category: %s' % category)
        indicator_codes = list()
        indicator_links = list()
        for indicator_code, indicator_name, indicator_url in indicators[category]:
            indicator_codes.append(indicator_code)
            indicator_links.append('[%s](%s)' % (indicator_name, indicator_url))
        category_link = '*%s:*\n%s' % (category, ', '.join(indicator_links))
        filename = '%s_indicators_%s.csv' % (category, countryiso)
        resourcedata = {
            'name': '%s Indicators for %s' % (category, countryname),
            'description': category_link
        }
        indicator_list_len = len(indicator_codes)
        i = 0
        iterables = list()
        while i < indicator_list_len:
            ie = min(i + indicator_limit, indicator_list_len)
            url = '%sdata/data-verbose.csv?target=GHO/%s&filter=COUNTRY:%s&profile=verbose' % (
                base_url, ','.join(indicator_codes[i:ie]), countryiso)
            fileheaders, iterator = downloadclass().get_tabular_rows(url, dict_form=True, row_function=process_row, format='csv')
            iterables.append(iterator)
            i += indicator_limit
        success, results = dataset.generate_resource_from_download(
            fileheaders, chain.from_iterable(iterables), hxltags, folder, filename, resourcedata, yearcol='YEAR (CODE)',
            quickcharts=quickcharts)
        if success is True:
            if len(all_rows) == 0:
                headers = fileheaders
                all_rows.extend(results['rows'])
            else:
                all_rows.extend(results['rows'][1:])
            for i, bite_disabled in enumerate(results['bites_disabled']):
                if bite_disabled is False:
                    bites_disabled[i] = False

    filename = 'health_indicators_%s.csv' % countryiso
    resourcedata = {
        'name': 'All Health Indicators for %s' % countryname,
        'description': 'See resource descriptions below for links to indicator metadata'
    }
    dataset.generate_resource_from_rows(folder, filename, all_rows, resourcedata, headers)

    resources = dataset.get_resources()
    resources.insert(0, resources.pop())

    isolower = countryiso.lower()
    showcase = Showcase({
        'name': '%s-showcase' % slugified_name,
        'title': 'Indicators for %s' % countryname,
        'notes': 'Health indicators for %s' % countryname,
        'url': 'http://www.who.int/countries/%s/en/' % isolower,
        'image_url': 'http://www.who.int/sysmedia/images/countries/%s.gif' % isolower
    })
    showcase.add_tags(alltags)
    return dataset, showcase, bites_disabled
