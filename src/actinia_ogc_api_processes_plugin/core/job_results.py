#!/usr/bin/env python
"""SPDX-FileCopyrightText: (c) 2026 by mundialis GmbH & Co. KG.

SPDX-License-Identifier: GPL-3.0-or-later

Core helper to fetch job results from actinia processing API.
"""

__license__ = "GPL-3.0-or-later"
__author__ = "Lina Krisztian"
__copyright__ = "Copyright 2026 mundialis GmbH & Co. KG"
__maintainer__ = "mundialis GmbH & Co. KG"

from flask import jsonify, make_response, redirect

import json
import re

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase

from actinia_ogc_api_processes_plugin.resources.config import ACTINIA

from actinia_ogc_api_processes_plugin.model.response_models import SimpleStatusCodeResponseModel

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
        # replace user-url with base-url
        resource_url = re.sub(r'https?://[^/]+/api/v\d+',ACTINIA.user_actinia_base_url,match_resource_url[0])
        export_out_dict[export_out_dict_key] = {
            "href": resource_url,
            "type": export_mimetype
            # "rel": -> NOTE: wenn es passenden type gibt
            }

    return export_out_dict
    
def stdout_to_multipart(stdout_dict):
    for stdout_id, stdout_content in stdout_dict.items():
        # for different return types from actinia dependent on format, see here:
        # https://github.com/actinia-org/actinia-processing-lib/blob/main/src/actinia_processing_lib/ephemeral_processing.py#L2086-L2125
        if type(stdout_content) is dict:
            part = MIMEText(json.dumps(stdout_content), "json")
        else:
            # tables to list for regular and nested lists
            data = stdout_content if isinstance(stdout_content[0], list) else [[x] for x in stdout_content]
            table = "\n".join(",".join(map(str, row)) for row in data)
            part = MIMEText(table, "plain")
        part.add_header("Content-ID", stdout_id)
    return part

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
    export_out_dict = None
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
    stdout_dict = {}
    for pc_rel_el in data["process_results"]:
       pc_rel_data = data["process_results"][pc_rel_el]
       stdout_dict[pc_rel_el] = pc_rel_data

    result_format.update(stdout_dict)

    # NOTE: Current dict key (returned Content-ID) of result_format is a combination of pc_el_id etc.
    #       If persisent information from processing start given -> set as output defined there

    # TODO: separate PR:
    #       add key "log" as last element of result_format with link to complete actinia response (data["urls"]["status"])
    #       replace with ACTINIA.user_actinia_base_url
    #       Note: check what to return, depent on transmissionmode/resultrepsonser, e.g. not for raw

    # -- Return results dependent on key-value of response and transmissionMode

    # 7.11.4.  Response
    # Table 11
    # This table shows all possible combinations of execute parameters that are specified by this standard.
    # Not all of these combinations need to be implemented by a server conforming to this standard.
    # For example, if a server only offers processes that support multiple outputs by value,
    # then the server must support multipart/related responses as indicated in Table 11.
    # If, on the other hand, the server only offers processes that support multiple outputs by reference,
    # then the server does not need to support multipart/related responses.
    # -> for actinia: choose supported combinations different for exported and stdout results

    # default values, if not explicitely given
    if not resultResponse:
        # 7.11.2.4.  Response type -> "The default value, if the parameter is not specified is raw."
        resultResponse = "raw"
    if not transmissionMode:
        # transmissionmode = mixed
        # - originally: when mutliple outputs with different transmission modes requested
        # - for actinia: automatically given if stdout (value) and exported results (reference) returned from
        # mixed allowed for all actinia results, thus choosen as default
        transmissionMode = "mixed"

    # default status_code for most returns
    status_code = 200

    if resultResponse == "document":
        # Note: for document the transmissionMode must not be filtered
        #       the correct formatting is already given by the results
        #       e.g. a tif can not be returned as raw binary in a json,
        #       so reference is used. If value desired, then it would need to be
        #       directly returned as e.g. base64 encoded (so already value)
        #       Especially here for actinia result format already fixed:
        #       stdout -> value | export -> reference
        #       thus no need to filter for transmissionMode
        return make_response(jsonify(result_format), status_code)

    elif resultResponse == "raw" and transmissionMode == "reference":
        # stdout result not supported as reference
        if stdout_dict and not export_out_dict:
            res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=405,
                        message=(
                            "Format resultResponse=raw and transmissionMode=reference "
                            "not allowed for current job results. "
                            "Use e.g. transmissionMode=value"
                        ),
                    ),
                )
            return make_response(res,405)
        if stdout_dict and export_out_dict:
            res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=405,
                        message=(
                            "Format resultResponse=raw and transmissionMode=reference "
                            "not allowed for current job results. "
                            "Use e.g. transmissionMode=mixed"
                        ),
                    ),
                )
            return make_response(res,405)

        status_code = 204
        if not stdout_dict and export_out_dict:
            response = make_response("", status_code)
            # format Link header, see e.g. here https://greenbytes.de/tech/webdav/rfc8288.html
            links_list =[]
            for key, value in result_format.items():
                if "href" in value:
                    # NOTE: if needed can add 'rel' type with semicolon e.g.
                    # Link: <https://example.org/>; rel="start",
                    #       <https://example.org/index>; rel="index"
                    links_list.append(f"<{value['href']}>")
            response.headers["Link"] = ", ".join(links_list)
            return response

    elif resultResponse == "raw" and transmissionMode == "value":
        # -- single result
        if len(result_format) == 1:
            value = next(iter(result_format.values()))
            if "href" in value:
                # flask.redirect
                #return redirect(value["href"])
                # NOTE: damit -> currently full doctype html
                #       + status_code of redirect not 200 (303?)
                # TODO: wenn 303 -> dann doch mit requests
                #       testen mit tif (1GB)-> laufzeit, timeout??
                # alternative?: (nicht mit localhost)
                import requests
                return requests.get(value["href"])
            else:
                return make_response(value, status_code)

        # -- multiple results
        if not stdout_dict and export_out_dict:
            res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=405,
                        message=(
                            "Format resultResponse=raw and transmissionMode=value "
                            "not allowed for current job results. "
                            "Use e.g. transmissionMode=reference"
                        ),
                    ),
                )
            return make_response(res,405)
        if stdout_dict and export_out_dict:
            res = jsonify(
                    SimpleStatusCodeResponseModel(
                        status=405,
                        message=(
                            "Format resultResponse=raw and transmissionMode=value "
                            "not allowed for current job results. "
                            "Use e.g. transmissionMode=mixed"
                        ),
                    ),
                )
            return make_response(res,405)
        # fallback: only stdout
        multipart_message = MIMEMultipart("related")
        if stdout_dict:
            multipart_message.attach(stdout_to_multipart(stdout_dict))

        response = make_response(multipart_message.as_string(), status_code)
        response.headers["Content-Type"] = "multipart/related"
        return response

    elif resultResponse == "raw" and transmissionMode == "mixed":
        multipart_message = MIMEMultipart("related")
        if export_out_dict:
            for key, value in result_format.items():
                if "href" in value:
                    reference_part = MIMEBase("message", "external-body")
                    reference_part.add_header("Content-ID", key)
                    reference_part.add_header("Content-Location", value["href"])
                    reference_part.set_payload("This is a reference to an external resource.")
                    multipart_message.attach(reference_part)
        if stdout_dict:
            multipart_message.attach(stdout_to_multipart(stdout_dict))

        response = make_response(multipart_message.as_string(), status_code)
        response.headers["Content-Type"] = "multipart/related"
        return response
