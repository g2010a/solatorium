#
# Macros to control milight/limitlessled lamps
#

from __future__ import division # force integer divisions to return floats instead of truncating
import sys, argparse        # command line arguments
import socket               # socket communications
from time import sleep      # sleep without doing anything for a while
import colorsys             # rgb to hls conversions 
import math                 # mathematical operations
import random               # generate random numbers

# DEFAULTS
UDP_IP="192.168.2.100" #this is the IP of the wifi bridge, or 255.255.255.255 for UDP broadcast
UDP_PORT=8899
INTRA_COMMAND_SLEEP_TIME=1/10 # 100ms=100(1s/1000)

# ARGUMENTS FROM COMMANDLINE
parser = argparse.ArgumentParser()
parser.add_argument("macro", help="the macro to execute",
                    choices=[
                        "on", 
                        "off",
                        "brightness",
                        "set_white",
                        "set_color",
                        "torch",
                        "white_sunrise"
                     ])
parser.add_argument("-g", "--group", help="lamp group receiving the command", type=int, choices=[0,1,2,3,4])
parser.add_argument("-d", "--duration", type=int, help="(seconds) if applicable, how long a macro should last")
parser.add_argument("--debug", help="shorten transition times for debugging purposes", action="store_true")
parser.add_argument("-p", "--param", help="Additional argument for special functions (e.g. color string for set_color, wind strength for torch)")
parser.add_argument("-v", "--verbosity", action="count", default=0)
args = parser.parse_args()

# SOCKET
sock=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# STATIC GLOBALS
DISCO_SLOWER="\x43\x00\x55"
DISCO_FASTER="\x44\x00\x55"
DISCO_ON="\x4D\x00\x55"
SIMPLE_CODE_TEMPLATE="{}\x00\x55"
BRIGHTNESS_CODE_TEMPLATE="\x4E{}\x55"
COLOR_CODE_TEMPLATE="\x40{}\x55"

# AUXILIARY FUNCTIONS
# Logs a statement depending on verbosity
def logger(verbosity, statement):
    if (args.verbosity >= verbosity):
        print statement
    
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
        0 : "\x41",    # All
        1 : "\x46",
        2 : "\x48",
        3 : "\x4A",
        4 : "\x4C"
    }.get(group, "\x42")

def _get_white_prefix(group):
    return {
        0 : "\xC2",    # All
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
#    elif etype is 'back':
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
def turn_on(group=None):
    if group is None:
        group = args.group
    logger(1, "Turn group %s on"%(group))
    bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))

def turn_off(group=None):
    if group is None:
        group = args.group
    logger(1, "Turn group %s off"%(group))
    bcast(SIMPLE_CODE_TEMPLATE.format(_get_off_prefix(group)))

def set_white(group=None, brightness=False):
    if group is None:
        group = args.group
    bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))
    sleep(INTRA_COMMAND_SLEEP_TIME)
    bcast(SIMPLE_CODE_TEMPLATE.format(_get_white_prefix(group)))
    if brightness is not False:
        sleep(INTRA_COMMAND_SLEEP_TIME)
        set_brightness(group,brightness)

def set_brightness(group=None, percent=1):
    # Sends a Group On command followed by brightness command after 100ms
    # we convert percent to the actual scale [2-27]
    if group is None:
        group = args.group
    scaled=2 + (percent * (27-2))
    brightness=int(round(scaled))
    logger(2, "Setting brightness of group %s to %s%%, scaled [2-27]: %s"%(group, percent*100, brightness))
    
    bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))
    sleep(INTRA_COMMAND_SLEEP_TIME)
    bcast(BRIGHTNESS_CODE_TEMPLATE.format(chr(brightness)))

def set_color(group=None, percent=1):
    # hue ranges [0-255]
    if group is None:
        group = args.group
    scaled=percent*255
    hue=chr(int(round(scaled)))
    bcast(SIMPLE_CODE_TEMPLATE.format(_get_on_prefix(group)))
    sleep(INTRA_COMMAND_SLEEP_TIME)
    bcast(COLOR_CODE_TEMPLATE.format(hue))

def set_color_rgb(group=None, rgb=(1,1,1)):
    if group is None:
        group = args.group
    if args.param is not None:
        rgb = map(float, args.param.split(','))
    hls=colorsys.rgb_to_hls(rgb[0], rgb[1], rgb[2])
    # Hue begins at RED in python but at VIOLET in the bulbs,
    # we therefore rotate the value to more-or-less match.
    hue=hls[0]+(115/360) # Rotate hue
    
    if(hue>1):
        hue=hue-1
    
    # Bulbs move counter-clockwise in the traditional wheel,
    # going from violet to green to red; we therefore invert the value
    hue=1-hue # invert the value
    
    lum=hls[1]
    sat=hls[2]
    logger(2, "HSL: %s, %s, %s"%(hue, lum, sat))
    if sat < 0.3 or lum > 0.75:
        # basically a white color
        logger(2, "Too luminous or desaturated, switching to white")
        set_white(group)
        sleep(INTRA_COMMAND_SLEEP_TIME)
        set_brightness(group, lum*0.65) # lower the brightness since WHITE is more powerful
    else:
        # set an unfortunately very saturated color
        set_color(group, hue)
        sleep(INTRA_COMMAND_SLEEP_TIME)
        set_brightness(group)#, lum)

def white_sunrise(group=None):
    # Sets lamp color to white and gradually increases the brightness to simulate
    # a sunrise
    #
    # @param {group} A lamp group to affect
    
    if group is None:
        group = args.group
    if args.debug is True:
        duration=10
    else:
        if args.duration is None:
            duration = 60*5             # default duration is 5 minutes
        else:
            duration = args.duration
    
    logger(1, "Starting white sunrise in group %s with duration %s (seconds)"%(group, duration))
    set_white(group)
    sleep(INTRA_COMMAND_SLEEP_TIME)
    set_brightness(group, 0)
    sleep(INTRA_COMMAND_SLEEP_TIME)
    
    # Short durations may require less than 100 steps due to the INTRA_COMMAND_SLEEP_TIME
    # so let's calculate how many steps we need
    min_duration = 100*3*INTRA_COMMAND_SLEEP_TIME
    logger(1, min_duration)
    if duration < min_duration:
        step = int(round(min_duration / duration))
        total_steps = 100/step
        logger(2, "Duration (%s) is shorter than min_duration (%s), setting step to %s (total_steps=%s)"%(duration, min_duration, step, total_steps))
    else:
        step = 1
        total_steps = 100
    
    # Send commands
    for x in range(0,100,step):
        logger(3, "Step %s"%(x))
        set_brightness(group, _ease(x/100, 'sin'))
        sleep(max(duration/total_steps, INTRA_COMMAND_SLEEP_TIME))
        
def torch(group=None, wind=5): 
    # Simulates a flickering torch
    if group is None:
        group = args.group
    if args.param is not None:
        wind = args.param
    
    def flicker():
        return max(random.random() / WIND, INTRA_COMMAND_SLEEP_TIME)
        
    def brightness():
        return random.randint(5,100)
    
    set_color_rgb(group, (1,0.5,0))
    while True:
        set_brightness(group, brightness()/100)
        sleep(flicker())
    
# MAIN LOGIC
commands = {
    "on"            : turn_on,
    "off"           : turn_off,
    "brightness"    : set_brightness,
    "set_white"     : set_white,
    "set_color"     : set_color_rgb,
    "torch"         : torch,
    "white_sunrise" : white_sunrise
}
commands[args.macro]()  # Execute desired macro