"""
This CLI-script encodes arbitrary text data into the colour channels of an image.
"""

from random import choice
from itertools import product
import argparse
from math import ceil
from PIL import Image

#   #   #   #   #   #   #   #   #   #   #   #   #   # #
# Basic bin -> ascii and ascii -> bin functions here. #
#   #   #   #   #   #   #   #   #   #   #   #   #   # #

def to_bin(s: str):
    """
    Convert each character in the string into an 8-bit sequence and concatenate.

    'hello' is converted to '0110100001100101011011000110110001101111'.
    """
    return "".join([ str(bin(ord(char)))[2:].zfill(8) for char in s])

def decode_byte(b: str) -> str:
    """
    Returns string representation of a byte into a character.

    '11000001' converts to 'a'.
    """
    return chr(int(bytes(b, "utf-8"), 2))

def bit_combinations(power=1):
    """
    Returns the set ["0", "1"]^power, elements concatenated.

    Generates ["0", "1"] with power==1
    Generates ["00", "01", "10", "11"] with power==2
    And so forth.
    """
    combos = product(["0", "1"], repeat=power)
    combos = ["".join(x) for x in combos]
    return combos

def to_ascii(b):
    """
    Returns a string of characters from a string of bytes.

    '0110100001100101011011000110110001101111' converts to 'hello'.
    The inverse operation of to_bin.
    """
    pos = 0
    s = ""
    max_length = len(b)
    while pos * 8 < max_length:
        s += decode_byte(b[pos * 8:pos * 8 + 8])
        pos += 1
    return s


#   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# Helper functions for the logic behind the encoding.   #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #

def round_to_congruence(k, end_remainder, modulus=2):
    """
    Rounds an integer to the nearest integer n such that n % modulus == end_remainder.
    """
    remainder = k % modulus
    end_remainder %= modulus # make sure it's not modulus itself.
    rem_diff = end_remainder - remainder
    n = k + rem_diff
    if n > k and n - modulus >= 0: return choice([n, n - modulus])
    elif n < k and n + modulus <= 255: return choice([n, n + modulus])
    elif n < 0: return n + modulus
    elif n > 255: return n - modulus
    return n

def generate_colour_tuple(pixel, new_val, ch):
    """
    Replaces the ch colour of the (r,g,b) tuple with new_val.
    """
    r, g, b = pixel
    match ch:
        case "red": return (new_val, g, b)
        case "green": return (r, new_val, b)
        case "blue": return (r, g, new_val)

