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

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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

def mimetype_to_multipart_format(mimetype):
    if mimetype == "application/zip" or mimetype == "application/x-tar+gzip":
        from email.mime.application import MIMEApplication
        # application/zip
        with open("example.zip", "rb") as zip_file:
            part = MIMEApplication(zip_file.read(), _subtype="zip")
            part.add_header("Content-Disposition", "attachment", filename="example.zip")
        # application/x-tar+gzip
        with open("archive.tar.gz", "rb") as tar_gz_file:
            part = MIMEApplication(tar_gz_file.read(), _subtype="x-tar+gzip")
            part.add_header("Content-Disposition", "attachment", filename="archive.tar.gz")

    if mimetype == "image/tiff":
        from email.mime.image import MIMEImage
        # image/tiff
        with open("image.tiff", "rb") as tiff_file:
            part = MIMEImage(tiff_file.read(), _subtype="tiff")
            part.add_header("Content-Disposition", "attachment", filename="image.tiff")

    if mimetype == "application/pdf":
        from email.mime.application import MIMEApplication
        # application/pdf
        with open("document.pdf", "rb") as pdf_file:
            part = MIMEApplication(pdf_file.read(), _subtype="pdf")
            part.add_header("Content-Disposition", "attachment", filename="document.pdf")

    return part

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

    if not result_format:
        # TODO: 405 or empty return?
        return make_response("No results returned for current job", 405)

    # NOTE: current dict key combination of pc_el_id etc. -> better if defined output from processing?
    #       (would required valkey db o.ä.?)

    # -- Return results dependent on key-value of response and transmissionMode

    # TODO: how to substitute localhost -> relevant for all reference links
    #       actinia core resource in logs?

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
        transmissionMode = "mixed" # -> mixed? -> see below
    # NOTE/TODO:
    # according to standard:
    # * response -> for complete request (not per output)
    #   * possible: document or raw
    # * transmissionmode -> per output
    #   * possible: value or reference (NOT: mixed)
    # transmissionmode = mixed => mutliple outputs with different transmission modes requested
    # BUT: with key-value as it is configured now -= transmissionmode not per output defined
    #      instead: give/add "mixed" explicitely as transmissionmode?
    #      OR: must define for each output via key value???


    # default status_code for most returns
    status_code = 200

    if resultResponse == "document":
        # Note: for document the transmissionMode must not be filtered
        #       the correct formatting is already given by the results
        #       e.g. a tif can not be returned as raw binary in a json,
        #       so reference is used. If value desired, then it would need to be
        #       directly returned as e.g. base64 encoded (so already value)
        return make_response(jsonify(result_format), status_code)

    elif resultResponse == "raw" and transmissionMode == "reference":
        # stdout result not supported as reference
        if stdout_dict and not export_out_dict:
            return make_response(
                ("Format resultResponse=raw and transmissionMode=reference "
                "not allowed for current job results. "
                "Use e.g. transmissionMode=value"),
                405,
            )
        if stdout_dict and export_out_dict:
            return make_response(
                ("Format resultResponse=raw and transmissionMode=reference "
                "not allowed for current job results. "
                "Use e.g. transmissionMode=mixed"),
                405,
            )

        status_code = 204
        if not stdout_dict and export_out_dict:
            response = make_response("", status_code)
            # format Link header, see e.g. here https://greenbytes.de/tech/webdav/rfc8288.html
            links_list =[]
            for key, value in result_format.items():
                if "href" in value:
                    # TODO/NOTE: braucht links ein 'rel' type?
                    # wenn ja welcher passt dann? (kein passenden gefunden unter 5.2)
                    # TODO: format so korrekt? richtig "manuell" zu machen?
                    links_list.append(f"<{value['href']}>")
            response.headers["Link"] = ", ".join(links_list)
            return response

    elif resultResponse == "raw" and transmissionMode == "value":
        # single result
        if len(result_format) == 1:
            value = next(iter(result_format.values()))
            if "href" in value:
                # flask.redirect
                return redirect(value["href"])
                # NOTE: damit -> currently full doctype html
                #       + status_code of redirect not 200 (303?)
                # alternative?: (nicht mit localhost)
                # import requests
                # return requests.get(value["href"])
            else:
                return make_response(value, status_code)

        # multiple results
        multipart_message = MIMEMultipart("related")
        if export_out_dict:
            for key, value in result_format.items():
                if "href" in value:
                    # Add as a related part with Content-Type
                    # TODO: wirklich value für ref links?
                    # siehe mimetype_to_multipart_format -> dann alle daten lesen
                    # gewünscht?
                    # wenn ja -> funktion finalisieren
                    # wenn nein -> bei #out > 1 + export_out_dict -> 405, und mixed empfehlen?
                    part = mimetype_to_multipart_format(value["type"])
                    multipart_message.attach(part)
        if stdout_dict:
            for stdout_id, stdout_content in stdout_dict.items():
                part = MIMEText(stdout_content, "plain")
                part.add_header("Content-ID", f"<{stdout_id}>")
                multipart_message.attach(part)
        response = make_response(multipart_message.as_string(), status_code)
        response.headers["Content-Type"] = "multipart/related"
        return response

    elif resultResponse == "raw" and transmissionMode == "mixed":
        multipart_message = MIMEMultipart("related")
        if export_out_dict:
            for key, value in result_format.items():
                if "href" in value:
                    # Erstelle eine MIMEMessage für einen externen Link
                    # base_message = Message()
                    from email.mime.base import MIMEBase
                    reference_part = MIMEBase("message", "external-body")
                    reference_part.add_header("Content-ID", key)
                    reference_part.add_header("Content-Location", value["href"])
                    reference_part.set_payload("This is a reference to an external resource.")
                    multipart_message.attach(reference_part)
        if stdout_dict:
            for stdout_id, stdout_content in stdout_dict.items():
                part = MIMEText(stdout_content, "plain")
                part.add_header("Content-ID", f"<{stdout_id}>")
                multipart_message.attach(part)
        response = make_response(multipart_message.as_string(), status_code)
        response.headers["Content-Type"] = "multipart/related"
        return response
