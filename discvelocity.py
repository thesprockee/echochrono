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

import logging

log = logging.getLogger(__name__)


def _setup_logging():
    """ Configure loggers """
    FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
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
        log.warning('No session. In lobby?')
        return {}
    try:
        return json.loads(r.text)
    except json.decoder.JSONDecodeError as e:
        log.error('Invalid json')
        log.debug('JSON decode error: {}'.format(e))
        click.echo('Invalid json.')
        return {}

def _get_player_with_possession(frame):
    """ Return the name of the player with posession of the disc """
    for t in frame['teams']:
        for p in t.get('players',[]):
            if p.get('possession'):
                return p['name']
    return None


class Chronograph(object):

    def __init__(self, recordpath=None,):
        self.speeds = []
        self.players = {}
        self.armed = True

    def loop(self, object):
       Screen.wrapper(self.display_loop)

    def display_loop(self, screen):
        while True:
            for n, playerspeed in enumerate(self.players):

                screen.print_at(
                    FigletText("14.3", font='doh'),
                    n, 0,
                )

                screen.refresh()




@click.argument('questhost', metavar='<QUEST IP>')
@click.option('-r', '--refresh-rate', 'refreshrate', help='Disc velocity update/refresh rate in Hz',
              type=float, metavar='HERTZ',  default=5)
@click.option('-m', '--minimum-speed', 'minspeed',
              help='Minimum disc speed to read out', type=float,
              show_default=True, default=10.0)
@click.option('--stability-tolerance', 'tolerance', type=float, default=0.1)
@click.option('--no-tts', 'notts', is_flag=True, default=False,
              help='Enable/Disable text-to-speech')
@click.option('--no-banner', 'nobanner', is_flag=True, default=False,
              help='Enable/Disable displaying velocity in large letters')
@click.option('--font', help='Figlet font to display speeds with',
              metavar='font name', default='doh')
@click.option('-R','--record', 'recordpath', type=click.Path(),
              metavar='FILEPATH', help='Record session frames to FILEPATH')
@click.option('--banner-font', 'font', metavar='figlet font', default='doh',
              help='figlet font to use for banner')
@click.option('--debug', 'debug', is_flag=True, default=False,
              help='Print lots of extra debug messages')
@click.option('--tts-options', 'ttsoptions', default='rate=125',
              help='TTS engine options')
@click.command(context_settings=dict(show_default=True,
                                     help_option_names=['-h', '--help']))
def main(questhost, refreshrate, minspeed, notts, nobanner, tolerance, font,
         recordpath, debug, ttsoptions, _engine=pyttsx3.init()):
    """ Chronograph for Echo Arena on the Oculus Quest """

    if not notts:
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

    apiurl = 'http://{}:6721/session'.format(questhost)
    click.echo('Using Echo Arena API at {}'.format(apiurl))

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
            click.echo('Lobby detected. waiting for match start...')
            time.sleep(3)
            continue

        if 'disc' not in sessionframe:
            click.echo('No disc velocity found in session frame.'
                       " Waiting for match start?")
            time.sleep(1)
            continue

        speed = vector_coords_to_speed(sessionframe['disc']['velocity'])

        log.debug('Current disk speed is {:.1f} m/s'.format(speed))
        speeds = speeds[-10:] + [speed]

        if len(speeds) < 3:
            continue

        if speed < speeds[-2]:
            armed = True

        if armed and sessionframe['disc']['bounce_count'] == 0 \
                and speed >= minspeed \
                and abs(speed - speeds[-2]) <= tolerance:

            player = _get_possession(sessionframe)
            players.setdefault(player, []).append(speed)

            click.echo('{:.1f} m/s by {}'.format(speed, player))
            if not nobanner:
                click.echo(Figlet(font='big').renderText(
                    '{speed:.2f}: {player}'.format(speed=speed, player=player)))

            if not notts:
                _engine.say('{:.1f}'.format(speed))
                _engine.runAndWait()
                armed = False

        #click.echo(print_big('{:.1f}'.format(speed)), color='green')


if __name__ =='__main__':
    main()
