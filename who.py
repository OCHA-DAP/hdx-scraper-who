#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
WHO:
------------

Reads WHO JSON and creates datasets.

"""
import logging
from collections import OrderedDict
from os.path import join

from hdx.data.dataset import Dataset
from hdx.data.hdxobject import HDXError
from hdx.data.resource import Resource
from hdx.data.resource_view import ResourceView
from hdx.data.showcase import Showcase
from hdx.data.vocabulary import Vocabulary
from hdx.utilities.dictandlist import write_list_to_csv
from slugify import slugify

logger = logging.getLogger(__name__)

hxlate = '&header-row=1&tagger-match-all=on&tagger-01-header=gho+%28code%29&tagger-01-tag=%23indicator%2Bcode&tagger-02-header=gho+%28display%29&tagger-02-tag=%23indicator%2Bname&tagger-03-header=gho+%28url%29&tagger-03-tag=%23indicator%2Burl&tagger-05-header=datasource+%28display%29&tagger-05-tag=%23meta%2Bsource&tagger-07-header=publishstate+%28code%29&tagger-07-tag=%23status%2Bcode&tagger-08-header=publishstate+%28display%29&tagger-08-tag=%23status%2Bname&tagger-11-header=year+%28display%29&tagger-11-tag=%23date%2Byear&tagger-13-header=region+%28code%29&tagger-13-tag=%23region%2Bcode&tagger-14-header=region+%28display%29&tagger-14-tag=%23region%2Bname&tagger-16-header=country+%28code%29&tagger-16-tag=%23country%2Bcode&tagger-17-header=country+%28display%29&tagger-17-tag=%23country%2Bname&tagger-19-header=sex+%28code%29&tagger-19-tag=%23sex%2Bcode&tagger-20-header=sex+%28display%29&tagger-20-tag=%23sex%2Bname&tagger-23-header=numeric&tagger-23-tag=%23indicator%2Bvalue%2Bnum&filter01=sort&sort-tags01=%23indicator%2Bcode%2C%23date%2Byear%2C%23sex%2Bcode'
resource_name = 'Health Indicators for %s'
hxltags = {'GHO (CODE)': '#indicator+code', 'GHO (DISPLAY)': '#indicator+name', 'GHO (URL)': '#indicator+url', 'DATASOURCE (DISPLAY)': '#meta+source', 'PUBLISHSTATE (CODE)': '#status+code', 'PUBLISHSTATE (DISPLAY)': '#status+name', 'YEAR (DISPLAY)': '#date+year', 'REGION (CODE)': '#region+code', 'REGION (DISPLAY)': '#region+name', 'COUNTRY (CODE)': '#country+code', 'COUNTRY (DISPLAY)': '#country+name', 'SEX (CODE)': '#sex+code', 'SEX (DISPLAY)': '#sex+name', 'Numeric': '#indicator+value+num'}


def get_indicators_and_tags(base_url, downloader, indicator_list):
    indicators = list()
    tags = list()
    response = downloader.download('%sapi/GHO?format=json' % base_url)
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


def get_countries(base_url, downloader):
    response = downloader.download('%sapi/COUNTRY?format=json' % base_url)
    json = response.json()
    return json['dimension'][0]['code']


def generate_dataset_and_showcase(base_url, downloader, folder, country, indicators):
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
    description = "Contains data from World Health Organization's [data portal](http://www.who.int/gho/en/) covering the following indicators:  \n%s"
    indicator_links = list()
    for _, indicator_name, indicator_url in indicators:
        indicator_links.append('[%s](%s)' % (indicator_name, indicator_url))
    dataset = Dataset({
        'name': slugified_name,
        'notes': description % (', '.join(indicator_links)),
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
    tags = ['hxl', 'indicators']
    dataset.add_tags(tags)
    years = set()
    who_url = '%sdata/data-verbose.csv?target=GHO/%s&filter=COUNTRY:%s&profile=verbose' % (base_url, ','.join([x[0] for x in indicators]), countryiso)
    no_rows = 0
    headers, iterator = downloader.get_tabular_rows(who_url, headers=1, dict_form=True, format='csv')
    rows = [downloader.hxl_row(headers, hxltags, dict_form=True)]
    for row in iterator:
        no_rows += 1
        rows.append(row)
        year = row['YEAR (CODE)']
        if year:
            if '-' in year:
                yearrange = year.split('-')
                years.add(int(yearrange[0]))
                years.add(int(yearrange[1]))
            else:
                years.add(int(year))
    if no_rows == 0:
        logger.error('Could not download data for %s!' % countryname)
        return None, None
    filepath = join(folder, 'health_indicators_%s.csv' % countryiso)
    resourcedata = {
        'name': resource_name % countryname,
        'description': 'See dataset description for links to indicator metadata'
    }
    write_list_to_csv(filepath, rows, headers=headers)
    resource = Resource(resourcedata)
    resource.set_file_type('csv')
    resource.set_file_to_upload(filepath)
    dataset.add_update_resource(resource)

    years = sorted(list(years))
    dataset.set_dataset_year_range(years[0], years[-1])

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
