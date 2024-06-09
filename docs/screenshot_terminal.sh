#!/bin/bash

# # enough entropy need too many key strokes
# dd if=/dev/random of=seed_file count=64 bs=1 > /dev/null
rm seed_file

CLASSNAME=$(head -c 6 /dev/urandom | base64 | tr -cd [:alnum:])

# gruvbox colors
colors=(
    '-xrm' '*.color0: #282828'
    '-xrm' '*.color1: #cc241d'
    '-xrm' '*.color2: #98971a'
    '-xrm' '*.color3: #d79921'
    '-xrm' '*.color4: #458588'
    '-xrm' '*.color5: #b16286'
    '-xrm' '*.color6: #689d6a'
    '-xrm' '*.color7: #a89984'
    '-xrm' '*.color8: #928374'
    '-xrm' '*.color9: #fb4934'
    '-xrm' '*.color10:#b8bb26'
    '-xrm' '*.color11:#fabd2f'
    '-xrm' '*.color12:#83a598'
    '-xrm' '*.color13:#d3869b'
    '-xrm' '*.color14:#8ec07c'
    '-xrm' '*.color15:#ebdbb2'
    '-xrm' '*.foreground:#ebdbb2'
    '-xrm' '*.background:#282828'
)

urxvt -hold "${colors[@]}" +is -g 150x41 -b 0 +sb -name $CLASSNAME -fn "xft:FiraCode Nerd Font:pixelsize=20"  -e python example.py &

RXVTWINDOWID=$(xdotool search --sync --classname "$CLASSNAME")

xdotool type -window $RXVTWINDOWID 'add_entropy timestamp'
xdotool key -window $RXVTWINDOWID Return
for i in {1..10}; do
    for i in {1..32}; do
        xdotool type -window $RXVTWINDOWID a
    done
done
xdotool key -window $RXVTWINDOWID ctrl+c

xdotool type -window $RXVTWINDOWID add_entropy
xdotool key -window $RXVTWINDOWID Return
for i in {1..26}; do
    xdotool type -window $RXVTWINDOWID a
done
xdotool key -window $RXVTWINDOWID ctrl+c

xdotool key -window $RXVTWINDOWID ctrl+l
xdotool type -window $RXVTWINDOWID random
xdotool key -window $RXVTWINDOWID Return
xdotool type -window $RXVTWINDOWID add_entropy
xdotool key -window $RXVTWINDOWID Return
xdotool type -window $RXVTWINDOWID asdfjkl
xdotool key -window $RXVTWINDOWID ctrl+c
xdotool type -window $RXVTWINDOWID random
xdotool key -window $RXVTWINDOWID Return

sleep 0.1

import -window $RXVTWINDOWID  /tmp/out.png

# https://imagemagick.org/script/command-line-options.php#trim
# you need a more recent version than 'ImageMagick 6.9.11-60 Q16 x86_64 2021-01-25' for the trim:edges
convert  /tmp/out.png -define trim:edges=south -trim $(dirname $0)/screenshot.png

kill %1
