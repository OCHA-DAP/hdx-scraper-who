#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this
script then creates in HDX.

"""
import logging
from os.path import expanduser, join

from hdx.api.configuration import Configuration
from hdx.data.hdxobject import HDXError
from hdx.facades.infer_arguments import facade
from hdx.utilities.downloader import Download, DownloadError
from hdx.utilities.path import (
    progress_storing_folder,
    wheretostart_tempdir_batch,
)
from hdx.utilities.retriever import Retrieve
from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)

from who import WHO

logger = logging.getLogger(__name__)

lookup = "hdx-scraper-who"


def main(save: bool = True, use_saved: bool = False) -> None:
    """Generate datasets and create them in HDX

    Args:
        save (bool): Save downloaded data. Defaults to False.
        use_saved (bool): Use saved data. Defaults to False.

    Returns:
        None
    """
    with wheretostart_tempdir_batch(lookup) as info:
        folder = info["folder"]
        with Download(rate_limit={"calls": 1, "period": 1}) as downloader:
            retriever = Retrieve(
                downloader, folder, "saved_data", folder, save, use_saved
            )
            configuration = Configuration.read()
            qc_indicators = configuration["qc_indicators"]
            who = WHO(configuration, retriever, folder)

            # countries = who.get_countries()
            # TODO: remove
            countries = who.get_countries()[1:2]
            logger.info(f"Number of datasets to upload: {len(countries)}")

            @retry(
                retry=(
                    retry_if_exception_type(DownloadError)
                    | retry_if_exception_type(HDXError)
                ),
                stop=stop_after_attempt(5),
                wait=wait_fixed(3600),
                after=after_log(logger, logging.INFO),
            )
            def process_country(country):
                quickcharts = {
                    "hashtag": "#indicator+code",
                    "values": [x["code"] for x in qc_indicators],
                    "numeric_hashtag": "#indicator+value+num",
                    "cutdown": 2,
                    "cutdownhashtags": [
                        "#indicator+code",
                        "#country+code",
                        "#date+year+end",
                        "#dimension+code",
                    ],
                }
                (dataset, showcase, bites_disabled) = (
                    who.generate_dataset_and_showcase(country, quickcharts)
                )

                if dataset:
                    dataset.update_from_yaml()
                    dataset.generate_quickcharts(
                        -1,
                        bites_disabled=bites_disabled,
                        indicators=qc_indicators,
                    )
                    # paths = [
                    #   x.get_file_to_upload() for x in dataset.get_resources()
                    # ]
                    dataset.create_in_hdx(
                        remove_additional_resources=True,
                        match_resource_order=False,
                        hxl_update=False,
                        updated_by_script="HDX Scraper: WHO",
                        batch=info["batch"],
                    )
                    showcase.create_in_hdx()
                    showcase.add_dataset(dataset)

                    # TODO: still needed?
                    # for path in paths:
                    #    try:  # Needed while there are duplicate categories
                    #        remove(path)
                    #    except OSError:
                    #        pass

            for _, country in progress_storing_folder(
                info, countries, "Code", "AFG"
            ):
                process_country(country)


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yml"),
        user_agent_lookup=lookup,
        project_config_yaml=join("config", "project_configuration.yml"),
    )
