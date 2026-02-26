#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Core helper to fetch job results from actinia processing API.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

import json
import re
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

import requests
from flask import make_response, request
from requests.auth import HTTPBasicAuth

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA


# ruff: noqa: PLR0912
def format_to_prefix(export_type, export_format):
    """Generate a file prefix based on the given type and format.

    see also https://github.com/actinia-org/actinia-processing-lib/blob/main/
                src/actinia_processing_lib/ephemeral_processing_with_export.py

    Args:
        export_type (str): The type of export data.
        export_format (str): The export format of the data.

    Returns:
        str: File extension corresponding to the given type and format.

    """
    prefix = ""
    if export_type == "vector":
        if export_format == "GPKG":
            prefix = ".gpkg"
        if export_format == "GML":
            prefix = ".gml"
        if export_format == "GeoJSON":
            prefix = ".json"
        if export_format == "ESRI_Shapefile":
            prefix = ""
        if export_format == "SQLite":
            prefix = ".sqlite"
        if export_format == "CSV":
            prefix = ".csv"
        # NOTE: adjust when in actinia-core vector date with only one file
        # are not zipped (equal to raster export) e.g. for single GPKG
        prefix += ".zip"
    if export_type == "raster" and (export_format in {"GTiff", "COG"}):
        prefix = ".tif"
    if export_type == "strds":
        prefix = ".tar.gz"
    if export_type == "file":
        if export_format != "PDF":
            prefix = ".zip"
        if export_format == "CSV":
            prefix = ".csv.zip"
        if export_format == "TXT":
            prefix = ".txt.zip"
    return prefix


def format_to_mimetype(export_type, export_format):
    """Determine the MIME type based on the given data type and format.

    see e.g. https://wiki.selfhtml.org/wiki/MIME-Type/%C3%9Cbersicht

    Args:
        export_type (str): The type of the export data.
        export_format (str): The export format of the data.

    Returns:
        str: The corresponding MIME type as a string.

    """
    mimetype = ""

    if export_type == "vector":
        # NOTE: adjust when in actinia-core vector date with only one file
        # are not zipped (equal to raster export) e.g. for single GPKG
        mimetype = "application/zip"
    if export_type == "raster" and (export_format in {"GTiff", "COG"}):
        mimetype = "image/tiff"
    if export_type == "strds":
        mimetype = "application/x-tar+gzip"
    if export_type == "file":
        mimetype = (
            "application/pdf" if export_format == "PDF" else "application/zip"
        )

    return mimetype


def extract_export(pc_el_inout_entry, pc_el_id, resources):
    """Extract actinia exporter results.

    Retrieve the exported filename from the provided process chain
    element entry and match it with the corresponding resource URLs.

    Args:
        pc_el_inout_entry (dict): A dictionary containing the export entry
            details, including the value, export type, and format.
        pc_el_id (str): The unique identifier for the process chain element.
        resources (list): List of all resource URLs to match against
            the export output.

    Returns:
        dict: A dictionary containing the export information:
            - "href" (str): The matched resource URL.
            - "type" (str): The MIME type of the export output.

    """
    # get value name
    if "$file::" in pc_el_inout_entry["value"]:
        # file export generated from GRASS GIS module
        # (value with $file::unique_id)
        export_value = pc_el_inout_entry["value"].split("$file::")[1]
    else:
        export_value = pc_el_inout_entry["value"]

    # get export type and format
    export_prefix = format_to_prefix(
        pc_el_inout_entry["export"]["type"],
        pc_el_inout_entry["export"]["format"],
    )
    export_out = export_value + export_prefix

    # get mimetype of output
    export_mimetype = format_to_mimetype(
        pc_el_inout_entry["export"]["type"],
        pc_el_inout_entry["export"]["format"],
    )

    # match resource url + write results formated to dict
    export_out_dict = dict()
    export_out_dict_key = (
        f"{pc_el_id}_{export_value}_{pc_el_inout_entry['export']['type']}"
        f"_{pc_el_inout_entry['export']['format']}"
    )
    match_resource_url = [url for url in resources if export_out in url]
    if match_resource_url:
        # replace user-url with base-url
        resource_url = re.sub(
            r"https?://[^/]+/api/v\d+",
            ACTINIA.user_actinia_base_url,
            match_resource_url[0],
        )
        export_out_dict[export_out_dict_key] = {
            "href": resource_url,
            "type": export_mimetype,
            # "rel": -> NOTE: can be added when a fitting rel type found
        }

    return export_out_dict


