#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this script then creates in HDX.

"""
import logging
from os.path import expanduser, join
from time import sleep

from hdx.facades.simple import facade
from hdx.hdx_configuration import Configuration
from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.path import progress_storing_tempdir

from who import generate_dataset_and_showcase, get_countries, get_indicators_and_tags

logger = logging.getLogger(__name__)

lookup = "hdx-scraper-who"


def main():
    """Generate dataset and create it in HDX"""

    configuration = Configuration.read()
    base_url = configuration["base_url"]
    qc_indicators = configuration["qc_indicators"]
    with Download(rate_limit={"calls": 1, "period": 1}) as downloader:
        indicators, tags = get_indicators_and_tags(base_url, downloader)
        countries = get_countries(base_url, downloader)
        logger.info(f"Number of datasets to upload: {len(countries)}")
        tries = 0
        ex = None
        cur_country = None
        prev_country = None
        while tries < 5:
            ex = None
            try:
                for info, country in progress_storing_tempdir(
                    "WHO", countries, "label"
                ):
                    cur_country = country
                    dataset, showcase, bites_disabled = generate_dataset_and_showcase(
                        base_url,
                        info["folder"],
                        country,
                        indicators,
                        tags,
                        qc_indicators,
                        downloadclass=Download,
                    )
                    if dataset:
                        dataset.update_from_yaml()
                        dataset.generate_resource_view(
                            -1, bites_disabled=bites_disabled, indicators=qc_indicators
                        )
                        dataset.create_in_hdx(
                            remove_additional_resources=True,
                            hxl_update=False,
                            updated_by_script="HDX Scraper: WHO",
                            batch=info["batch"],
                        )
                        showcase.create_in_hdx()
                        showcase.add_dataset(dataset)
                break
            except DownloadError as ex:
                if cur_country == prev_country:
                    raise
                prev_country = cur_country
                tries += 1
                logger.warning(
                    f"Download failed! Trying again in an hour. Try = {tries}"
                )
                sleep(3600)
        if ex is not None:
            raise


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yml"),
        user_agent_lookup=lookup,
        project_config_yaml=join("config", "project_configuration.yml"),
    )
