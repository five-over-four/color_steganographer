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

def to_bin(s: str) -> str:
    """
    Convert each character in the string into an 8-bit sequence and concatenate.

    'hello' is converted to '0110100001100101011011000110110001101111'.
    """
    return "".join([ str(bin(ord(char)))[2:].zfill(8) for char in s])


def decode_byte(b: str) -> str:
    """
    Returns string representation of a byte into a character.

    '01100001' converts to 'a'.
    """
    return chr(int(bytes(b, "utf-8"), 2))


def bit_combinations(power=1, to="decimal") -> dict:
    """
    Returns the dict translating between 0-255 and their corresponding power-bit strings.

    170 -> "10101010" unless to="decimal", in which case it's "10101010" -> 170.
    27 -> "11011" at power=5, 27 -> "0011011" at power=7.
    """
    combos = product(["0", "1"], repeat=power)
    combos = ["".join(x) for x in combos]
    if to == "decimal":
        return {x: i for x,i in zip(combos, range(2**power))}
    return {i: x for x, i in zip(combos, range(2**power))}


def to_ascii(b: str) -> str:
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

def round_to_congruence(k: int, end_remainder: int, modulus=2) -> int:
    """
    Rounds an integer to the nearest integer n such that n % modulus == end_remainder.
    """
    remainder = k % modulus
    end_remainder %= modulus # make sure it's not modulus itself.
    rem_diff = end_remainder - remainder
    n = k + rem_diff
    if n > k and n - modulus >= 0:
        return choice([n, n - modulus])
    elif n < k and n + modulus <= 255:
        return choice([n, n + modulus])
    elif n < 0:
        return n + modulus
    elif n > 255:
        return n - modulus
    return n


def generate_colour_tuple(pixel: tuple[int, int, int],
                          new_val: int, ch: str) -> tuple[int, int, int]:
    """
    Replaces the ch colour of the (r,g,b) tuple with new_val.
    """
    r, g, b = pixel
    match ch:
        case "red": return (new_val, g, b)
        case "green": return (r, new_val, b)
        case "blue": return (r, g, new_val)


