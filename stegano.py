from random import choice
from itertools import product
import argparse
from time import perf_counter
from PIL import Image

#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #
# Define basic bin -> ascii and ascii -> bin functions here. #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #

def to_bin(s: str):
    """
    Returns a string of bytes from a string of text;
    "hello" => "0110100001100101011011000110110001101111"
    """
    return "".join([ str(bin(ord(char)))[2:].zfill(8) for char in s])

def to_ascii_old(b: str):
    """
    Returns a string of characters from a string of bytes:
    "0110100001100101011011000110110001101111" => "hello"
    """
    pos = 0
    s = ""
    max_length = len(b)
    while pos * 8 < max_length:
        s += decode_byte(b[pos * 8:pos * 8 + 8])
        pos += 1
    return s

def decode_byte(b: str) -> str:
    """
    Returns string representation of a byte into a character:
    "11000001" => "a"
    """
    return chr(int(bytes(b, "utf-8"), 2))

def bit_combinations(power=1):
    """
    Generates ["0", "1"] with power==1
    Generates ["00", "01", "10", "11"] with power==2
    And so forth.
    """
    combos = product(["0", "1"], repeat=power)
    combos = ["".join(x) for x in combos]
    return combos

def to_ascii(b):
    pos = 0
    s = ""
    max_length = len(b)
    while pos * 8 < max_length:
        s += decode_byte(b[pos * 8:pos * 8 + 8])
        pos += 1
    return s

# this is pretty slow for now, because it loops over all the pixels individually.
# TODO: use numpy or build a little queue that checks for termination string.
def decode_message(img, mod_power = 1, skipping=1):
    """
    Reads ch channels' parity as 0 or 1 into b and returns.
    Terminates on 24 bits of "10101010..."

    mod_power means we encode mod_power bits per pixel, resulting in
    more aggressive rounding of values and thus more visible changes.
    """
    b = ""
    key_seq = "10"*12
    bit_data = bit_combinations(mod_power)
    steps = 0
    pixel_pos = 0

    for x in range(width):
        for y in range(height):
            if (pixel_pos % skipping) == 0:
                for ch in ("red", "green", "blue"):
                    modulus = img[x, y][channels[ch]] % (2**mod_power)
                    b += bit_data[modulus]
                    steps += 1
                    if steps == 24 and b[:24] != key_seq:
                        return to_bin("no message found!")
            pixel_pos += 1
    try:
        endpoint = b[24:].index(key_seq)
        return b[24: endpoint] # cut out everything outside key_seq
    except Exception: # the image was too small to contain the key_seq at the end.
        return b[24:]
    

