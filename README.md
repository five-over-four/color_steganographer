# Channel Stenographer
This fun little tool will encode any message you write into the three
colour channels of any image of your choosing. It will do this by altering the
parity of that channels' colour codes, in order of red, green, blue. An even number corresponds with a 0 and an odd one with 1.

Each message begins and ends with an alternating sequence of 24 1s and 0s; 10101010...

Encode your message into `image.png` with the command `python steno.py image.png -e "this is my message."` or from a file `source.txt` by using `python steno.py image.png -i source.txt`

Decode such a message from `encoded.png` with the command `python steno.py encoded.png -d`. If the encoded message is very long, it's recommended you pipe the result into a file with the `>` operator; `python steno.py encoded.png -d > target.txt`.

## Help
    usage: Simple Binary Stenography Tool [-h] [-i TEXTFILE] [-e [MESSAGE]] [-d] filename

    Encode and decode a message into and from the colour channels of an image.

    positional arguments:
    filename              name of the image file.

    options:
    -h, --help            show this help message and exit
    -i TEXTFILE, --input TEXTFILE
                            encode the contents of a text file into the image.
    -e [MESSAGE], --encode [MESSAGE]
                            encode a message into the image file.
    -d, --decode          read a message from the image file.

## Space considerations
As each pixel can contain 3 bits of information and the starting sequence takes up 24 bits (end sequence can be omitted), the maximum number of characters you can encode into an image of size width * height is `(width * height * 3)/8 - 24`, rounded down.

For instance, a 400 x 400 image can hold (400 * 400 * 3)/8 - 24 = 59976 characters, or about 60 kilobytes of information.

Note that compressing the image after encoding will likely destroy the encoded information.

## Included example
I've encoded something into the `example_encoded.png` that you can test the program on. Simply run

`python steno.py example_encoded.png -d > result.txt`

to see what it is.