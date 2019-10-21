#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 14 14:05:34 2019

@author: cohenlhyver

functions:
    - runRequest
    - getGPSFromAddress
    - formatResponseToGPS
    - formatGeocoderRequest
    - getRoute
    - formatRouteRequest
    - getRouteLegs
"""

# === LIBRARIES TO IMPORT === #
import re
import requests
import webbrowser

# === API URLs === %
GEOCODER_URL = 'https://geocoder.api.here.com/6.2/geocode.json?'
ROUTING_URL = 'https://route.api.here.com/routing/7.2/calculateroute.json?'
MAP_URL = 'https://image.maps.api.here.com/mia/1.6/mapview'
MAPROUTING_URL = 'https://image.maps.api.here.com/mia/1.6/routing'


# === ID & CODE === %
APP_ID = 'app_id=ofaaEVtxE5BrWM68AmtC&'
APP_CODE = 'app_code=7VVgtO0pWlQX8QxlyYl05Q&'


def runRequest(request):
    ''' Runs a request to the HereWeGo API
        Input:
            - request (str)
        Output:
            - dict
        Calls:
            - requests.get(request) [from requests pkg]
            - json() [converts json into Python dict type]
        Called by:
            - getGPSFromAddress()
            - getRoute()
    '''
    return requests.get(request).json()


def getGPSFromAddress(address):
    ''' Get the GPS location from a postal address.
        Input:
            - address (str)
                example: '92, avenue des Champs-Elysées, 75008, Paris, France'
        Output:
            - list[2] (float): [latitude, longitude]
        Calls:
            - formatGeocoderRequest(address)
            - runRequest(request)
            - formatResponseToGPS(response)
    '''
    request = formatGeocoderRequest(address)
    response = runRequest(request)
    return formatResponseToGPS(response)


def formatResponseToGPS(response):
    ''' Extract [latitude, longitude] from the result of a request
    '''
    return [response['Response']['View'][0]['Result'][0]['Location']['NavigationPosition'][0]['Latitude'],
            response['Response']['View'][0]['Result'][0]['Location']['NavigationPosition'][0]['Longitude']]


def formatGeocoderRequest(address):
    ''' Create a proper request for retrieving GPS coordinates from a postal address
        Input:
            - address [str]: postal address
        Output:
            - list[2] [float]: [latitude, longitude]
        Called by:
            - getGPSFromAddress(address)
        Example:
            formatGeocoderRequest('92, avenue des Champs-Elysées, 75008, Paris, France')
        TODO:
            Make it working for non French addresses (no commas)
    '''
    # === Finds all occurrences of ',' in a postal address
    commas = [comma.start() for comma in re.finditer(',', address)]
    # === Format the different field into a suitable HereWeGo request
    house_number = '&houseNumber=' + address[0:commas[0]]
    street = '&street=' + address[commas[0] + 1:commas[1]]
    postal_code = '&postalCode=' + address[commas[1] + 1:commas[2]]
    city = '&city=' + address[commas[2] + 1:commas[3]]
    country = '&country=' + address[commas[3] + 1:]
    # === Returns the request by concatenating all the variables
    return GEOCODER_URL + APP_ID + APP_CODE + country + city + street + house_number + postal_code


def getRoute(points, vehicle_properties, avoid_links=''):
    ''' Returns
    '''
    request = formatRouteRequest(points, vehicle_properties, avoid_links)
    response = runRequest(request)
    if 'response' in response.keys():
        response = response['response']
    legs = getRouteLegs(response)
    return response, [[legs[iLeg][0], legs[iLeg][1]] for iLeg in legs]


def formatRouteRequest(points, vehicle_properties, avoid_links=''):
    ''' Format a proper request to retrieve a GPS route
        Input:
            - points [list]: list of latitudes [float] and longitudes [float]
            - vehicle_properties [dict]:
                [keys:
                    - 'vehicle_type'='truck'|'car'
                    - 'engine_gas'='diesel'|'gas'|'electric'
                    - 'engine_consumption' (float)]
        Output:
            - [str]: the formatted request
        Called by:
            - getRoute()
    '''
    # === Format all the coordinates (from 'points' variable) the route has to go through
    waypoints = 'waypoint0=geo!' + str(points[0][0]) + ',' + str(points[0][1])
    for iPoint in range(1, len(points)):
        waypoints += '&waypoint' + str(iPoint) + '=geo!'
        waypoints += str(points[iPoint][0]) + ',' + str(points[iPoint][1])
    # === Properties about the type of vehicle used...
    mode = '&' + 'mode=fastest;' + vehicle_properties['vehicle_type'] + ';traffic:enabled'
    vehicle_prop = '&' + 'vehicletype=' + vehicle_properties['engine_gas'] + ',' + str(vehicle_properties['engine_consumption'])
    # === Points the route should avoid (using the 'linkId' variables from a previous request)
    avoid = avoid_links
    if len(avoid_links) != 0:
        avoid = '&avoidlinks='
        for iLink in avoid_links:
            avoid += iLink + ';'
        avoid = avoid[:-1]
    #lattr = '&legAttributes=wp,sm,sh'
    # === Returns the request as all the variables concatenated
#    return ROUTING_URL + APP_ID + APP_CODE + waypoints + lattr + mode + vehicle_prop + avoid
    return ROUTING_URL + APP_ID + APP_CODE + waypoints + mode + vehicle_prop + avoid


def getRouteLegs(response):
    ''' Extract information about each legs of the route
        Input:
            - response [dict]
        Output:
            - result [dict]:
                [values:
                    - [latitude [float], longitude [float]]
                    - travel time [float, in seconds]
                    - length of the legs [double, in meters]]
        Called by:
            - getRoute()
    '''
    legs = response['route'][0]['leg']
    nb_legs = len(legs)
    result = dict()
    for iLeg in range(nb_legs):
        points = legs[iLeg]['maneuver']
        for iIdx, iPoint in enumerate(points):
            idx = int(iPoint['id'][1:])
            result[idx] = [iPoint['position']['latitude'],
                           iPoint['position']['longitude']]
            result[idx].append(iPoint['travelTime'])
            result[idx].append(iPoint['length'])
    return result


def retrieveETA(response):
    ''' Retrieve the Estimated Time of Arrival from an API's request's response
    '''
    return response['route'][0]['summary']['trafficTime']/3600


def showRouteOnMap(route):
    ''' Displayed the computed route on a map in the default browser
    '''
    waypoints = 'waypoint0=geo!' + str(route[0][0]) + ',' + str(route[0][1])
    for iPoint in range(1, len(route)):
        waypoints += '&waypoint' + str(iPoint) + '=geo!'
        waypoints += str(route[iPoint][0]) + ',' + str(route[iPoint][1])
    request = MAPROUTING_URL + '?' + APP_ID + APP_CODE + waypoints
    webbrowser.open(request)


def showPointOnMap(coord):
    ''' Displays a single point on a map in the default browser
    '''
    request = MAP_URL + '?' + APP_ID + APP_CODE + 'c=' + str(coord[0]) + ',' + str(coord[1])
    webbrowser.open(request)
