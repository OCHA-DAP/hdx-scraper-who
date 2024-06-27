#!/usr/bin/python
"""
Top level script. Calls other functions that generate datasets that this
script then creates in HDX.

"""

import logging
from os.path import expanduser, join
from pathlib import Path

from hdx.api.configuration import Configuration
from hdx.data.hdxobject import HDXError
from hdx.data.showcase import Showcase
from hdx.database import Database
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


def main(
    save: bool = False,
    use_saved: bool = False,
    populate_db: bool = True,
    create_archived_datasets: bool = False,
) -> None:
    """Generate datasets and create them in HDX

    Args:
        save (bool): Save downloaded data. Defaults to True.
        use_saved (bool): Use saved data. Defaults to False.
        populate_db (bool): Populate the database. Defaults to True.
        create_archived_datasets (bool): Create archived datasets. Defaults to False.

    Returns:
        None
    """
    with wheretostart_tempdir_batch(lookup) as info:
        folder = info["folder"]
        params = {
            "dialect": "sqlite",
            "database": f"/{folder}/who_gho.sqlite",
        }
        # Remove sqlite file if re-populating
        if populate_db:
            logger.warning("Populating DB, removing sqlite file if it exists")
            Path(params["database"]).unlink(missing_ok=True)
        with Database(**params) as session:
            with Download(rate_limit={"calls": 1, "period": 1}) as downloader:
                retriever = Retrieve(
                    downloader,
                    folder,
                    "saved_data",
                    folder,
                    save,
                    use_saved,
                )
                configuration = Configuration.read()
                qc_indicators = configuration["qc_indicators"]
                quickcharts = {
                    "hashtag": "#indicator+code",
                    "values": [x["code"] for x in qc_indicators],
                    "numeric_hashtag": "#indicator+value+num",
                    "cutdown": 2,
                    "cutdownhashtags": [
                        "#indicator+code",
                        "#country+code",
                        "#date+year+end",
                        "#dimension+name",
                    ],
                }

                who = WHO(configuration, retriever, folder, session)

                who.populate_db(
                    populate_db=populate_db,
                    create_archived_datasets=create_archived_datasets,
                )
                countries = who.get_countries()

                logger.info(f"Number of countries: {len(countries)}")

                for _, country in progress_storing_folder(
                    info,
                    countries,
                    "Code",
                ):
                    process_country(
                        who,
                        country,
                        quickcharts,
                        qc_indicators,
                        info,
                        create_archived_datasets,
                    )


@retry(
    retry=(
        retry_if_exception_type(DownloadError)
        | retry_if_exception_type(HDXError)
    ),
    stop=stop_after_attempt(5),
    wait=wait_fixed(3600),
    after=after_log(logger, logging.INFO),
)
def process_country(
    who, country, quickcharts, qc_indicators, info, create_archived_datasets
):
    upload_dataset(who, country, quickcharts, qc_indicators, info)
    if create_archived_datasets:
        upload_archived_dataset(who, country, info)


def upload_dataset(who, country, quickcharts, qc_indicators, info):
    (dataset, showcase, bites_disabled) = who.generate_dataset_and_showcase(
        country, quickcharts
    )
    if not dataset:
        return

    logger.info(f"Uploading dataset for {country['Code']}")
    dataset.update_from_yaml()
    dataset.generate_quickcharts(
        -1,
        bites_disabled=bites_disabled,
        indicators=qc_indicators,
    )
    dataset.create_in_hdx(
        remove_additional_resources=True,
        match_resource_order=False,
        hxl_update=False,
        updated_by_script="HDX Scraper: WHO",
        batch=info["batch"],
    )

    if "url" in showcase.data.keys():
        showcase.create_in_hdx()
        showcase.add_dataset(dataset)
    else:
        # If the showcase has no URL, it should be deleted if it exists
        showcase = Showcase.read_from_hdx(showcase.data["name"])
        if showcase:
            showcase.delete_from_hdx()

    logger.info(f"Finished uploading dataset for {country['Code']}")


def upload_archived_dataset(who, country, info):
    archived_dataset = who.generate_archived_dataset(country)
    if not archived_dataset:
        return

    logger.info(f"Uploading archived dataset for {country['Code']}")
    archived_dataset.update_from_yaml()
    archived_dataset.create_in_hdx(
        remove_additional_resources=True,
        match_resource_order=False,
        hxl_update=False,
        updated_by_script="HDX Scraper: WHO",
        batch=info["batch"],
    )
    logger.info(f"Finished uploading archived dataset for {country['Code']}")


if __name__ == "__main__":
    facade(
        main,
        user_agent_config_yaml=join(expanduser("~"), ".useragents.yaml"),
        user_agent_lookup=lookup,
        project_config_yaml=join("config", "project_configuration.yaml"),
    )
