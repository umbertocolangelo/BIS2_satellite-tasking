# Satellite Tasking Microservice

This microservice is part of a larger microservices-based architecture developed for a **Recommender System** aimed at detecting and responding to critical events. The role of this specific microservice is to handle **satellite tasking**, where it interacts with satellite data sources, processes recommendations for tasking, and retrieves satellite images based on areas and dates of interest. The code was developed for **Business Information Systems 2** course at Politecnico di Milano in collabolation with **eGeos** and **Cherrydata**

The microservice is built using **Flask** to expose a REST API, and it integrates with the **Microsoft Planetary Computer** to download satellite imagery, including data from **Landsat**, **Sentinel**, and **MODIS**.

## Key Features

1. **Satellite Tasking**:
   - Receives recommendations via a POST request in JSON format containing subareas and satellite rankings.
   - Identifies the optimal satellite for tasking based on predefined ranking and cost constraints.
   - Downloads satellite imagery for the subareas of interest from available data sources.

2. **Imagery Download**:
   - Fetches satellite images from the Microsoft Planetary Computer using the **STAC API**.
   - Supports satellite collections such as **Landsat**, **Sentinel**, and **MODIS**.
   - Downloads images for the dates immediately before and after the critical event.
   - Saves images and recommendation files to a structured directory.

3. **Asynchronous Execution**:
   - The microservice processes the tasking and image downloads asynchronously using Python threads to avoid blocking the API while the images are being fetched.

## Technologies Used

- **Flask**: The microservice is built on Flask, a lightweight Python web framework, to handle HTTP requests.
- **pystac_client**: This library is used to interact with the Planetary Computer’s STAC API for querying satellite data.
- **Microsoft Planetary Computer**: The microservice integrates with Planetary Computer for satellite data retrieval.
- **Clint**: Used for showing download progress when fetching images.
- **Threading**: Python’s `Thread` class is used to execute downloads in parallel, improving performance by avoiding blocking on long-running tasks.
