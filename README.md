# Channel Stenographer
This fun little tool will encode any message you write into one of the three
colour channels of any image of your choosing. It will do this by altering the
parity of that channel's colour code. An even number corresponds with a 0 and an odd one with 1.

Each message begins and ends with an alternating sequence of 24 1s and 0s; 10101010...

Encode `image.png` into the channel `colour` with the command `python steno.py image.png -e "this is my message." -c "colour"` with an optional channel flag `-c` (default is red) taking arguments "red", "green", and "blue".

Decode such a message from `encoded.png` from the channel `colour` with the command `python steno.py encoded.png -d -c "colour"`

## Help
    usage: Simple Binary Stenography Tool [-h] [-e MESSAGE] [-d] [-c COLOUR] [-s] filename

    Encode and decode a message into and from one of the colour channels of an image.     

    positional arguments:
    filename              name of the image file.

    options:
    -h, --help            show this help message and exit
    -e MESSAGE, --encode MESSAGE
                            encode a message into the image file.
    -d, --decode          read a message from the image file.
    -c COLOUR, --channel COLOUR
                            red/green/blue
    -s, --scramble        remove any message from given channel.

## TODO

* I'll add an optional padding flag that will allow you to begin a message at an arbitrary position in the image.

* Perhaps some more complex methods of staggering the bits, but I may not do this.