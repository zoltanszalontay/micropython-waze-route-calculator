#!/usr/bin/env python
# -*- coding: utf-8 -*-
import WazeRouteCalculator

from_address = 'Budapest, Hungary'
to_address = 'Gyor, Hungary'
route = WazeRouteCalculator.WazeRouteCalculator(from_address, to_address, 'EU')#, 'US')


try:
    route.calc_route_info()
except WazeRouteCalculator.WRCError as err:
    print(err)
