#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Top level script. Calls other functions that generate datasets that this script then creates in HDX.

"""
import logging
from os.path import join, expanduser

from hdx.hdx_configuration import Configuration
from hdx.utilities.downloader import Download
from hdx.utilities.path import progress_storing_tempdir

from who import generate_dataset_and_showcase, get_countries, get_indicators_and_tags

from hdx.facades.simple import facade

logger = logging.getLogger(__name__)

lookup = 'hdx-scraper-who'


def main():
    """Generate dataset and create it in HDX"""

    configuration = Configuration.read()
    base_url = configuration['base_url']
    with Download() as downloader:
        indicators, tags = get_indicators_and_tags(base_url, downloader)
        countries = get_countries(base_url, downloader)
        logger.info('Number of datasets to upload: %d' % len(countries))
        for folder, country in progress_storing_tempdir('WHO', countries, 'label'):
            dataset, showcase, bites_disabled = generate_dataset_and_showcase(
                base_url, folder, country, indicators, tags, downloadclass=Download)
            if dataset:
                dataset.update_from_yaml()
                dataset.generate_resource_view(-1, bites_disabled=bites_disabled)
                dataset.create_in_hdx(remove_additional_resources=True, hxl_update=False, updated_by_script='HDX Scraper: WHO')
                showcase.create_in_hdx()
                showcase.add_dataset(dataset)


if __name__ == '__main__':
    facade(main, hdx_site='test', user_agent_config_yaml=join(expanduser('~'), '.useragents.yml'), user_agent_lookup=lookup, project_config_yaml=join('config', 'project_configuration.yml'))