def get_results(resp):
    """Return the results of a job execution.

    Extract the results of actinia job: either exported or stdout results.

    Args:
        resp: The response object containing the job execution results.

    Returns:
        result_format (dict): A dictionary containing the formatted results
            of the job.

    """
    data = resp.json()
    resources = data["urls"]["resources"]
    result_format = dict()

    # -- Filter results from actinia
    # Exported results
    export_out_dict = None
    for pc_el in data["process_chain_list"][0]["list"]:
        # NOTE: for actinia only outputs can be exported
        # if "inputs" in pc_el:
        #     for pc_inp_el in pc_el["inputs"]:
        #         if "export" in pc_inp_el:
        #             export_out_dict = extract_export(
        #                 pc_inp_el,
        #                 pc_el["id"],
        #                 resources,
        #             )
        #             result_format.update(export_out_dict)
        if "outputs" in pc_el:
            for pc_out_el in pc_el["outputs"]:
                if "export" in pc_out_el:
                    export_out_dict = extract_export(
                        pc_out_el,
                        pc_el["id"],
                        resources,
                    )
                    result_format.update(export_out_dict)

    # Results from stdout
    stdout_dict = {}
    for pc_rel_el in data["process_results"]:
        pc_rel_data = data["process_results"][pc_rel_el]
        stdout_dict[pc_rel_el] = pc_rel_data

    result_format.update(stdout_dict)

    # NOTE: Current dict key (returned Content-ID) of result_format
    #       is a combination of pc_el_id etc.
    #       If persisent information from processing start given
    #       -> set as output defined there

    return result_format, stdout_dict, export_out_dict


def export_ref_to_header(result_format, status_code):
    """Generate a Flask response with reference links included in the header.

    Args:
        result_format (dict): A dictionary containing the formatted results
            of the job.
        status_code (int): The HTTP status code to be used in the response.

    Returns:
        Response: A Flask response object with empty body,
            the reference links included in the "Link" header
            and the specified HTTP status code.

    """
    response = make_response("", status_code)
    # format Link header, see e.g. here:
    # https://greenbytes.de/tech/webdav/rfc8288.html
    # NOTE: if needed can add 'rel' type with semicolon e.g.
    # Link: <https://example.org/>; rel="start",
    #       <https://example.org/index>; rel="index"
    links_list = [
        f"<{value['href']}>"
        for value in result_format.values()
        if "href" in value
    ]
    response.headers["Link"] = ", ".join(links_list)
    return response


def get_ref_value(value, status_code):
    """Get the value of reference link via request.

    Args:
        value (dict): A dictionary containing the reference link information,
        status_code (int): The HTTP status code to be used in the response.

    Returns:
        Response: A Flask response object containing the content retrieved from
            the reference link, with the specified HTTP status code.

    """
    auth = request.authorization
    kwargs = dict()
    if auth:
        kwargs["auth"] = HTTPBasicAuth(
            auth.username,
            auth.password,
        )
    url = re.sub(
        r"https?://[^/]+/api/v\d+",
        ACTINIA.processing_base_url,
        value["href"],
    )
    return make_response(
        requests.get(url, **kwargs).content,
        status_code,
    )


def export_ref_to_multipart(result_format, multipart_message):
    """Attach reference links as MIME parts to a multipart message.

    Args:
        result_format (dict): A dictionary containing the formatted results
            of the job.
        multipart_message (MIMEMultipart): A MIME multipart message object to
            which the reference link parts will be attached.

    """
    for key, value in result_format.items():
        if "href" in value:
            reference_part = MIMEBase("message", "external-body")
            reference_part.add_header("Content-ID", key)
            reference_part.add_header(
                "Content-Location",
                value["href"],
            )
            reference_part.set_payload(
                "This is a reference to an external resource.",
            )
            multipart_message.attach(reference_part)


def stdout_to_multipart(stdout_dict, multipart_message):
    """Convert stdout data into MIME message.

    Convert the content of a dictionary containing stdout data into MIME
    multipart message parts and attach them to the provided multipart message.

    Args:
        stdout_dict (dict): A dictionary where keys are stdout IDs (str) and
            values are the corresponding stdout content. The content can either
            be a dictionary or a list.
        multipart_message (MIMEMultipart): A MIME multipart message object to
            which the generated MIME parts will be attached.

    """
    for stdout_id, stdout_content in stdout_dict.items():
        # for different return types from actinia dependent on format, see here
        # https://github.com/actinia-org/actinia-processing-lib/blob/main/
        #   src/actinia_processing_lib/ephemeral_processing.py#L2086-L2125
        # either dict or list
        if type(stdout_content) is dict:
            part = MIMEText(json.dumps(stdout_content), "json")
        else:
            # tables to list for regular and nested lists
            data = (
                stdout_content
                if isinstance(stdout_content[0], list)
                else [[x] for x in stdout_content]
            )
            table = "\n".join(",".join(map(str, row)) for row in data)
            part = MIMEText(table, "plain")
        part.add_header("Content-ID", stdout_id)
        multipart_message.attach(part)
