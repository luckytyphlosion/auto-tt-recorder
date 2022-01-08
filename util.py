import codecs
import struct
import itertools

def min_sec_ms_to_time(minutes, seconds, milliseconds):
    return minutes * 100000 + seconds * 1000 + milliseconds

def utf_16_hex(s):
    s_as_utf_16_bytes = s.encode(encoding="utf-16")
    if s_as_utf_16_bytes[:2] == codecs.BOM_UTF16_LE:
        struct_format = "<H"
        s_as_utf_16_bytes_no_bom = s_as_utf_16_bytes[2:]
    elif s_as_utf_16_bytes[:2] == codecs.BOM_UTF16_BE:
        struct_format = ">H"
        s_as_utf_16_bytes_no_bom = s_as_utf_16_bytes[2:]
    else:
        struct_format = "<H"
        s_as_utf_16_bytes_no_bom = s_as_utf_16_bytes

    return "".join(f"{num[0]:04x}" for num in struct.iter_unpack(struct_format, s_as_utf_16_bytes_no_bom))

def grouper(iterable, n, fillvalue=None):
    "Collect data into non-overlapping fixed-length chunks or blocks"
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

def arg_default_or_validate_from_choices(arg, *choices_and_error_message):
    default = choices_and_error_message[0]
    choices = choices_and_error_message[:-1]
    error_message = choices_and_error_message[-1]

    if arg is None:
        arg = default
    elif arg not in choices:
        raise RuntimeError(error_message.format(arg))

    return arg
