# -*- coding: utf-8 -*-
import pystac_client
import planetary_computer
import requests
from datetime import datetime, timedelta
import pytz
import os
from clint.textui import progress
import json
from flask import Flask, request
from threading import Thread

app = Flask(__name__)


def prepare_output(recommendation_json):

    for i, subarea in enumerate(recommendation_json['ranking']['subareas']):

        # Retrieve the information used for tasking
        ranking = subarea['ranking']
        area_of_interest = subarea['geometry']

        # Retrieve date of interest
        utc = pytz.UTC
        date = utc.localize(datetime.fromisoformat(recommendation_json['ranking']['event_date']))

        # If it doesn't exist already, create folder for the output
        folder_name = f"{recommendation_json['ranking']['event_id']}_{recommendation_json['ranking']['aoi_id']}_{i+1}"
        if not os.path.exists(folder_name):
            os.mkdir(folder_name)

        # Generate recommendation file and save it in the output directory
        generate_recommendation_file(subarea, folder_name)

        # Pick the satellite ranked first
        if recommendation_json['ranking']['ranking_ord'] == "desc":
            satellite = ranking[0]
        else:
            satellite = ranking[len(ranking)]

        # If the satellite does not have a free API there is nothing else to do
        if satellite['tasking']['type'] != 'API' or satellite['tasking']['cost_per_sq_km'] != 0:
            return

        # Call the download function
        download_images(satellite['family'], area_of_interest, date, folder_name)


def save_image(item, asset, img_folder_name):
    file_name = asset
    if ".tif" in item.assets[asset].href.lower():
        file_name = f"{file_name}.tif"
    if not os.path.exists(os.path.join(img_folder_name, file_name)):
        print(f"Downloading {file_name}")
        r = requests.get(item.assets[asset].href, stream=True)
        with open(os.path.join(img_folder_name, file_name), 'wb') as f:
            total_length = int(r.headers.get('content-length'))
            for chunk in progress.bar(r.iter_content(chunk_size=1024),
                                      expected_size=(total_length / 1024) + 1):
                if chunk:
                    f.write(chunk)
                    f.flush()
        f.close()


def download_images(satellite, area_of_interest, date, output_folder):

    if satellite == "Landsat" or satellite == "Sentinel":

        match satellite:
            case "Landsat":
                collections = ["landsat-c2-l2"]
            case "Sentinel":
                collections = ["sentinel-2-l2a"]
            case _:
                print(f"{satellite['satName']} is not supported yet")
                return

        # Define the time interval of interest
        start_date = date - timedelta(days=14)
        end_date = date + timedelta(days=14)
        time_of_interest = f"{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"

        # Connect to the MS Planetary Computer API
        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )

        # Query the API
        search = catalog.search(
            collections=collections,
            datetime=time_of_interest,
            intersects=area_of_interest
        )
        items = search.item_collection()

        # Find the dates immediately before and after the event
        date_before = None
        date_after = None

        for i in range(len(items) - 1):
            if items[i].datetime > date > items[i + 1].datetime:
                print(f"Selected dates: {items[i].datetime.strftime('%Y-%m-%d')} - "
                      f"{items[i + 1].datetime.strftime('%Y-%m-%d')}")
                date_before = items[i].datetime
                date_after = items[i + 1].datetime
                break
            date_before = items[0].datetime

        # Download the images from the selected dates in the output directory
        for item in items:
            if item.datetime == date_before or item.datetime == date_after:
                img_folder_name = os.path.join(output_folder, item.id)
                if not os.path.exists(img_folder_name):
                    os.mkdir(img_folder_name)
                for asset in item.assets:
                    save_image(item, asset, img_folder_name)

    elif satellite == "Modis":

        catalog = pystac_client.Client.open(
            "https://planetarycomputer.microsoft.com/api/stac/v1",
            modifier=planetary_computer.sign_inplace,
        )
        # Define the time interval of interest
        dates = [date - timedelta(days=8), date + timedelta(days=8)]
        for date in dates:
            print(f"Fetching {date}")
            search = catalog.search(
                collections=["modis-09A1-061"],
                intersects=area_of_interest,
                datetime=datetime,
            )
            items = search.item_collection()

            # Download the images from the selected dates in the output directory
            for item in items:
                img_folder_name = os.path.join(output_folder, item.id)
                if not os.path.exists(img_folder_name):
                    os.mkdir(img_folder_name)
                for asset in item.assets:
                    save_image(item, asset, img_folder_name)


def generate_recommendation_file(subarea, output_folder):

    # Get file with tasking information
    with open('tasking_info.json', 'r') as f:
        tasking_info = json.load(f)

    # Associate each satellite with its tasking information
    for satellite in subarea['ranking']:
        del satellite["details"]["apiURL"]
        for info in tasking_info:
            if satellite['family'] == info["name"]:
                satellite['tasking'] = info['tasking']

    # Include recommendation file in the output directory
    output_file = open(os.path.join(output_folder, "recommendation.json"), "w")
    output_file.write(json.dumps(subarea, indent=4))
    output_file.close()


@app.route("/tasking/main", methods=['GET', 'POST'])
def tasking():

    if request.method == 'POST':

        # Get JSON data from the request
        recommendation_json = request.get_json()

        # Create new thread to download the images
        thread = Thread(target=prepare_output, args=(recommendation_json,))
        thread.start()

        return "Downloads started"

    else:

        # The request should be a POST
        return "This the main function, please POST the input data"
