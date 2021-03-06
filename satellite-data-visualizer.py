#!/usr/bin/env python2.7

#   Copyright (c) 2015 Martin F. Falatic
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Satellite Data Visualizer for Python
------------------------------------

Author: Martin Falatic, 2015-10-15
Based on code by user /u/chknoodle_aggie 2015-08-14 as posted in
https://www.reddit.com/r/Python/comments/3gwzjr/using_pyephem_i_just_plotted_every_tleinfo/

More about TLE:
https://en.wikipedia.org/wiki/Two-line_element_set
http://spaceflight.nasa.gov/realdata/sightings/SSapplications/Post/JavaSSOP/SSOP_Help/tle_def.html

"""

from __future__ import print_function   # PEP 3105: Make print a function

import math
import time
from datetime import datetime, timedelta
import sys
import os.path
import ephem
import numpy as np
import matplotlib.pyplot as plt
import zipfile
import geocoder

try:
    from urllib.request import URLopener
except ImportError:
    from urllib import URLopener

try:
    input = raw_input
except NameError:
    pass

TITLE = "Satellite Data Visualizer for Python"
DEBUG = False
SIMSECS = 0  # 60*60
t = time.time()

tleSources = [
    {'name':  'McCant\'s classifieds',
     'url':   'https://www.prismnet.com/~mmccants/tles/classfd.zip',
     'file':  'classfd.zip',
     'color': '#000000'},

    {'name':  'AUS-CITY all',
     'url':   'http://www.tle.info/data/ALL_TLE.ZIP',
     'file':  'ALL_TLE.ZIP',
     'color': '#ffffff'},

    {'name':  'AUS-CITY GPS',
     'url':   'http://www.tle.info/data/gps-ops.txt',
     'file':  'gps-ops.txt',
     'color': '#ff0000'},

    {'name':  'Celestrak visual',
     'url':   'http://www.celestrak.com/NORAD/elements/visual.txt',
     'file':  'visual.txt',
     'color': '#00ff00'},

    {'name':  'Planet Labs',
     'url':   'http://ephemerides.planet-labs.com/planet_mc.tle',
     'file':  'planet_mc.tle',
     'color': '#00ffff'},

    # {'name':  'Celestrak BREEZE-M R/B',
    #  'url':   'http://www.celestrak.com/NORAD/elements/2012-044.txt',
    #  'file':  '2012-044.txt',
    #  'color': '#0000ff'},
    ]


def readTLEfile(source):
    ''' Read a TLE file (unzip if necessary) '''
    sourceName = source['name']
    sourceUrl = source['url']
    sourceFile = source['file']
    if os.path.isfile(sourceFile):
        print('Using saved TLE data {} ({})'.format(sourceFile,
              time.ctime(os.path.getmtime(sourceFile))))
    else:
        print('Retrieving TLE data from {}'.format(sourceUrl))
        file = URLopener()
        try:
            file.retrieve(sourceUrl, sourceFile)
        except:
            print("Error: Failed to get TLE data")
            return None
        else:
            print('{} updated'.format(sourceFile))

    if sourceFile.lower().endswith('.zip'):
        print('Unzipping {}...'.format(sourceFile))
        zip = zipfile.ZipFile(sourceFile)
        zip.extractall('.')
        sourceFile = zip.namelist()[0]
        print('Extracted {}'.format(zip.namelist()))

    tempContent = []
    with open(sourceFile) as f:
        for aline in f:
            tempContent.append(aline.replace('\n', ''))
        print(len(tempContent) // 3,
              'TLEs loaded from {}'.format(sourceFile))

    return tempContent


def processTLEdata(tleSources):
    ''' Process each TLE entry '''
    sats = []
    for source in tleSources:
        print("Processing {}".format(source['name']))
        tempContent = readTLEfile(source=source)
        print()
        if tempContent:
            i_name = 0
            while 3 * i_name + 2 <= len(tempContent):
                rawTLEname = tempContent[3 * i_name + 0]
                rawTLEdat1 = tempContent[3 * i_name + 1]
                rawTLEdat2 = tempContent[3 * i_name + 2]
                partsTLEdat1 = rawTLEdat1.split()
                try:
                    body = ephem.readtle(rawTLEname, rawTLEdat1, rawTLEdat2)
                except ValueError:
                    print("Error: line does not conform to tle format")
                    print("       " + rawTLEname)
                    print("       " + rawTLEdat1)
                    print("       " + rawTLEdat2)
                    print()
                else:
                    name = body.name
                    number = partsTLEdat1[1]
                    designator = partsTLEdat1[2]
                    sats.append({'name': name,
                                 'number': number,
                                 'designator': designator,
                                 'color': source['color'],
                                 'body': body, })
                    # print("{} {} {} {}".
                    #     format(name, number, designator, body))
                i_name += 1
                # if i_name > 100:
                #     break
    return sats


def getLocation():
    ''' Get user location based on input '''
    defaultLocation = "San Francisco, CA"
    # Note: Pontianak, Indonesia and Quito, Ecuador are right on the equator
    locationKeyword = ''
    while not locationKeyword:
        locationKeyword = input(
            'Enter location (default="{}"): '.format(defaultLocation))
        if not locationKeyword or locationKeyword.isspace():
            locationKeyword = defaultLocation
        g = geocoder.google(locationKeyword)
        if g.status != 'OK':
            print('Location not found: "{}"'.format(locationKeyword))
            locationKeyword = ''
        else:
            print()
            print('Location found: "{}"'.format(g.location))
    if DEBUG:
        print()
        print(g.json)
    return g


def plotSats(savedsats, latitude, longitude, elevation):
    home = ephem.Observer()
    home.lat = str(latitude)    # +N
    home.lon = str(longitude)   # +E
    home.elevation = elevation  # meters

    if DEBUG:
        print('{}N {}E, {}m'.format(latitude, longitude, elevation))
        print('{}N {}E, {}m'.format(home.lat, home.lon, home.elevation))
        print()

    print('-'*79)
    print()

    fig = plt.figure()
    fig.canvas.set_window_title(TITLE)

    global t
    t = time.time()
    currdate = datetime.utcnow()
    errored_sats = set()

    while 1:
        if SIMSECS > 0:
            currdate += timedelta(seconds=SIMSECS)
        else:
            currdate = datetime.utcnow()
        home.date = currdate
        theta_plot = []
        r_plot = []
        colors = []

        def handle_close(event):
            # This doesn't work well yet
            # print("Close event received")
            pass

        # Click on a satellite to print its TLE name to the console
        def onpick(event):
            global t
            if time.time() - t < 1.0:  # limits calls to 1 per second
                return
            t = time.time()
            ind = event.ind
            r = np.take(r_plot, ind)[0]
            theta = np.take(theta_plot, ind)[0]
            for satdata in savedsats:
                if (math.degrees(theta) == math.degrees(satdata['body'].az) and
                        math.cos(satdata['body'].alt) == r):
                    break
            print('name=' + satdata['body'].name,
                  'az=' + str(math.degrees(satdata['body'].az)),
                  'alt=' + str(math.degrees(satdata['body'].alt)))

        for satdata in savedsats:  # for each satellite in the savedsats list
            try:
                satdata['body'].compute(home)
                alt = satdata['body'].alt
            except ValueError:
                pass  # print("Date out of range")
            except RuntimeError:
                if satdata['name'] not in errored_sats:
                    errored_sats.add(satdata['name'])
                    print("Cannot compute position for {}".format(satdata['name']))
            else:
                if math.degrees(alt) > 0.0:
                    theta_plot.append(satdata['body'].az)
                    r_plot.append(math.cos(satdata['body'].alt))
                    colors.append(satdata['color'])

        # plot initialization and display
        pltTitle = str(home.date)
        ax = plt.subplot(111, polar=True)
        ax.set_title(pltTitle, va='bottom')
        ax.set_theta_offset(np.pi / 2.0)  # Top = 0 deg = north
        ax.set_theta_direction(-1)  # clockwise
        ax.xaxis.set_ticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        ax.yaxis.set_ticklabels([])  # hide radial tick labels
        ax.grid(True)
        ax.scatter(theta_plot, r_plot, c=colors, alpha=0.5, picker=True)
        ax.set_rmax(1.0)
        fig.canvas.mpl_connect('pick_event', onpick)
        fig.canvas.mpl_connect('close_event', handle_close)
        plt.pause(0.25)  # A pause is needed here, but the loop is rather slow
        fig.clf()


if __name__ == "__main__":
    print()
    print('-'*79)
    print(TITLE)
    print('-'*79)
    print()
    savedsats = processTLEdata(tleSources)
    g = getLocation()
    (latitude, longitude) = g.latlng
    elevation = geocoder.elevation(g.latlng).meters
    plotSats(savedsats=savedsats, latitude=latitude,
             longitude=longitude, elevation=elevation)
