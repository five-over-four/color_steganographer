# Colour Steganographer
This fun little tool will encode any message you write into the three
colour channels of any image of your choosing. It will do this by altering the
remainder under modular arithmetic of that channels' colour codes, in order of red, green, blue.

Encode your message into `image.png` with the command `python stegano.py image.png -t "this is my message."` or from a file `source.txt` by using `python stegano.py image.png -i source.txt`

Decode such a message from `encoded.png` with the command `python stegano.py encoded.png -d`. If the encoded message is very long, it's recommended you pipe the result into a file with the `>` operator; `python stegano.py encoded.png -d > target.txt`.

## Encoding tweaks
To use more bits of each colour for the message, use the `-b` or `--bitlevel` flag, with numbers 1-8, 1 being the least bits (most discreet) and 8 being the most extreme (0 bits for colour information!). To skip all but every Nth pixel (up -> down, then left -> right), use the `-s` or `--skipping` flag.

For instance, to encode the file `source.txt` into `example.png`, storing 4 bits per pixel, and skipping all but every 3rd pixel, you'd use the command

`python stegano.py -i source.txt -b 4 -s 3`

## Help
    usage: Simple Binary Steganography Tool [-h] [-i TEXTFILE] [-t MESSAGE] [-b BITS_PER_PIXEL] [-s N] [-d] [-a] filename

    Encode and decode a message into and from the colour channels of an image.

    positional arguments:
    filename              Name of the image file.

    options:
    -h, --help            show this help message and exit
    -i TEXTFILE, --input TEXTFILE
                            Encode the contents of a text file into the image.
    -t MESSAGE, --typemessage MESSAGE
                            Type directly to encode a message into the image file.
    -b BITS_PER_PIXEL, --bitlevel BITS_PER_PIXEL
                            Store n bits per pixel. Higher = less discreet, as the colours are represented in fewer bits.
    -s N, --skipping N    Skip all but every Nth pixel in the encoding process.
    -d, --decode          Read a message from the image file.
    -a, --analyze         Gives storage constraints for the image.

## Method of steganography used
Each pixel in the image contains three colours, red, green, and blue. Their values range from 0 to 255 (2^8 values, 8 bits). By adjusting
each colour value to the nearest value (random direction) that corresponds with a binary representation of your text data, we're able to
encode bit_level bits of information in each colour channel of each pixel in mod 2^bit_level modular arithmetic.

For example: at bit_level = 3, we're working with 2^3 = mod 8 arithmetic. 0 = "000", 1 = "001", ..., 6 = "110", and 7 = "111". This would
take the least significant 3 bits from the colour channel to what is essentially random-ish noise and leave 5 to the actual colour data.
This naturally introduces some noise, but is completely invisible at low bit_levels (up to about 4). At 8 bits, the entire underlying image is lost, as
0 bits of information are retained of it.

## Space considerations
As each pixel can contain 3 * bit_level bits of information and the starting sequence takes up 24 bits (end sequence can be omitted), the maximum number of characters you can encode into an image of size width * height is `(width * height * 3 * bit_level)/8 - 24`, rounded down.

For instance, at bit_level 1, a 400 x 400 image can hold (400 * 400 * 3)/8 - 24 = 59976 characters, or about 60 kilobytes of information.

Note that compressing the image after encoding will likely destroy the encoded information as it relies on precise numerical values.

## Included example
I've encoded something into the `example_encoded.png` that you can test the program on. Simply run `python stegano.py example_encoded.png -d > result.txt` to see what it is.