# Colour Steganographer
This fun little tool will encode any message you write into the three
colour channels of any image of your choosing. It will do this by altering the
remainder under modular arithmetic of that channels' colour codes, in order of red, green, blue.

Encode your message into `image.png` with the command `python stegano.py image.png -t "this is my message."` or from a file `source.txt` by using `python stegano.py image.png -i source.txt`

Decode such a message from `encoded.png` with the command `python stegano.py encoded.png -d`. If the encoded message is very long, it's recommended you pipe the result into a file with the `>` operator; `python stegano.py encoded.png -d > target.txt`.

## Encoding tweaks
To use more bits of each colour for the message, use the `-b` or `--bitlevel` flag, with numbers 1-8, 1 being the least bits (most discreet) and 8 being the most extreme (0 bits for colour information!). To offset the encoding by N pixels, use the `-o N` or `--offset N` flag. To skip all but every Nth pixel (up -> down, then left -> right), use the `-s N` or `--skipping N` flag. `-s 0` will attempt to populate the image as evenly as possible.

As an example, to encode the file `source.txt` into `example.png`, storing 4 bits per pixel, skipping all but every 3rd pixel, and starting on the 17th pixel, you'd use the command

`python stegano.py -i source.txt -b 4 -s 3 -o 17`.

The program will attempt to automatically detect the message, but you can override that by using any of the flags -b, -s, -o: `python stegano.py encoded.png -d -b 4 -s 3` will decode without searching for a message. Useful if offsets are used, as the detection won't look for those (too time-complex.)

### Encoding multiple messages within one image
With the skipping number N, it is possible to encode N separate messages by cycling through all integer offsets 0 - (N-1) (or 1 - N), courtesy of modular arithmetic. The automatic decoding feature will not work for images with multiple messages and the analysis will likely find many false positives.

Example: to encode *two* messages, `file1.txt` and `file2.txt`, use `python stegano.py image.png -i file1.txt -s 2 -o 0` and `python stegano.py image.png -i file1.txt -s 2 -o 1` (with optional bit levels) and decode using `python stegano.py encoded.png -d -s 2 -o 0` and `python stegano.py encoded.png -d -s 2 -o 1`. The downside is the reduction of storage per offset channel, you'll have to calculate the storage manually.

## Help
    usage: Steganography Tool [-h] [-i TEXTFILE] [-t MESSAGE] [-d] [-b BITS_PER_PIXEL] [-s N] [-o K] [-a] filename

    Encode and decode a message into and from the colour channels of an image.

    positional arguments:
    filename              Name of an image file.

    options:
    -h, --help            show this help message and exit
    -i TEXTFILE, --input TEXTFILE
                            Contents of this file will be encoded into the image.
    -t MESSAGE, --type MESSAGE
                            Type directly to encode a message into the image file.
    -d, --decode          Read a message from the image file.
    -b BITS_PER_PIXEL, --bitlevel BITS_PER_PIXEL
                            Store n bits per pixel. 1-8. Higher = more storage, less discreet, more colour data lost.
    -s N, --skipping N    Encode to every Nth pixel. 0 to populate the image evenly.
    -o K, --offset K      Start encoding at the Kth pixel, allows for multiple messages per image, assuming you use the same skipping number (>1).
    -a, --analyze         Tries to automatically find an encoded message and its settings.

## Method of steganography used
Each pixel in the image contains three colours, red, green, and blue. Their values range from 0 to 255 (2^8 values, 8 bits). By adjusting
each colour value to the nearest value (random direction) that corresponds with a binary representation of your text data, we're able to
encode bit_level bits of information in each colour channel of each pixel in mod 2^bit_level modular arithmetic.

For example: at bit_level = 3, we're working with 2^3 = mod 8 arithmetic. 0 = "000", 1 = "001", ..., 6 = "110", and 7 = "111". This would
take the least significant 3 bits from the colour channel to what is essentially random-ish noise and leave 5 to the actual colour data.
This naturally introduces some noise, but is completely invisible at low bit_levels (up to about 3-4). At 8 bits, the entire underlying image is lost, as 0 bits of colour information are retained in each channel.

* N.B. *All* printable characters can be represented with 7 bits, and therefore the only functional difference between `-b 8` and `-b 7` is that the former destroys more of the image.

### Initialisation sequence
The first 8 pixels of any encoding are used for a sequence of alternating bits to identify the beginning of a message. The second 8 pixels are used to encode length information about the message, so the program knows where to stop. If you encode an image with bit_level 8, you'll see this as 8 gray/white pixels in the top left, followed by 8 mostly black and then a coloured pixel or two, as below.

![](./resources/encoding_pixels.png)

## Space considerations
### Calculating required image size
Given N bytes of text data, the number of pixels this requires is exactly (N * 8) / (3 * bit_level) + 16. The + 16 comes from the message initialisation sequence. For a square image, then, one needs a sqrt((N * 8) / (3 * bit_level) + 16) wide and tall image, dimensions rounded up. For, say, 15kB at bit_level=3, this means a 116 x 116 picture.

### Calculating image storage capacity
Given a W x H image, the data storage capacity without the 10101010-sequences is W * H * 3 * bit_level / skipping bits. Subtracting from it the initial sequence,
exactly 3 * 16 * bit_level * skipping bits, so we're left with

`(W * H * 3 * bit_level / skipping - 3 * 16 * bit_level * skipping)/8` bytes of storage.

Offsets aren't taken into account, but generally you'd only use offset < skipping. This way, for instance, the absolute maximum storage capacity of a 400 x 400 image is about 480kB, destroying all the colour information.

* Note that compressing the image after encoding will likely destroy the encoded information as it relies on precise numerical values.

## Included examples
I've encoded something into the `./resources/example_encoded.png` that you can test the program on. Simply run `python stegano.py example_encoded.png -d > result.txt` to see what it is.

![Hmm...](./resources/pgp.png)