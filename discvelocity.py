#!/usr/bin/env python3
""" echochrono.py: Echo Arena Chronograph for Oculus Quest """

__author__ = 'Andrew Bates <a@sprock.io>'

import requests
import json
import time
import math
import datetime
import tempfile
import logging

import requests
import pyttsx3
import click
from pyfiglet import Figlet


def _setup_logging():
    """ Configure loggers """
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.WARNING)
    return logging.getLogger(__name__)


def vector_coords_to_speed(vel):
    """ Convert 3D vector velocities into a linear velocity. """
    return round(math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2),2)


def get_session_frame(url):
    """ Retrieve and return the session json object from the oculus quest API at
    url """
    r = requests.get(url)
    if r.status_code == 404:
        log.warning('No session data. API returned 404.')
        return {}
    try:
        # fix bug when private arena is restarted
        s = r.text.replace('-nan.','')
        return json.loads(s)
    except json.decoder.JSONDecodeError as e:
        log.error('Invalid json')
        log.debug('JSON decode error: {}'.format(e))
        return {}


def _get_player_with_possession(frame):
    """ Return the name of the player with posession of the disc """
    for t in frame['teams']:
        for p in t.get('players',[]):
            if p.get('possession'):
                return p
    return {}


def _relative_velocity(vel1, vel2):
    """ Return x,y,z velocities for vel2 relative to vel1 """
    return [ v1 - v2 for (v1, v2) in zip(vel1, vel2)]

@click.argument('questhost', metavar='<QUEST IP>')
@click.option('-r', '--refresh-rate', 'refreshrate', help='Disc velocity update/refresh rate in Hz',
              type=float, metavar='HERTZ',  default=5)
@click.option('-m', '--min-speed', 'minspeed',
              help='Minimum disc speed to read out', type=float,
              show_default=True, default=10.0)
@click.option('--stability-tolerance', 'tolerance', type=float, default=0.1)
@click.option('-B', '--banner', 'showbanner', is_flag=True, default=False,
              help='Display velocity in large letters')
@click.option('--banner-font', 'font', metavar='figlet font', default='banner3',
              help='Font to use for banner. (figlet)')
@click.option('-w','--write', 'recordpath', type=click.Path(),
              metavar='FILEPATH', help='Write session frames to FILEPATH')
@click.option('--debug', 'debug', is_flag=True, default=False,
              help='Print lots of extra debug messages')
@click.option('--tts', 'dotts', is_flag=True, default=False,
              help="Enable text-to-speech")
@click.option('--tts-options', 'ttsoptions', default='rate=125',
              help='TTS engine options')
@click.option('-o', '--output', help='Output speeds to FILEPATH')
@click.option('-T', '--throw-speed', 'throwspeed', is_flag=True, default=False,
              help='Announce speed relative to player (throw speed)')
@click.command(context_settings=dict(show_default=True,
                                     help_option_names=['-h', '--help']))
def main(questhost, refreshrate, minspeed, dotts, showbanner, tolerance, font,
         recordpath, debug, ttsoptions, output, throwspeed, _engine=pyttsx3.init()):
    """ Chronograph for Echo Arena on the Oculus Quest """

    if dotts:
        for prop, val in [s.strip().split('=') for s in ttsoptions.split(',')]:
            prop = prop.strip()
            val = val.strip()
            val = float(val) if val.isdecimal() else val
            _engine.setProperty(prop, val)


    speeds = []
    players = {}
    armed = True

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    apiurl = 'http://{}:6721/session'.format(questhost)
    click.echo('Using Echo Arena API at {}'.format(apiurl))

    if recordpath:
        click.echo('Writing session frames to {}'.format(recordpath))
        log.info('Writing session frames to {}'.format(recordpath))
        recordfp = open(recordpath, 'a')

    if output:
        outputfp = open(output,'a')

    velocities = [0,0,0]

    while True:

        time.sleep(1.0/refreshrate)

        try:
            sessionframe = get_session_frame(apiurl)
            if recordpath:
                recordfp.write(
                    datetime.datetime.now().isoformat() + ' ')
                json.dump(sessionframe, recordfp)
                recordfp.write('\n')
        except requests.exceptions.ConnectionError:
            click.echo('Connection failed. Retrying... ')
            time.sleep(1)
            continue

        if  sessionframe.get('match_type', '').startswith('Social'):
            click.echo('Lobby detected. waiting for match join...')
            time.sleep(3)
            continue

        if 'disc' not in sessionframe:
            click.echo('No disc velocity detected. Match must be started.')
            time.sleep(1)
            continue

        velprev = [round(v,2) for v in velocities]
        velocities = [round(v, 2) for v in sessionframe['disc']['velocity']]

        if velocities != velprev:
            armed = True

        speed = vector_coords_to_speed(velocities)

        log.debug('Current disk speed is {:.1f} m/s'.format(speed))


        speeds = speeds[-10:] + [speed]

        if len(speeds) < 2 or sessionframe['disc']['bounce_count']: continue

        if armed and speed >= minspeed and abs(speed - speeds[-2]) <= tolerance:
            armed = False

            playerdata = _get_player_with_possession(sessionframe)

            relativevelocities = _relative_velocity(
                playerdata.get('velocity', [0,0,0]),
                sessionframe['disc']['velocity'])

            relativespeed = vector_coords_to_speed(relativevelocities)
            player = playerdata.get('name', 'N/A')
            players.setdefault(player, []).append(speed)

            speedmsg = '{:.2f} m/s by {} (thrown at {:.2f} m/s)'.format(
                speed, player or 'N/A', relativespeed)

            click.echo(speedmsg)

            if output:
                outputfp.write(speedmsg + '\n')
                outputfp.flush()

            if showbanner:
                click.echo(Figlet(font=font, width=140).renderText(
                    '{speed:.1f}: {player}'.format(speed=relativespeed if
                                                   throwspeed else speed,
                                                    player=player)))

            if dotts:
                _engine.say('{:.1f}'.format(relativespeed if throwspeed else speed))
                _engine.runAndWait()

def _parse_delimited_options(ttsoptions, _engine):
    """ Parse and return options into key,value pairs. """
    options = []
    for prop, val in [s.strip().split('=') for s in ttsoptions.split(',')]:
        prop = prop.strip()
        val = val.strip()
        val = float(val) if val.isdecimal() else val
        options[prop] = val

    return options


if __name__ =='__main__':
    log = _setup_logging()
    main()
