#!/usr/bin/env python3
""" echochrono.py: Echo Arena Chronograph for Oculus Quest """

__author__ = 'Andrew Bates <a@sprock.io>'

import requests
import json
import time
import math
import datetime
import tempfile

import requests
import pyttsx3
import click
from pyfiglet import Figlet


def vector_coords_to_speed(vel):
    """ Convert 3D vector velocities into a linear velocity. """
    return round(math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2),2)

def get_session_frame(url):
    """ Retrieve and return the session json object from the oculus quest API at
    url """
    r = requests.get(url)
    try:
        return json.loads(r.text)
    except json.decoder.JSONDecodeError:
        click.echo('Invalid json.')
        return {}

def _get_possession(frame):
    """ Return the name of the player with posession of the disc """
    for t in frame['teams']:
        if 'players' in t:
            for p in t['players']:
                if p.get('possession'):
                    return p['name']
    return 'None'

@click.argument('questhost', metavar='HOST')
@click.option('-r', '--rate', help='refresh rate', type=float, default=0.25)
@click.option('-m', '--minimum-speed', 'minspeed',
              help='Minimum disc speed to read out', type=float,
              show_default=True, default=10.0)
@click.option('--stability-tolerance', 'tolerance', type=float, default=0.1)
@click.option('--tts/--no-tts', 'dotts', is_flag=True, default=True,
              help='Enable/Disable text-to-speech')
@click.option('--banner/--no-banner', 'showbanner', is_flag=True, default=True,
              help='Enable/Disable displaying velocity in large letters')
@click.option('--font', default='doh')
@click.option('-R','--record', 'recordpath', type=click.Path(),
              metavar='FILEPATH', help='Record session frames to FILEPATH')
@click.option('--figlet-font', 'font', metavar='FONTNAME', default='doh',
              help='figlet font to use for banner')
@click.command()
def main(questhost, rate, minspeed, dotts, showbanner, tolerance, font,
         recordpath, engine=pyttsx3.init()):
    """ Main console script """
    speeds = []

    if recordpath:
        click.echo('Writing session frames to {}'.format(recordpath))
        recordfp = open(recordpath, 'a')

    apiurl = 'http://{}:6721/session'.format(questhost)
    click.echo('Using Echo Arena API at {}'.format(apiurl))

    while True:
        time.sleep(rate)
        try:
            sessionframe = get_session_frame(apiurl)
            json.dump(sessionframe, recordfp)
            recordfp.write('\n')
        except requests.exceptions.ConnectionError:
            click.echo('Connection failed. Retrying... ')
            time.sleep(1)
            continue

        if 'disc' not in sessionframe:
            click.echo('No disc velocity found in session frame.'
                       " Waiting for match start?")
            time.sleep(1)
            continue

        speed = vector_coords_to_speed(sessionframe['disc']['velocity'])

        speeds = speeds[-10:] + [speed]

        if len(speeds) < 3:
            continue

        if sessionframe['disc']['bounce_count'] == 0 \
                and speed >= minspeed \
                and abs(speed - speeds[-2]) <= tolerance:

            player = _get_possession(sessionframe)
            click.echo('{:.1f} m/s by {}'.format(speed, player))
            if showbanner:
                click.echo()
                bannertext = '{:.1f}'.format(speed)
                click.echo(Figlet(font=font).renderText(str(bannertext)))

            if dotts:
                engine.say('{:.1f}'.format(speed))
                engine.runAndWait()
        #click.echo(print_big('{:.1f}'.format(speed)), color='green')


if __name__ =='__main__':
    main()
