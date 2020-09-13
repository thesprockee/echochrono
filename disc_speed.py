#!/usr/bin/env python3
import requests
import json
import time
import math
import datetime
from pyfiglet import Figlet
import click

import pyttsx3



engine = pyttsx3.init()

def vel2speed(vel):
    return round(math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2),2)



def get_telemetry():
    r = requests.get('http://10.0.1.113:6721/session')
    try:
        j = json.loads(r.text)
    except json.decoder.JSONDecodeError:
        print('Invalid json.')
        return {}
    return j

def parse_disc_speed(telemetry):
    velocity = telemetry['disc']['velocity']
    speed = vel2speed(velocity)
    return speed

def print_big(text, font='doh'):
    f = Figlet(font=font)
    return f.renderText(str(text))


def speak(text):
    engine.say(text)
    engine.runAndWait()

@click.option('-r', '--rate', help='refresh rate', type=float, default=0.5)
@click.option('-m', '--minjspeed', 'minspeed',
              help='Minimum disc speed to detect a shot', type=float, default=7)
@click.option('-l', '--log-frames', 'logframes', is_flag=True, default=True)
@click.command()
def main(rate, minspeed, logframes):
    if logframes:
        print ('Logging frames')
        framelog = open(datetime.datetime.now().strftime('%Y%m%d-%H:%M:%S.json'), 'w')
    recent = []
    while True:
        time.sleep(rate)
        try:
            telemetry = get_telemetry()
            if logframes:
                json.dump(telemetry, framelog)

        except requests.exceptions.ConnectionError:
            print('Connection failed. Retrying... ')
            continue


        if 'disc' not in telemetry:
            print('No disc telemetry')
            continue

        if telemetry['disc']['bounce_count'] > 0:
            continue
        speed = parse_disc_speed(telemetry)
        recent = recent[-10:] + [speed]

        if len(recent) < 3:
            continue

        accel = recent[-1] - recent[-2]
        delta = speed - min(recent[-5:-1])

        if delta > minspeed:
            click.echo()
            click.echo(print_big('{:.1f}'.format(speed)), color='green')
            speak('{:.1f}'.format(speed))
        #click.echo(print_big('{:.1f}'.format(speed)), color='green')


if __name__ =='__main__':
    main()
