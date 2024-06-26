# This Project
This tool will encode any message you write into the three
colour channels of any image of your choosing. It will do this by altering the
remainder under modular arithmetic of that channels' colour codes, in order of red, green, blue.

Encode your message into `image.png` with the command `python stegano.py image.png -t "this is my message."` or from a file `source.txt` by using `python stegano.py image.png -i source.txt`

Decode such a message from `encoded.png` with the command `python stegano.py encoded.png -d`. If the encoded message is very long, it's recommended you pipe the result into a file with the `>` operator; `python stegano.py encoded.png -d > target.txt`.

---

# Encoding Options

### Bit depth with `-b` or `--bitlevel` (default=1)

This option determines how many bits of each colour of an encoded pixel are used 
to store information rather than colour data. Default is $1$, maximum $8$. 
This is mostly unnoticeable until `-b 3`, after which the generated noise will start to be more visible, though random.

### Skip pixels with `-s` or `--skipping` (default=1)

You can decide to encode the data into only every $N\text{th}$ pixel by using the flag `-s N` or `--skipping N`. 
This will of course cut the storage capacity of the image to $\frac{1}{N}$ of the original. Default is 1, 
which uses every pixel in sequence. `-s 0` attempts to spread the data as evenly as possible across the image, 
finding the largest skipping number that can still fit all of the data in.

### Offset encoding with `-o` or `--offset` (default=0)

`-o K` or `--offset K` will begin encoding the data at the $(K + 1)\text{th}$ pixel rather than the first, from the top left down. Default is 0, no maximum.

> To encode `textfile.txt` into `image.png` with bitlevel=3, skipping=15, offset=200:
> ```
>python stegano.py image.png -i textfile.txt -b 8 -s 15 -o 20
> ```

The program will attempt to automatically detect the message, but you can override that by using any of the flags -b, -s, -o: `python stegano.py encoded.png -d -b 4 -s 3` will attempt to decode without searching for a message. Note that the automatic detection cannot find messages that use an offset, as this would increase the time-complexity of the algorithm by essentially an arbitrary factor.

### Encoding multiple messages within one image
With the skipping number $N$, it is possible to encode $N$ separate messages by cycling through all offsets $0$ to $(N-1)$ (or $1$ to $N$), courtesy of modular arithmetic. The automatic decoding feature will not work for images with multiple messages and the analysis will likely find many false positives.

Example: to encode *two* messages, `file1.txt` and `file2.txt`, use 
```
python stegano.py image.png -i file1.txt -s 2 -o 0
python stegano.py image.png -i file1.txt -s 2 -o 1
```
and decode using 
```
python stegano.py encoded.png -d -s 2 -o 0
python stegano.py encoded.png -d -s 2 -o 1
```

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
Each pixel in the image contains three colours, red, green, and blue. Their values range from $0$ to $255$ ($2^8$ values, $8$ bits). By adjusting
each colour value to the nearest value (random direction) that corresponds with a binary representation of your text data, we're able to
encode bitlevel bits of information in each colour channel of each pixel under $\text{mod } 2^{\text{bitlevel}}$ modular arithmetic.

For example: at bitlevel = $3$, we're working with $2^3 = \text{mod } 8$ arithmetic. If our character is an 'a', that is, $97$ or $1100001$, the first $3$ bits
are $110$, or $6$, we adjust the first colour channel value to the nearest value whose remainder under division by $8$ is $6$, thereby encoding the bits.
This changes the least significant $3$ bits to store the information and leaves $5$ bits of colour data.
This naturally introduces some noise, but is completely invisible at low bitlevels (up to about $\text{3--4}$). At $8$ bits, the entire underlying image is lost, as $0$ bits of colour information are retained of each channel.

* N.B. *All* printable characters can be represented with 7 bits, and therefore the only functional difference between `-b 8` and `-b 7` is that the former destroys more of the image.

### Initialisation sequence
The first $8$ pixels of any encoding are used for a sequence of alternating bits to identify the beginning of a message. The *second* $8$ pixels are used to encode length information about the message, so the program knows where to stop. If you encode an image with bitlevel $8$, you'll see this as $8$ gray/white pixels in the top left, followed by $8$ mostly black and then a coloured pixel or two, as below.

![](./resources/encoding_pixels.png)

## Space considerations
### Calculating required image size
Given $N$ bytes of text data, the number of pixels this requires is exactly $$\frac{8N}{3\cdot\text{bitlevel}} + 16$$ The $+ 16$ comes from the message initialisation sequence. For a square image, then, one needs a $$\sqrt{\frac{8N}{3\cdot\text{bitlevel}} + 16}$$ wide and tall image, dimensions rounded up. For, say, $15\text{kB}$ at $\text{bitlevel}=3$, this means a $116 \times 116$ picture.

### Calculating image storage capacity
Given a $W \times H$ image, the data storage capacity without the initialisation sequences is 
$\frac{3WH\cdot\text{bitlevel}}{\text{skipping}}$ bits. Subtracting from it the initial sequence, $3\cdot16\cdot\text{bitlevel}\cdot\text{skipping}$ bits, we're left with

$$\frac{3\cdot\text{bitlevel}}{8}\left\lbrack\frac{W\cdot H}{S} - 16\cdot S - \text{offset}\right\rbrack$$

bytes of storage. This way, for instance, the absolute maximum storage capacity of a 400 x 400 image is about 60kB, destroying all the colour information.

***Note that compressing the image after encoding will likely destroy the encoded information as it relies on precise numerical values.***

## Included examples
I've encoded something into the `./resources/example_encoded.png` that you can test the program on. Simply run `python stegano.py example_encoded.png -d > result.txt` to see what it is.

![Hmm...](./resources/pgp.png)