def encode_message(img, msg, mod_power=1, skipping=1):
    """
    Writes an already encoded string of bytes into the pixels of
    the chosen image from a given message. msg is a sequence
    of 1s and 0s.

    mod_power writes mod_power bit(s) of information per pixel.
    (until the message ends or the pixels end.)
    """
    # message ends and starts with 24 bits of alternating 1s and 0s.
    # 24 empty characters are added to the end, because it's possible that
    # the 10101010... sequence is PRECEDED by a pattern that extends the sequence,
    # therefore trashing the characters.
    msg = "10"*12 + to_bin(msg) + "0"*24 + "10"*12
    bit_data = bit_combinations(mod_power)

    # pad to make msg length divisible by mod_power, so it'll process nicely with
    # msg_segment down in the next block.
    msg_length = len(msg)
    if msg_length % mod_power != 0:
        msg += (mod_power - (msg_length % mod_power)) * "0"
    msg_pos = 0
    pixel_pos = 0
    
    for x in range(width):
        for y in range(height):
            if (pixel_pos % skipping) == 0:
                for ch in ("red", "green", "blue"):
                    if msg_pos >= len(msg):
                        return 1
                    msg_segment = msg[msg_pos:msg_pos + mod_power] # this many bits [010]0101011101 with mod_power==3.
                    img[x, y] = generate_colour_tuple(img[x, y],
                                                round_to_congruence(img[x, y][channels[ch]],
                                                            bit_data.index(msg_segment), 
                                                            2**mod_power), ch)
                    msg_pos += mod_power
            pixel_pos += 1

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
    Returns a pixel 3-tuple (r,g,b), where the ch-corresponding
    colour is replaced by new_val.
    """
    r, g, b = pixel
    match ch:
        case "red": return (new_val, g, b)
        case "green": return (r, new_val, b)
        case "blue": return (r, g, new_val)

def analyze_file(img, skip_max=15, utility_mode=True):
    """
    This will check the image for a starting sequence in all possible combinations 
    of bit_levels and skipping modes up to skip_max - 1. Will stop each time after 24
    bits are found. utility_mode just returns found values so we can automatically decode.
    """
    pos = 0
    for bits in range(1,9):
        bit_data = bit_combinations(bits)
        for skip_level in range(1, skip_max):
            pos = 0
            b = ""
            while len(b) < 24:
                for ch in ("red", "green", "blue"):
                    modulus = img[pos // height, pos % height][channels[ch]] % (2**bits)
                    b += bit_data[modulus]
                pos += skip_level
            if len(b) >= 24 and b[:24] == "10"*12:
                if not utility_mode: 
                    print(f"Message detected with bit_level = {bits} and skipping {skip_level}.")
                return (bits, skip_level)
    print("No message found.")
    return (-1, -1)

def calculate_skip(skip: int, msg: str, bits: int):
    """
    If supplied with -s 0, calculates skipping number such that the message gets evenly
    encoded across the image. Try it with -t "asdfasdfasdfasdfasdfasdfasdfasdfasdf" -b 8 -s 0.
    """
    if skip != "0": return int(skip)
    from math import ceil
    return max((height * width) // (ceil(len(msg) * 8 /(3 * bits))), 1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog="Simple Binary Steganography Tool", 
                    description="Encode and decode a message into and from the colour channels\nof an image.",
                    epilog="")
    
    parser.add_argument("filename", help="Name of the image file.")
    parser.add_argument("-i", "--input", metavar="TEXTFILE", help="Encode the contents of a text file into the image.")
    parser.add_argument("-t", "--typemessage", metavar="MESSAGE", help="Type directly to encode a message into the image file.")
    parser.add_argument("-b", "--bitlevel", metavar="BITS_PER_PIXEL", help="Store n bits per pixel. Higher = less discreet, as the colours are represented in fewer bits.")
    parser.add_argument("-s", "--skipping", metavar="N", help="Skip all but every Nth pixel in the encoding process. 0 to populate the image evenly.")
    parser.add_argument("-d", "--decode", action="store_true", help="Read a message from the image file.")
    parser.add_argument("-m", "--manual", action="store_true", help="Decode with optional manual --bitlevel and --skipping flags (default to 1 and 1).")
    parser.add_argument("-a", "--analyze", action="store_true", help="Tries to automatically find an encoded message and its settings.")

    argv = parser.parse_args()
    
    # just some global vars and validation. bit messy.
    try:
        image = Image.open(argv.filename).convert("RGB")
        img = image.load()
        width, height = image.size
        channels = {"red": 0, "green": 1, "blue": 2}
        bit_level = int(argv.bitlevel) if argv.bitlevel else 1
        bit_level = bit_level if (0 < bit_level <= 8) else 1
        skipping = int(argv.skipping) if argv.skipping else 1
        skipping = skipping if skipping > 0 else 1
    except FileNotFoundError:
        print("No such file found.")
        argv = None # dirty hack, vol. 1
    if not argv: # dirty hack, the finale.
        pass

    elif argv.decode: # -d
        bit_level, skipping = analyze_file(img)
        if bit_level != -1:
            print(to_ascii(decode_message(img, bit_level, skipping)))
    
    elif argv.manual: # -m -b [bitlevel] -s [skipping]
        print(to_ascii(decode_message(img, bit_level, skipping)))
    
    elif argv.input: # -i [textfile.txt]
        try:
            text = open(argv.input, "r").read()
            stripped = "".join((c for c in text if 0 < ord(c) < 255)) # stupid unicode.
            skipping = calculate_skip(skip=argv.skipping, msg=stripped, bits=bit_level)
            encode_message(img, stripped, bit_level, skipping)
            image.save("encoded.png")
            print(f"Encoded with bit_level = {bit_level} and skipping = {skipping}")
        except FileNotFoundError:
            print(f"Supplied text file {argv.input} not found.")
    
    elif argv.typemessage: # -t "this is a message i wish to encode." -b [bitlevel] -s [skipping]
        skipping = calculate_skip(skip=argv.skipping, msg=argv.typemessage, bits=bit_level)
        encode_message(img, argv.typemessage, bit_level, skipping)
        image.save("encoded.png")
        print(f"Encoded with bit_level = {bit_level} and skipping = {skipping}")
    
    elif argv.analyze: # -a
        analyze_file(img, skip_max=15, utility_mode=False)