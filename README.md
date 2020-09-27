# echochrono
Oculus Quest API chronograph that prints and announces the disc throw/shot
velocities

*NOTICE: Only the white disc in public and private matches report velocities in
the API. Lobby and Personal discs DO NOT report velocities.*
## Installation

```
pip3 install -r ./requirements.txt
```
## Enabling API Access

This script communicates with the Echo Arena API on the Oculus Quest. To enable the API go to *Settings* then set **Enable API Access** to *Enable*. This will open tcp port 6721 on the Quest. Use the Quest's IP address as the first argument to the script.

### Usage

```
./discvelocity.py <QUEST IP>
```

### Private Arena Training Mode

To use this script in a private arena, The match clock must have been started
at least once.

To enable disc velocity in a private arena training mode, follow this
procedure:

1. Hit *"Team Ready"* on the arena console
2. Wait for clock to start counting down
3. Hit *Restart* on the arena console


