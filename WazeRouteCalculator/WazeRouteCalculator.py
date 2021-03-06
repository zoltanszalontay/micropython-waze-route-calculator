# -*- coding: utf-8 -*-
"""Waze route calculator"""

from urequests import * #import urequests?
import re
import json

class WRCError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class WazeRouteCalculator(object):
    """Calculate actual route time and distance with Waze API"""

    WAZE_URL = "https://www.waze.com/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
        "referer": WAZE_URL,
    }

    def __init__(self, start_address, end_address, region='US'):
        print("From: {} - to: {}".format(start_address, end_address))

        region = region.upper()
        self.region = region


        if self.already_coords(start_address): #See if we have coordinates or address to resolve
            print("Start Coords are lat-long")
            self.start_coords = self.coords_string_parser(start_address)
        else:
            print("Start Coords are not lat-long")
            self.start_coords = self.address_to_coords(start_address)

        print('Start coords: ({}, {})'.format(self.start_coords["lat"], self.start_coords["lon"]))


        if self.already_coords(end_address): #See if we have coordinates or address to resolve
            print("End Coords are lat-long")
            self.end_coords = self.coords_string_parser(end_address)
        else:
            print("End Coords are not lat-long")
            self.end_coords = self.address_to_coords(end_address)

        print('End coords: ({}, {})'.format(self.end_coords["lat"], self.end_coords["lon"]))

    def already_coords(self, address):
        """test used to see if we have coordinates or address"""

        gps_match = '^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$'
        m = re.search(gps_match, address)
        return (m != None)

    def coords_string_parser(self, coords):
        """Pareses the address string into coordinates to match address_to_coords return object"""

        lat_lon = coords.split(',')
        lat = lat_lon[0].strip()
        lon = lat_lon[1].strip()
        bounds = {}
        return {"lat": lat, "lon": lon, "bounds": bounds}


    def address_to_coords(self, address):
        """Convert address to coordinates"""

        EU_BASE_COORDS = {"lat": "47.498", "lon": "19.040"}
        US_BASE_COORDS = {"lat": "40.713", "lon": "-74.006"}
        IL_BASE_COORDS = {"lat": "31.768", "lon": "35.214"}
        AU_BASE_COORDS = {"lat": "-35.281", "lon": "149.128"}
        BASE_COORDS = dict(US=US_BASE_COORDS, EU=EU_BASE_COORDS, IL=IL_BASE_COORDS, AU=AU_BASE_COORDS)[self.region]
        # the origin of the request can make a difference in the result

        get_cords = "row-SearchServer/mozi"
        # url_options = {
        #     "q": address,
        #     "lang": "eng",
        #     "origin": "livemap",
        #     "lat": BASE_COORDS["lat"],
        #     "lon": BASE_COORDS["lon"]
        # }
        address_to_coords_string = (self.WAZE_URL + get_cords + "?q=" +
            address + "&lang=eng&origin=livemap&lat=" +
            BASE_COORDS["lat"] + "&lon=" + BASE_COORDS["lon"]).replace(" ", "%20")
        print(address_to_coords_string)
        response = get(address_to_coords_string, headers=self.HEADERS)# get(self.WAZE_URL + get_cords, json=url_options, headers=self.HEADERS)
        try:
            for response_json in response.json():
                if response_json.get('city'):
                    lat = response_json['location']['lat']
                    lon = response_json['location']['lon']
                    bounds = response_json['bounds']  # sometimes the coords don't match up
                    if bounds is not None:
                        bounds['top'], bounds['bottom'] = max(bounds['top'], bounds['bottom']), min(bounds['top'], bounds['bottom'])
                        bounds['left'], bounds['right'] = min(bounds['left'], bounds['right']), max(bounds['left'], bounds['right'])
                    else:
                        bounds = {}
                    response.close()
                    return {"lat": lat, "lon": lon, "bounds": bounds}
        except ValueError as error:
            print("Bad JSON returned: \r\n%s" % (response.text))
            response.close()
            gc.collect()
            print("The request was sent to %s\r\n" % (self.WAZE_URL + get_cords))
