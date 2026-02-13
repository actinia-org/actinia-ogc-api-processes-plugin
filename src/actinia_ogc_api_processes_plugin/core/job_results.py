#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Core helper to fetch job results from actinia processing API.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify

def format_to_prefix(type, format):
    """
    Generate a file prefix based on the given type and format.

    This function maps a combination of data type and format to a specific file
    prefix or extension. The mapping is based on predefined rules for vector,
    raster, strds, and file types
    (see also https://github.com/actinia-org/actinia-processing-lib/blob/main/src/actinia_processing_lib/ephemeral_processing_with_export.py).

    Args:
        type (str): The type of data. Supported values are:
        format (str): The format of the data. Supported values depend on the type:

    Returns:
        str: The file prefix or extension corresponding to the given type and format.
    """
    prefix = ""
    if type == "vector":
        if format == "GPKG":
            prefix = ".gpkg"
        if format == "GML":
            prefix = ".gml"
        if format == "GeoJSON":
            prefix = ".json"
        if format == "ESRI_Shapefile":
            prefix = ""
        if format == "SQLite":
            prefix = ".sqlite"
        if format == "CSV":
            prefix = ".csv"
        prefix += ".zip"
    if type == "raster":
        if format == "GTiff" or format == "COG":
            prefix = ".tif"
    if type == "strds":            
        prefix = ".tar.gz"
    if type == "file":
        if format != "PDF":
           prefix = ".zip"
        if format == "CSV":
            prefix = ".csv.zip"
        if format == "TXT":
            prefix = ".txt.zip"
    return prefix

def format_to_mimetype(type, format):
    # see e.g. https://wiki.selfhtml.org/wiki/MIME-Type/%C3%9Cbersicht
    mimetype = ""

    if type == "vector":
        mimetype = "application/zip"
    # if format == "GeoJSON":
    #     mimetype = "application/geo+json"
    # if format == "CSV":
    #     mimetype = "text/csv"
    if type == "raster":
        if format == "GTiff" or format == "COG":
            mimetype = "image/tiff"
    if type == "strds":
        mimetype = "application/x-tar+gzip"
    if type == "file":
        if format == "PDF":
            mimetype = "application/pdf"
        else:
            mimetype = "application/zip"

    return mimetype

def extract_export(pc_el_inout_entry, pc_el_id, resources):
    """
    This function retrieves the exported filename from the provided process chain
    element entry and matches it with the corresponding resource URLs.
    It returns the formatted result as a dictionary containing the export information,
    including the resource URL and MIME type.

    Args:
        pc_el_inout_entry (dict): A dictionary containing the export entry details,
            including the value, export type, and format.
        pc_el_id (str): The unique identifier for the process chain element.
        resources (list): List of all resource URLs to match against the export output.

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
        pc_el_inout_entry["export"]["format"]
    )
    export_out = export_value + export_prefix

    # get mimetype of output
    export_mimetype = format_to_mimetype(
        pc_el_inout_entry["export"]["type"],
        pc_el_inout_entry["export"]["format"]
    )

    # match resource url + write results formated to dict
    export_out_dict = dict()
    export_out_dict_key = f"{pc_el_id}_{export_value}_{pc_el_inout_entry['export']['type']}_{pc_el_inout_entry['export']['format']}"
    match_resource_url = [url for url in resources if export_out in url]
    if match_resource_url:
        export_out_dict[export_out_dict_key] = {
            "href": match_resource_url[0],
            "type": export_mimetype
            # "rel": -> NOTE: wenn es passenden type gibt
            }

    return export_out_dict
    
def get_results(
        resp,
        resultResponse: str | None = None,
        transmissionMode: str | None = None,
):

    data = resp.json()
    resources = data["urls"]["resources"]
    result_format = dict()

    # -- Filter results from actinia
    # Exported results
    for pc_el in data["process_chain_list"][0]["list"]:
        if "inputs" in pc_el:
            for pc_inp_el in pc_el["inputs"]:
                if "export" in pc_inp_el:
                    export_out_dict = extract_export(pc_inp_el, pc_el["id"], resources)
                    result_format.update(export_out_dict)
        if "outputs" in pc_el:
            for pc_out_el in pc_el["outputs"]:
                if "export" in pc_out_el:
                    export_out_dict = extract_export(pc_out_el, pc_el["id"], resources)
                    result_format.update(export_out_dict)

    # Results from stdout
    stdout_ids = list()
    stdout_dict = {}
    for pc_el in data["process_chain_list"][0]["list"]:
        if "stdout" in pc_el:
            stdout_ids.append(pc_el["id"])
    for stdout_id in stdout_ids:
        for pc_log_el in data["process_log"]:
            if stdout_id == pc_log_el["id"]:
                stdout_dict[stdout_id] = pc_log_el["stdout"]
    result_format.update(stdout_dict)

    # -- Return results dependent on key-value of response and transmissionMode

    # TODO: set reasonable default values
    if not resultResponse:
        resultResponse = "document"
    if not transmissionMode:
        transmissionMode = "reference"

    status_code = 200
    if resultResponse == "document" and transmissionMode == "reference":
        return jsonify(result_format), status_code
    elif resultResponse == "document" and transmissionMode == "value":
        return jsonify(result_format), status_code
    # elif resultResponse == "document" and transmissionMode == "mixed":
        # allowed?
    elif resultResponse == "raw" and transmissionMode == "reference":
        status_code = 204
        return jsonify(result_format), status_code
        # direkt match_Resouce_url zurück geben
        # stdout nicht als reference, nur value
    # elif resultResponse == "raw" and transmissionMode == "value":
        # request auf resource_url? (redirect mit zurückgebbar)
        # z.B: mit from flask import redirect
    # elif resultResponse == "raw" and transmissionMode == "mixed":

    # TODO: some resultResponse/transmissionMode should be not allowed for certain actinia results
    #       if specified different via key/value pair -> return 405
