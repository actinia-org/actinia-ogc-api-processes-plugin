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
    # mapping of formats see here:
    # https://github.com/actinia-org/actinia-processing-lib/blob/main/src/actinia_processing_lib/ephemeral_processing_with_export.py
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

def extract_export(pc_el):
    # get output name + format for later matching with corresponding resources link

    for export_params in pc_el["outputs"]: # TODO: check for input and output
        # get value name
        if "$file::" in export_params["value"]:
            # file export generated from GRASS GIS module
            # (value with $file::unique_id)
            export_value = export_params["value"].split("$file::")[1]
        else:
            export_value = export_params["value"]
        export_prefix = format_to_prefix(
            export_params["export"]["type"],
            export_params["export"]["format"]
        )
        export_out = export_params["value"] + export_prefix
        export_out_dict_key = f"{pc_el['id']}_{export_value}_{export_params['export']['type']}_{export_params['export']['format']}"
        return export_out_dict_key, export_out
    
def get_results(resp):

    # hardcoded for testing!
    result_mode = {
        "response": "document",
        "transmissionMode": "reference",
    }
    
    data = resp.json()
    result_format = dict()
    status_code = 200
    if result_mode["response"] == "document" and result_mode["transmissionMode"] == "reference":
        export_out_dict = dict()
        for pc_el in data["process_chain_list"][0]["list"]:
            if "exporter" in pc_el["module"]:
                # Note: POSTGIS not supported
                # TODO: exception for postgsi needed?
                # results from exporter, see here:
                # https://github.com/actinia-org/actinia-processing-lib/blob/main/src/actinia_processing_lib/ephemeral_processing_with_export.py
                export_out_dict_key, exporter_out = extract_export(pc_el)
                export_out_dict[export_out_dict_key] = exporter_out
            elif "outputs" in pc_el: # TODO: sowohl für outputs als auch inputs abfragen
                for export_params in pc_el["outputs"]: 
                    if "export" in export_params:
                        export_out_dict_key, exporter_out = extract_export(pc_el)
                        export_out_dict[export_out_dict_key] = exporter_out

        for key, value in export_out_dict.items():
            resources = data["urls"]["resources"]
            match_resource_url = [url for url in resources if value in url]
            result_format[key] = {
                "href": match_resource_url[0],
                "type": "application/json" # TODO: /tif, /zip, etc.
                # "rel": -> wenn es passenden type gibt
            }
        return jsonify(result_format), status_code
    elif result_mode["response"] == "document" and result_mode["transmissionMode"] == "value":
        # stdout
        return jsonify(result_format), status_code
    # elif result_mode["response"] == "document" and result_mode["transmissionMode"] == "mixed":
        # allowed?
    # elif result_mode["response"] == "raw" and result_mode["transmissionMode"] == "reference":
        # status_code = 204
        # direkt match_Resouce_url zurück geben
        # stdout nicht als reference, nur value
    # elif result_mode["response"] == "raw" and result_mode["transmissionMode"] == "value":
        # request auf resource_url? (redirect mit zurückgebbar)
        # z.B: mit from flask import redirect
    # elif result_mode["response"] == "raw" and result_mode["transmissionMode"] == "mixed":