#            print("with header %s" % (self.HEADERS))
#            print("and options %s" % (json.dumps(url_options, sort_keys=True, indent=4, separators=(',', ': '))))
            raise WRCError("Bad JSON returned")


        response.close()
        gc.collect()
        raise WRCError("Cannot get coords for %s" % address)

    def get_route(self, npaths=1, time_delta=0):
        """Get route data from waze"""

        routing_servers = ["row-RoutingManager/routingRequest",
                           "RoutingManager/routingRequest",
                           "il-RoutingManager/routingRequest"]
        # url_options = {
        #     "from": "x:%s y:%s" % (self.start_coords["lon"], self.start_coords["lat"]),
        #     "to": "x:%s y:%s" % (self.end_coords["lon"], self.end_coords["lat"]),
        #     "at": time_delta,
        #     "returnJSON": "true",
        #     "returnGeometries": "true",
        #     "returnInstructions": "true",
        #     "timeout": 60000,
        #     "nPaths": npaths,
        #     "options": "AVOID_TRAILS:t"
        # }

        for routing_srv in routing_servers:
            get_route_string = (self.WAZE_URL + routing_srv + "?" +
                ("from=x:" + str(self.start_coords["lon"]) +"y:" + str(self.start_coords["lat"])) +
                ("to=x:" + str(self.end_coords["lon"]) +"y:" + str(self.end_coords["lat"])) +
                "at=" + str(time_delta) +
                "returnJSON=true" +
                "returnGeometries=true" +
                "returnInstructions=true" +
                "timeout=60000" +
                "nPaths=" + str(npaths) +
                "options=AVOID_TRAILS:t").replace(" ", "%20")
            print(get_route_string)
            response = get(get_route_string, headers=self.HEADERS)
            response.encoding = 'utf-8'
            response_json = self._check_response(response)
            response.close()
            gc.collect()
            if response_json and 'error' not in response_json:
                if response_json.get("alternatives"):
                    return [alt['response'] for alt in response_json['alternatives']]
                if npaths > 1:
                    return [response_json['response']]
                return response_json['response']
        if response_json and 'error' not in response_json:
            raise WRCError(response_json.get("error"))
        else:
            raise WRCError("empty response")

    @staticmethod
    def _check_response(response):
        """Check waze server response."""
        # TODO: See if .ok exists in mPY
        try:
            return response.json()
        except ValueError as error:
            print("Bad JSON returned: \r\n%s" % (response.text))
            return False
#            print("with header %s" % (self.HEADERS))
#            print("and options %s" % (json.dumps(url_options, sort_keys=True, indent=4, separators=(',', ': '))))
        #    raise WRCError("Bad JSON returned")
        # if response.ok:
        #     try:
        #         return response.json()
        #     except ValueError:
        #         return None

    def _add_up_route(self, results, real_time=True, stop_at_bounds=False):
        """Calculate route time and distance."""

        start_bounds = self.start_coords['bounds']
        end_bounds = self.end_coords['bounds']

        def between(target, min, max):
            return target > min and target < max

        time = 0
        distance = 0
        for segment in results:
            if stop_at_bounds and segment.get('path'):
                x = segment['path']['x']
                y = segment['path']['y']
                if (
                    between(x, start_bounds.get('left', 0), start_bounds.get('right', 0)) or
                    between(x, end_bounds.get('left', 0), end_bounds.get('right', 0))
                ) and (
                    between(y, start_bounds.get('bottom', 0), start_bounds.get('top', 0)) or
                    between(y, end_bounds.get('bottom', 0), end_bounds.get('top', 0))
                ):
                    continue
            time += segment['crossTime' if real_time else 'crossTimeWithoutRealTime']
            distance += segment['length']
        route_time = time / 60.0
        route_distance = (distance / 1000.0) * 0.62137
        return route_time, route_distance

    def calc_route_info(self, real_time=True, stop_at_bounds=False, time_delta=0):
        """Calculate best route info."""

        route = self.get_route(1, time_delta)
        results = route['results']
        route_time, route_distance = self._add_up_route(results, real_time=real_time, stop_at_bounds=stop_at_bounds)
        printf('Time %.2f minutes, distance %.2f mi.', route_time, route_distance)
        return route_time, route_distance

    def calc_all_routes_info(self, npaths=3, real_time=True, stop_at_bounds=False, time_delta=0):
        """Calculate all route infos."""

        routes = self.get_route(npaths, time_delta)
        results = {route['routeName']: self._add_up_route(route['results'], real_time=real_time, stop_at_bounds=stop_at_bounds) for route in routes}
        route_time = [route[0] for route in results.values()]
        route_distance = [route[1] for route in results.values()]
        printf('Time %.2f - %.2f minutes, distance %.2f - %.2f mi.', min(route_time), max(route_time), min(route_distance), max(route_distance))
        return results