def calculate_skip(skipping: int, msg: str, bit_level: int,
                   width: int, height: int, **kwargs) -> int:
    """
    Calculates the maximum skipping number for encoding a given message such that it fits the image.

    If supplied with -s 0, calculates skipping number such that the message gets evenly
    encoded across the image. Try it with -t "asdfasdfasdfasdfasdfasdfasdfasdfasdf" -b 8 -s 0.
    """
    if skipping != 0:
        return skipping
    required_pixels = 16 + ceil((len(msg) * 8) / (3 * bit_level))
    return max( ((height * width) // required_pixels), 1)


def convert_img_len_data(numbers, bit_level: int) -> int:
    """
    Converts list of decimal representations of bit_level-bit numbers into a concatenated decimal integer.

    at 4 bits, [3, 13] -> ["1001", "1111"] -> "10011111" -> 63, 'A'.
    """
    binary = "".join([bin(n)[2:].zfill(bit_level) for n in numbers])
    return int(bytes(binary, "utf-8"), 2)


#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #  #
# IO functions that deal with the actual encoding and decoding. #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #  #

def encode_message(image: Image.Image, msg: str, width: int, height: int, channels: dict,
                   bit_level=1, skipping=1, offset=0, **kwargs) -> str:
    """
    Writes binary sequence into the pixels of image. In-place.

    Reserves bit_level bits per colour channel while skipping every skipping-th pixel. 
    offset allows one to start at the offset-th pixel. 8px init sequence, 8px msg length info.
    """
    if width*height <= 16:
        return "Image is too small."

    binary = to_bin(msg)
    msg_length = 3*8*bit_level*2 + len(binary) # total len in binary.
    
    # if the message overfloweth, then the message you shalt rend asunder with thine most
    # unholy calculus proffered hereunder.
    if ceil(msg_length / bit_level) > width * height * 3 / skipping - offset * 3 - 48:
        length_data = bin(ceil(width * height * 3 / skipping - 48))[2:].zfill(3*8*bit_level)
    else:
        length_data = bin(ceil(msg_length / bit_level - 48))[2:].zfill(3*8*bit_level)

    # 8 pixels of padding and 8 pixels of message length information at start.
    msg = "10"*3*4*bit_level + length_data + binary
    bit_data = bit_combinations(bit_level, to="decimal")

    while msg_length % bit_level != 0:
        msg += "0"
        msg_length += 1

    msg_pos = 0 # in terms of the binary sequence.
    pos = offset # in terms of pixels.

    while pos < width * height:
        for ch in ("red", "green", "blue"):
            msg_segment = msg[msg_pos:msg_pos + bit_level]
            x, y = pos // height, pos % height
            percent_done = 100 * (msg_pos - 3*8*bit_level*2) / (msg_length - 3*8*bit_level*2)

            if pos >= (width * height - skipping) and percent_done < 100:
                image.save("encoded.png")
                return f"Couldn't fit entire message in image ({round(percent_done, 1)} % completed.)"
            elif msg_pos >= msg_length:
                image.save("encoded.png")
                return f"Encoded with bit_level = {bit_level}, skipping = {skipping}, offset = {offset}."

            image.putpixel((x, y), generate_colour_tuple(image.getpixel((x, y)),
                            round_to_congruence(image.getpixel((x, y))[channels[ch]],
                                                bit_data[msg_segment],
                                                2**bit_level), ch)
            )
            msg_pos += bit_level
        pos += skipping
    image.save("encoded.png")
    return f"Encoded with bit_level = {bit_level}, skipping = {skipping}, offset = {offset}."


def decode_message(image: Image.Image, height: int, channels: dict,
                   bit_level = 1, skipping=1, offset=0, **kwargs) -> str:
    """
    Reads pixel data and returns a string of bits if an encoded message is found.

    Reads ch channels' remainder with division modulo 2**bit_level 
    as that number in binary and returns the concatenated string.
    Message begins with 16 pixels of identification data.
    """
    b = ""
    key_seq = "10"*3*4*bit_level # this means 8 pixels regardless of bit_level.
    key_len = 3*8*bit_level
    bit_data = bit_combinations(bit_level, to="binary")

    # analyse the first 8 + 8 pixels and get diagnostic data.
    msg_diagnostics = ""
    for i in range(offset, 16 * skipping + offset, skipping):
        for ch in ("red", "green", "blue"):
            (x, y) = i // height, i % height
            modulus = image.getpixel((x, y))[channels[ch]] % (2**bit_level)
            msg_diagnostics += bit_data[modulus]
    if msg_diagnostics[:key_len] != key_seq:
        return to_bin("No message found!")
    msg_len = int(msg_diagnostics[key_len:], 2)

    pos = 16 * skipping + offset
    colour_pos = 0

    while colour_pos < msg_len:
        (x, y) = pos // height, pos % height
        pixel = image.getpixel((x, y))
        for ch in ("red", "green", "blue"):
            modulus = pixel[channels[ch]] % (2**bit_level)
            b += bit_data[modulus]
            colour_pos += 1
            if colour_pos >= msg_len:
                return b
        pos += skipping
    return b


def analyze_file(image: Image.Image, height: int, channels: dict,
                 skip_max=15, print_mode=False, **kwargs) -> tuple[int, int]:
    """
    Tries to find an encoded message in the pixel data by identifying a starting sequence.

    This will check the image for a starting sequence in all possible combinations 
    of bit_levels and skipping modes up to skip_max. Will go through each skip level
    as it's pretty fast. print_mode=True is used for --decode.
    """
    pos = 0
    found = None
    for bits in range(8,0,-1): # 8 bit start seq. is also 6, 4, 2 startup; start high.
        bit_data = bit_combinations(bits, to="binary")
        key_len = 3*8*bits
        loop_skip = max(ceil(skip_max / (9 - bits)), 1) # max skip for this bit_level.
        for skip_level in range(1, loop_skip + 1):
            pos = 0
            b = ""
            while len(b) < key_len * 2:
                for ch in ("red", "green", "blue"):
                    (x,y) = (pos // height, pos % height)
                    modulus = image.getpixel((pos // height, pos % height))[channels[ch]] % (2**bits)
                    b += bit_data[modulus]
                pos += skip_level
            if b[:key_len] == "10"*3*4*bits:
                msg_len = int(b[key_len:], 2) * bits / (8000)
                if print_mode:
                    print(f"{round(msg_len,2)}kB message detected with bit_level = {bits} and skipping = {skip_level}.")
                return (bits, skip_level)
    if not found:
        print("No message found.")
        return (-1, -1)


def main(argv: argparse.Namespace) -> None:
    """
    Argument handling and data validation for user input.
    """

    # just some global vars and validation. bit messy.
    try:
        image = Image.open(argv.filename).convert("RGB")
    except FileNotFoundError:
        print(f"No file '{argv.filename}' found.")
        return
    width, height = image.size
    channels = {"red": 0, "green": 1, "blue": 2}
    bit_level = argv.bitlevel or 1
    skipping = argv.skipping or 1
    offset = argv.offset or 0
    bit_level = bit_level if (8 >= bit_level > 0) else 1
    skipping =  skipping if (skipping > 0) else 1
    offset = offset if (offset >= 0) else 0
    data = {"image": image, "width": width, "height": height,
            "bit_level": bit_level, "skipping": skipping,
            "offset": offset, "channels": channels,
            "msg": ""}

    if argv.decode: # -d
        if any([argv.bitlevel, argv.skipping, argv.offset]): # with -b, -s, or -o
            print(to_ascii(decode_message(**data)))
        else: # without extra flags, automatic.
            data["bit_level"], data["skipping"] = \
                analyze_file(skip_max=calculate_skip(0, " ", 8, width, height),
                            print_mode=False,
                            **data)
            if data["bit_level"] != -1: # something was found automatically, otherwise get (-1, -1).
                print(to_ascii(decode_message(**data)))

    elif argv.input: # -i [textfile.txt]
        try:
            text = open(argv.input, "r", encoding="utf-8").read()
            data["msg"] = "".join((c for c in text if 0 < ord(c) < 255)) # stupid unicode.
            data["skipping"] = calculate_skip(**data)
            print(encode_message(**data))
        except FileNotFoundError:
            print(f"Supplied text file '{argv.input}' not found.")

    elif argv.type: # -t "some message." -b [bitlevel] -s [skipping] -o [offset]
        data["msg"] = argv.type
        skipping = calculate_skip(**data)
        print(encode_message(**data))

    elif argv.analyze: # -a. will not test offsets.
        largest_possible_skip = calculate_skip(0, " ", 8, width, height)
        analyze_file(skip_max=largest_possible_skip, print_mode=True, **data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog="Simple Binary Steganography Tool",
                    description="Encode and decode a message into and from the colour channels\nof an image.")

    parser.add_argument("filename", help="Name of the image file.")
    parser.add_argument("-i", "--input", metavar="TEXTFILE", help="Encode the contents of a text file into the image.")
    parser.add_argument("-t", "--type", metavar="MESSAGE", help="Type directly to encode a message into the image file.")
    parser.add_argument("-d", "--decode", action="store_true", help="Read a message from the image file.")
    parser.add_argument("-b", "--bitlevel", metavar="BITS_PER_PIXEL", type=int, help="Store n bits per pixel. Higher = less discreet, as the colours are represented in fewer bits.")
    parser.add_argument("-s", "--skipping", metavar="N", type=int, help="Skip all but every Nth pixel in the encoding process. 0 to populate the image evenly (default).")
    parser.add_argument("-o", "--offset", metavar="K", type=int, help="Start encoding at the Kth pixel, allows for multiple messages per image, assuming you use the same skipping number.")
    parser.add_argument("-a", "--analyze", action="store_true", help="Tries to automatically find an encoded message and its settings.")

    main(parser.parse_args())