def calculate_skip(skipping: int, msg: str, bit_level: int, width: int, height: int, **kwargs):
    """
    Calculates the maximum skipping number for encoding a given message such that it fits the image.

    If supplied with -s 0, calculates skipping number such that the message gets evenly
    encoded across the image. Try it with -t "asdfasdfasdfasdfasdfasdfasdfasdfasdf" -b 8 -s 0.
    """
    if skipping != 0:
        return skipping
    required_pixels = 8 + ceil((len(msg) * 8) / (3 * bit_level))
    return int(max( ((height * width) // required_pixels), 1))


#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #  #
# IO functions that deal with the actual encoding and decoding. #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #  #

def decode_message(img, width: int, height: int, channels: dict,
                   bit_level = 1, skipping=1, offset=0, **kwargs):
    """
    Reads pixel data and returns a string of bits if an encoded message is found.

    Reads ch channels' remainder with division modulo 2**bit_level 
    as that number in binary and returns the concatenated string.
    Terminates and begins on 3*8*bit_level bits of alternating "1010..."
    """
    b = ""
    key_seq = "10"*3*4*bit_level # this means 8 pixels regardless of bit_level.
    key_len = 3*8*bit_level
    bit_data = bit_combinations(bit_level)
    pos = offset

    while pos < width * height:
        for ch in ("red", "green", "blue"):
            (x, y) = pos // height, pos % height
            modulus = img[x, y][channels[ch]] % (2**bit_level)
            b += bit_data[modulus]
        if pos - offset == 8 * skipping and b[:key_len] != key_seq:
            return to_bin("no message found!")
        pos += skipping
    try:
        endpoint = b[key_len:].index(key_seq) + key_len # i have no idea why this works.
        return b[key_len: endpoint] # cut out everything outside key_seq
    except Exception: # the image was too small to contain the key_seq at the end.
        return b[key_len:]

def encode_message(img, msg: str, width: int, height: int, channels: dict,
                   bit_level=1, skipping=1, offset=0, **kwargs):
    """
    Writes binary sequence into the pixels of img.

    Reserves bit_level bits per colour channel while skipping
    every skipping-th pixel. offset allows one to start at the
    offset-th pixel.
    """
    # 8 pixels of padding at start and end, 16 bits of nothing before end to safeguard
    # ending characters.
    msg = "10"*3*4*bit_level + to_bin(msg) + "00"*16 + "10"*3*4*bit_level
    bit_data = bit_combinations(bit_level)

    # pad to make msg length divisible by bit_level, so it'll process nicely with
    # msg_segment down in the next block.
    msg_length = len(msg)
    while msg_length % bit_level != 0:
        msg += "0"
        msg_length += 1
    msg_length = len(msg)
    msg_pos = 0
    pos = offset

    while msg_pos < msg_length:
        for ch in ("red", "green", "blue"):
            # window[010]0101011101 with bit_level=3.
            msg_segment = msg[msg_pos:msg_pos + bit_level]
            (x, y) = pos // height, pos % height
            if pos >= width * height:
                return 1
            elif msg_pos >= msg_length: # in case we run out of data mid-pixel.
                return 1
            img[x, y] = generate_colour_tuple(img[x, y],
                            round_to_congruence(img[x, y][channels[ch]],
                                                bit_data.index(msg_segment),
                                                2**bit_level), ch)
            msg_pos += bit_level
        pos += skipping

def analyze_file(img, height: int, channels: dict, skip_max=15, print_mode=False, **kwargs):
    """
    Tries to find an encoded message in the pixel data by identifying a starting sequence.

    This will check the image for a starting sequence in all possible combinations 
    of bit_levels and skipping modes up to skip_max - 1. Will go through each skip level
    as it's pretty fast. print_mode=True is used for --decode.
    """
    pos = 0
    found = None
    for bits in range(1,9):
        bit_data = bit_combinations(bits)
        key_len = 3*8*bits
        loop_skip = ceil(skip_max / (9 - bits))
        for skip_level in range(1, loop_skip):
            pos = 0
            b = ""
            while len(b) < key_len:
                for ch in ("red", "green", "blue"):
                    modulus = img[pos // height, pos % height][channels[ch]] % (2**bits)
                    b += bit_data[modulus]
                pos += skip_level
            if b[:key_len] == "10"*3*4*bits:
                if print_mode:
                    print(f"Message detected with bit_level = {bits} and skipping = {skip_level}.")
                found = (bits, skip_level)
    if not found:
        print("No message found.")
        return (-1, -1)
    return found

def main(argv):
    """
    Argument handling and data validation for user input.
    """

    # just some global vars and validation. bit messy.
    try:
        image = Image.open(argv.filename).convert("RGB")
        img = image.load()
        width, height = image.size
        channels = {"red": 0, "green": 1, "blue": 2}
        bit_level = argv.bitlevel or 1
        skipping = argv.skipping or 1
        offset = argv.offset or 0
        bit_level = bit_level if (8 >= bit_level > 0) else 1
        skipping =  skipping if (skipping > 0) else 1
        offset = offset if (offset >= 0) else 0
        data = {"img": img, "width": width, "height": height,
                "bit_level": bit_level, "skipping": skipping,
                "offset": offset, "channels": channels,
                "msg": ""}
    except FileNotFoundError:
        print(f"No file '{argv.filename}' found.")
        return -1

    if argv.decode: # -d
        data["bit_level"], data["skipping"] = analyze_file(skip_max=calculate_skip(0, " ", 8, width, height),
                                                           print_mode=False,
                                                           **data)
        if data["bit_level"] != -1: # something was found automatically, otherwise get (-1, -1).
            print(to_ascii(decode_message(**data)))

    elif argv.manual: # -m -b [bitlevel] -s [skipping]
        print(to_ascii(decode_message(**data)))

    elif argv.input: # -i [textfile.txt]
        try:
            text = open(argv.input, "r", encoding="utf-8").read()
            data["msg"] = "".join((c for c in text if 0 < ord(c) < 255)) # stupid unicode.
            data["skipping"] = calculate_skip(**data)
            encode_message(**data)
            image.save("encoded.png")
            print(f"Encoded with bit_level = {data['bit_level']} and skipping = {data['skipping']}")
        except FileNotFoundError:
            print(f"Supplied text file '{argv.input}' not found.")

    elif argv.typemessage: # -t "some message." -b [bitlevel] -s [skipping] -o [offset]
        data["msg"] = argv.typemessage
        skipping = calculate_skip(**data)
        encode_message(**data)
        image.save("encoded.png")
        print(f"Encoded with bit_level = {data["bit_level"]} and skipping = {data["skipping"]}")

    elif argv.analyze: # -a. will not test offsets.
        largest_possible_skip = calculate_skip(0, " ", 8, width, height)
        analyze_file(skip_max=largest_possible_skip, print_mode=True, **data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog="Simple Binary Steganography Tool",
                    description="Encode and decode a message into and from the colour channels\nof an image.")

    parser.add_argument("filename", help="Name of the image file.")
    parser.add_argument("-i", "--input", metavar="TEXTFILE", help="Encode the contents of a text file into the image.")
    parser.add_argument("-t", "--typemessage", metavar="MESSAGE", help="Type directly to encode a message into the image file.")
    parser.add_argument("-d", "--decode", action="store_true", help="Read a message from the image file.")
    parser.add_argument("-b", "--bitlevel", metavar="BITS_PER_PIXEL", type=int, help="Store n bits per pixel. Higher = less discreet, as the colours are represented in fewer bits.")
    parser.add_argument("-s", "--skipping", metavar="N", type=int, help="Skip all but every Nth pixel in the encoding process. 0 to populate the image evenly (default).")
    parser.add_argument("-o", "--offset", metavar="K", type=int, help="Start encoding at the Kth pixel, allows for multiple messages per image, assuming you use the same skipping number.")
    parser.add_argument("-m", "--manual", action="store_true", help="Decode with optional manual --bitlevel and --skipping flags (default to 1 and 1).")
    parser.add_argument("-a", "--analyze", action="store_true", help="Tries to automatically find an encoded message and its settings.")

    main(parser.parse_args())
