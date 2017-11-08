#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Top level script. Calls other functions that generate datasets that this script then creates in HDX.

"""
import logging
from os.path import join

from hdx.hdx_configuration import Configuration
from hdx.utilities.downloader import Download

from who import generate_dataset_and_showcase, get_countriesdata, get_indicators_and_tags

from hdx.facades import logging_kwargs
logging_kwargs['smtp_config_yaml'] = join('config', 'smtp_configuration.yml')

from hdx.facades.hdx_scraperwiki import facade

logger = logging.getLogger(__name__)


def main():
    """Generate dataset and create it in HDX"""

    base_url = Configuration.read()['base_url']
    with Download() as downloader:
        indicators, tags = get_indicators_and_tags(base_url, downloader, Configuration.read()['indicator_list'])
        countriesdata = get_countriesdata(base_url, downloader)
        logger.info('Number of datasets to upload: %d' % len(countriesdata))
        for countrydata in countriesdata:
            dataset, showcase = generate_dataset_and_showcase(base_url, downloader, countrydata, indicators)
            if dataset:
                 dataset.add_tags(tags)
                 dataset.update_from_yaml()
                 dataset.create_in_hdx()
                 showcase.create_in_hdx()
                 showcase.add_dataset(dataset)


if __name__ == '__main__':
    facade(main, hdx_site='feature', project_config_yaml=join('config', 'project_configuration.yml'))

