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

def format_to_prefix(format):
    # see here:
    # https://github.com/actinia-org/actinia-processing-lib/blob/main/src/actinia_processing_lib/ephemeral_processing_with_export.py
    prefix = ""
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
    if format == "GTiff":
        prefix = ".tif"
    # COG? other raster? 
    # strds -> .tar.gz (but format gtiff)
    return prefix
    
def get_results(resp):
    # for testing!
    result_mode = {
        "response": "document",
        "transmissionMode": "reference",
    }
    
    data = resp.json()
    result_format = dict()
    status_code = 200
    if result_mode["response"] == "document" and result_mode["transmissionMode"] == "reference":
        ind = 0
        for pc_el in data["process_chain_list"][0]["list"]:
            if "exporter" in pc_el["module"]:
                result_format[pc_el["id"]] = {
                    "href": data["urls"]["resources"][ind],
                    "type": "application/json"
                }
                ind += 1
        return jsonify(result_format), status_code
    # elif result_mode["response"] == "document" and result_mode["transmissionMode"] == "value":
    # elif result_mode["response"] == "raw" and result_mode["transmissionMode"] == "reference":
    #     status_code = 204
    # elif result_mode["response"] == "raw" and result_mode["transmissionMode"] == "value":
    # elif result_mode["response"] == "raw" and result_mode["transmissionMode"] == "mixed":

