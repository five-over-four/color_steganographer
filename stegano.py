from random import choice
from itertools import product
import argparse
from math import ceil
from time import perf_counter
from PIL import Image

#   #   #   #   #   #   #   #   #   #   #   #   #   # #
# Basic bin -> ascii and ascii -> bin functions here. #
#   #   #   #   #   #   #   #   #   #   #   #   #   # #

def to_bin(s: str):
    """
    Returns a string of bytes from a string of text;
    "hello" => "0110100001100101011011000110110001101111"
    """
    return "".join([ str(bin(ord(char)))[2:].zfill(8) for char in s])

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
    Returns a pixel 3-tuple (r,g,b), where the ch-corresponding
    colour is replaced by new_val.
    """
    r, g, b = pixel
    match ch:
        case "red": return (new_val, g, b)
        case "green": return (r, new_val, b)
        case "blue": return (r, g, new_val)

def calculate_skip(skip: int, msg: str, bits: int):
    """
    If supplied with -s 0, calculates skipping number such that the message gets evenly
    encoded across the image. Try it with -t "asdfasdfasdfasdfasdfasdfasdfasdfasdf" -b 8 -s 0.
    """
    if skip != "0": return int(skip)
    required_pixels = 8 + ceil((len(msg) * 8) / (3 * bits))
    return int(max( ((height * width) // required_pixels), 1))
    

#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #  #
# IO functions that deal with the actual encoding and decoding. #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #  #

# TODO: Consider using numpy?
def decode_message(img, mod_power = 1, skipping=1):
    """
    Reads ch channels' remainder with division modulo 2**mod_power 
    as that number in binary and returns the concatenated string.
    Terminates and begins on 3*8*mod_power bits of alternating "1010..."

    mod_power means we encode mod_power bits per pixel, resulting in
    more aggressive rounding of values and thus more visible changes.
    """
    b = ""
    key_seq = "10"*3*4*mod_power # this means 8 pixels regardless of mod_power. 24bits for 1, 192bits for 8.
    key_len = 3*8*mod_power
    bit_data = bit_combinations(mod_power)
    pos = 0
    
    while pos < width * height:
        for ch in ("red", "green", "blue"):
            (x, y) = pos // height, pos % height
            modulus = img[x, y][channels[ch]] % (2**mod_power)
            b += bit_data[modulus]
        if pos == 8 * skipping and b[:key_len] != key_seq:
            return to_bin("no message found!")
        pos += skipping
    try:
        endpoint = b[key_len:].index(key_seq) + key_len # i have no idea why this works.
        return b[key_len: endpoint] # cut out everything outside key_seq
    except Exception: # the image was too small to contain the key_seq at the end.
        return b[key_len:]

def encode_message(img, msg, mod_power=1, skipping=1):
    """
    Writes binary sequence as a string (msg) into the pixels of img, taking
    mod_power bits per colour channel every skipping-th pixel.
    """
    # 8 pixels of padding at start and end, 16 bits of nothing before end to safeguard
    # ending characters.
    msg = "10"*3*4*mod_power + to_bin(msg) + "00"*16 + "10"*3*4*mod_power
    bit_data = bit_combinations(mod_power)

    # pad to make msg length divisible by mod_power, so it'll process nicely with
    # msg_segment down in the next block.
    msg_length = len(msg)
    if msg_length % mod_power != 0:
        msg += (mod_power - (msg_length % mod_power)) * "0"
    msg_length = len(msg)
    msg_pos = 0
    pos = 0

    while msg_pos < msg_length:
        for ch in ("red", "green", "blue"):
            msg_segment = msg[msg_pos:msg_pos + mod_power] # this many bits [010]0101011101 with mod_power==3.
            (x, y) = pos // height, pos % height
            if pos >= width * height:
                return 1
            img[x, y] = generate_colour_tuple(img[x, y],
                            round_to_congruence(img[x, y][channels[ch]],
                                                bit_data.index(msg_segment), 
                                                2**mod_power), ch)
            msg_pos += mod_power
        pos += skipping

def analyze_file(img, skip_max=15, print_mode=False):
    """
    This will check the image for a starting sequence in all possible combinations 
    of bit_levels and skipping modes up to skip_max - 1. Will go through each skip level
    as it's pretty fast. print_mode=True is used for --decode.
    """
    pos = 0
    found = None
    for bits in range(1,9):
        bit_data = bit_combinations(bits)
        key_len = 3*8*bits
        loop_skip = ceil(skip_max / (9 - bits)) # the number of pixels needed each bit_level is inversely proportional to it.
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog="Simple Binary Steganography Tool", 
                    description="Encode and decode a message into and from the colour channels\nof an image.",
                    epilog="")
    
    parser.add_argument("filename", help="Name of the image file.")
    parser.add_argument("-i", "--input", metavar="TEXTFILE", help="Encode the contents of a text file into the image.")
    parser.add_argument("-t", "--typemessage", metavar="MESSAGE", help="Type directly to encode a message into the image file.")
    parser.add_argument("-b", "--bitlevel", metavar="BITS_PER_PIXEL", help="Store n bits per pixel. Higher = less discreet, as the colours are represented in fewer bits.")
    parser.add_argument("-s", "--skipping", metavar="N", help="Skip all but every Nth pixel in the encoding process. 0 to populate the image evenly (default).")
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
        print(f"No file '{argv.filename}' found.")
        argv = None # dirty hack, vol. 1
    if not argv: # dirty hack, the finale.
        pass

    elif argv.decode: # -d
        bit_level, skipping = analyze_file(img, skip_max=calculate_skip("0", " ", 8), print_mode=False)
        if bit_level != -1:
            print(to_ascii(decode_message(img, bit_level, skipping)))
    
    elif argv.manual: # -m -b [bitlevel] -s [skipping]
        print(to_ascii(decode_message(img, bit_level, skipping)))
    
    elif argv.input: # -i [textfile.txt]
        try:
            text = open(argv.input, "r").read()
            stripped = "".join((c for c in text if 0 < ord(c) < 255)) # stupid unicode.
            
            if not argv.skipping:
                skipping = calculate_skip(skip="0", msg=stripped, bits=bit_level)
            else:
                skipping = calculate_skip(skip=argv.skipping, msg=stripped, bits=bit_level)
            encode_message(img, stripped, bit_level, skipping)
            image.save("encoded.png")
            print(f"Encoded with bit_level = {bit_level} and skipping = {skipping}")
        except FileNotFoundError:
            print(f"Supplied text file '{argv.input}' not found.")
    
    elif argv.typemessage: # -t "this is a message i wish to encode." -b [bitlevel] -s [skipping]
        if not argv.skipping:
            skipping = calculate_skip(skip="0", msg=argv.typemessage, bits=bit_level)
        else:
            skipping = calculate_skip(skip=argv.skipping, msg=argv.typemessage, bits=bit_level)
        encode_message(img, argv.typemessage, bit_level, skipping)
        image.save("encoded.png")
        print(f"Encoded with bit_level = {bit_level} and skipping = {skipping}")
    
    elif argv.analyze: # -a
        largest_possible_skip = calculate_skip("0", " ", 8) # this is absolute shortest message that can exist.
        analyze_file(img, skip_max=largest_possible_skip, print_mode=True)