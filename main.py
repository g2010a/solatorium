from __future__ import division # force integer divisions to return floats instead of truncating
import sys, getopt # For command line arguments
import socket
from time import sleep
import colorsys # For rgb to hls conversions 
import math

# DEFAULTS
UDP_IP="192.168.2.100" #this is the IP of the wifi bridge, or 255.255.255.255 for UDP broadcast
UDP_PORT=8899
INTRA_COMMAND_SLEEP_TIME=1/10 # 100ms=100(1s/1000)

# SOCKET
sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# VARIABLES
DISCO_SLOWER="\x43\x00\x55"
DISCO_FASTER="\x44\x00\x55"
DISCO_ON="\x4D\x00\x55"
SIMPLE_CODE_TEMPLATE="{}\x00\x55"
BRIGHTNESS_CODE_TEMPLATE="\x4E{}\x55"
COLOR_CODE_TEMPLATE="\x40{}\x55"

# AUXILIARY FUNCTIONS
def bcast(cmd):
	sock.sendto(cmd, (UDP_IP, UDP_PORT))

def _get_on_prefix(group):
	return {
		0 : "\x42", # All
		1 : "\x45",
		2 : "\x47",
		3 : "\x49",
		4 : "\x4B"
	}.get(group, "\x42")

def _get_off_prefix(group):
	return {
		0 : "\x41",	# All
		1 : "\x46",
		2 : "\x48",
		3 : "\x4A",
		4 : "\x4C"
	}.get(group, "\x42")

def _get_white_prefix(group):
	return {
		0 : "\xC2",	# All
		1 : "\xC5",
		2 : "\xC7",
		3 : "\xC9",
		4 : "\xCB"
	}.get(group, "\x42")

# Easing functions
def _ease(t, etype='linear'):
	if etype is 'linear':
		return t
	elif etype is 'quad':
		return t**2
	elif etype is 'cubic':
		return t**3
	elif etype is 'sin':
		return 1-math.cos(t*math.pi/2)
	elif etype is 'exp':
		return 2**(10*(t-1))
	elif etype is 'circle':
		return 1-math.sqrt(1-t**2)
	elif etype is 'elastic':
		p=0.45 # elasticity... should be user defineable but oh well
		tau=math.pi*2
		s=p/tau*math.asin(1/t)
#	elif etype is 'back':
	elif etype is 'bounce':
		if t<1/2.75:
			return 7.5625*t*t
		elif t<2/2.75:
			u=t-1.5/2.75
			return 7.5625*u*u+.75
		elif t<2.5/2.75:
			u=t-2.25/2.75	
			return 7.5625*u*u+.9375
		else:
			u=t-2.625/2.75
			return 7.562*u*u+.984375
	return


# SEND COMMANDS IN A NICE, FUNCTION-AL WAY
def disco_slower():
	bcast(DISCO_SLOWER)
def disco_faster():
	bcast(DISCO_FASTER)
def disco_on():
	bcast(DISCO_ON)

# COMPLEX COMMANDS
# e.g. set_brightness(1,0.5)
def turn_on(group):
	bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))

def turn_off(group):
	bcast(SIMPLE_CODE_TEMPLATE.format(_get_off_prefix(group)))

def set_white(group, brightness=False):
	bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))
	sleep(INTRA_COMMAND_SLEEP_TIME)
	bcast(SIMPLE_CODE_TEMPLATE.format(_get_white_prefix(group)))
	if brightness is not False:
		sleep(INTRA_COMMAND_SLEEP_TIME)
		set_brightness(group,brightness)

def set_brightness(group, percent=1):
	# Sends a Group On command followed by brightness command after 100ms
	# we convert percent to the actual scale [2-27]
	scaled=2 + (percent * (27-2))
	brightness=chr(int(round(scaled)))
	bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))
	sleep(INTRA_COMMAND_SLEEP_TIME)
	print"%s, %s"%(percent, int(round(scaled)))
	bcast(BRIGHTNESS_CODE_TEMPLATE.format(brightness))

def set_color(group, percent=1):
	# hue ranges [0-255]
	scaled=percent*255
	hue=chr(int(round(scaled)))
	bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))
	sleep(INTRA_COMMAND_SLEEP_TIME)
	bcast(COLOR_CODE_TEMPLATE.format(hue))

def set_color_rgb(group, rgb=(1,1,1)):
	hls=colorsys.rgb_to_hls(rgb[0], rgb[1], rgb[2])
	# Hue begins at RED in python but at VIOLET in the bulbs,
	# we therefore rotate the value 90 degrees
	# Bulbs more counter-clockwise in the traditional wheel,
	# going from violet to green to red; we therefore invert the value
	hue=hls[0]+(115/360) #
	if(hue>1):
		hue=hue-1
	hue=1-hue # invert the value
	lum=hls[1]
	sat=hls[2]
	print(hue)
	print(lum)
	print(sat)
	if sat < 0.3 or lum > 0.7:
		# basically a white color
		set_white(group)
		sleep(INTRA_COMMAND_SLEEP_TIME)
		set_brightness(group, lum*0.7) # lower the brightness since WHITE is more powerful
	else:
		# set an unfortunately very saturated color
		set_color(group, hue)
		sleep(INTRA_COMMAND_SLEEP_TIME)
		set_brightness(group)#, lum)

def white_sunrise(group, duration=60*30): #default duration is 30 mins
	set_white(group)
	set_brightness(group, 0)
	for x in range(0,100):
		set_brightness(group, _ease(x/100, 'cubic'))
		sleep(max(duration/100, INTRA_COMMAND_SLEEP_TIME))

white_sunrise(1, 10)
sleep(3)
set_brightness(1,0.5)