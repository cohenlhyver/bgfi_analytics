#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import hwg_api_stu as hwg

vehicle_properties = {'vehicle_type': 'car',
                      'engine_gas': 'diesel',
                      'engine_consumption': 6.5}

origin = hwg.getGPSFromAddress('92, avenue des Champs-Elysées, 75008, Paris, France')
destination = hwg.getGPSFromAddress('25, Quai des Belges, 13001, Marseille, France')

response, legs = hwg.getRoute([origin, destination], vehicle_properties)

hwg.showRouteOnMap(legs)