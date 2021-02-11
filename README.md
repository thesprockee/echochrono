# echochrono
Oculus Quest API chronograph that prints and announces the disc throw/shot
velocities

*NOTICE: Only the white disc in public and private matches report velocities in
the API. Lobby and Personal discs DO NOT report velocities.*
## Installation

1. Install Python 3
2. Run ```pip3 install -r ./requirements.txt```

## Enabling API Access

This script communicates with the Echo Arena API on the Oculus Quest. To enable
the API go to *Settings* then set **Enable API Access** to *Enable*. This will
open TCP port 6721 on the Quest. Use the Quest's IP address as the first
argument to the script.

## Usage

```
./discvelocity.py <QUEST IP>
```

To see available options run ```./discvelocity.py --help```

### Example Usage

To poll a quest at 192.168.1.1.140 30 times a second, read out throws over 8
m/s via text-to-speech and display the speed in large letters on the screen:

```./discvelocity.py 192.168.1.140 --min-speed 8.0 --refresh-rate 30 --relative --tts --banner```

### Private Arena Training Mode

To use this script in a private arena, The match clock must have been started
at least once.

To enable disc velocity in a private arena training mode, follow this
procedure:

1. Hit *"Team Ready"* on the arena console
2. Wait for clock to start counting down
3. Hit *Restart* on the arena console


