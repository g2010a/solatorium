SOLATORIUM
==========
Simulate sunrises using wifi-enabled lightbulbs.

This is only a proof-of-concept library that works with milight/limitlessled lamps and a raspberry pi. Pre-assembled "wake-up" sunrise-simuulating lamps already exist but are rather expensive for the functionality they offer... for the same price, a raspberry pi and cheap wifi-enabled light bulbs can be purchased and custom sunrise simlations created. 

The choice of lightbulbs was based on price; milight/limitlessled bulbs can only receive commands but provide no feedback about their status (e.g. is the lamp already on? how bright is it? what color is rendered?) and are not suitable for complex setups, but are perfectly fine for simple applications where lamp state is irrelevant, such as a wake-up lamp.
 
The eventual goal of this library is to also replicate lighting conditions based on meteorological information from other locations, to simulate the brightening and dimming of light on a cloudy day, and to mimic other illumination sources such as candles. 

Installation
============
Ensure raspberry pi has the correct timezone set up: run tzconfig

1. sudo apt-get install pip
2. sudo pip install pyephem

Currently, there is only a simple file to which arguments can be passed:

python milight.py -g 3 -d 300 white_sunrise

Type milight.py --help for more information.

Timeone setup is critical for CRON events; sometimes the Raspberry Pi will execute CRON commands Greenwich time although the date command returns time in your timezone. Use sudo dpkg-reconfigure tzdata to set up the system (as opposed to user) timezone.
