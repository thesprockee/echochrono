# echochrono
Oculus Quest API chronograph that prints and announces the disc throw/shot
velocities


## Installation

```
pip3 install -r ./requirements.txt
```

## Enabling API Access

This script communicates with the Echo Arena API on the Oculus Quest. To enable the API go to *Settings* then set **Enable API Access** to *Enable*. This will open tcp port 6721 on the Quest. Use the Quest's IP address as the first argument to the script.

### Usaage

```
./discvelocity.py <QUEST IP>
```

