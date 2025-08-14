#emebron.py
#Encode any file into a lossless PNG image and decode it back.

import argparse
import math
import os
import struct
import hashlib
import zlib
from PIL import Image

#---------------Header Stuff------------------#
MAGIC = b'EMBERON1'   # 8 bytes magic/version
HEADER_FMT = '>8sB B Q Q 32s'  # HEADER YAY: big-endian: magic(8), comp_method(1), reserved(1), orig_size(8), comp_size(8), sha256(32)

# Total header size computed by struct.calcsize
HEADER_SIZE = struct.calcsize(HEADER_FMT)  # should be 8+1+1+8+8+32 = 58 we'll pad header to HEADER_PAD_TO bytes
HEADER_PAD_TO = 64

COMP_ZLIB = 1  # Compression used
COMP_NONE = 0  # Compression NOT used

HEADER_RESERVED_BYTE = 0
BYTES_PER_PIXEL = 4  # RGBA = 4 bytes per pixel

#--------------Calculate total header size---------------#
def calc_header(orig_size: int, comp_bytes: bytes, comp_method: int = COMP_ZLIB) -> bytes:
    sha = hashlib.sha256()
    sha.update(b'%d:' % orig_size)
    sha.update(comp_bytes)  # hash depends on original length & compressed content
    digest = sha.digest()

    comp_size = len(comp_bytes)
    header = struct.pack(HEADER_FMT,
                         MAGIC,
                         comp_method,
                         HEADER_RESERVED_BYTE,  # reserved for future purposes ^^
                         orig_size,
                         comp_size,
                         digest)

    # pad header to HEADER_PAD_TO bytes
    if len(header) > HEADER_PAD_TO:
        raise RuntimeError("header unexpectedly too large")
    header += b'\x00' * (HEADER_PAD_TO - len(header))
    return header


#-----------Chooses the dimensions---------------#
def choose_dimensions(num_pixels: int):
    #Choose image width and height to be near-square.
    #Returns (width, height) integers.
    w = int(math.ceil(math.sqrt(num_pixels)))
    h = int(math.ceil(num_pixels / w))
    return w, h


#------------------------ENCODE!!!!---------------------#
def encode_file_to_png(in_path: str, out_path: str, compress_level: int = 6, no_compress=False):
    # Read file bytes
    with open(in_path, 'rb') as f:
        data = f.read()
    orig_size = len(data)

    # Compress (zlib) unless no_compress set
    if not no_compress:
        comp_bytes = zlib.compress(data, level=compress_level)
        comp_method = COMP_ZLIB
    else:
        comp_bytes = data
        comp_method = COMP_NONE

    header = calc_header(orig_size, comp_bytes, comp_method=comp_method)
    payload = header + comp_bytes  # 'payload' sounds too serious but i'm keeping it

    # Pad to multiple of BYTES_PER_PIXEL
    pad_len = (-len(payload)) % BYTES_PER_PIXEL
    if pad_len:
        payload += b'\x00' * pad_len

    num_pixels = len(payload) // BYTES_PER_PIXEL
    width, height = choose_dimensions(num_pixels)

    # If width*height pixels > needed, pad trailing bytes
    total_pixels = width * height
    extra_pixels = total_pixels - num_pixels
    if extra_pixels:
        payload += b'\x00' * (extra_pixels * BYTES_PER_PIXEL)

    assert len(payload) == total_pixels * BYTES_PER_PIXEL

    # Create RGBA image from raw bytes
    img = Image.frombytes('RGBA', (width, height), payload)

    # Save as PNG (lossless)
    img.save(out_path, format='PNG', compress_level=0)
    print(f"Encoded {in_path} ({orig_size} bytes) -> {out_path} ({width}x{height}, {total_pixels} pixels).")
    print(f"Compression: {'none' if comp_method==COMP_NONE else 'zlib'} (orig {orig_size} -> comp {len(comp_bytes)} bytes)")


#--------------------------------DECODE!!-----------------------------#
def decode_png_to_file(in_path: str, out_path: str):
    img = Image.open(in_path)
    raw = img.tobytes("raw", "RGBA")  # bytes length = w*h*BYTES_PER_PIXEL

    # Header is at start
    if len(raw) < HEADER_PAD_TO:
        raise RuntimeError("image too small to contain header")

    header_bytes = raw[:HEADER_PAD_TO]
    unpacked = struct.unpack(HEADER_FMT, header_bytes[:struct.calcsize(HEADER_FMT)])
    magic, comp_method, reserved, orig_size, comp_size, digest = unpacked
    if magic != MAGIC:
        raise RuntimeError("magic mismatch: not a file produced by this encoder")

    # Extract compressed payload of comp_size bytes that immediately follow header
    comp_start = HEADER_PAD_TO
    comp_end = comp_start + comp_size
    if comp_end > len(raw):
        raise RuntimeError("image does not contain full compressed payload (truncated?)")

    comp_bytes = raw[comp_start:comp_end]

    # Verify sha256
    sha = hashlib.sha256()
    sha.update(b'%d:' % orig_size)
    sha.update(comp_bytes)
    if sha.digest() != digest:
        raise RuntimeError("SHA-256 mismatch: data corrupted or wrong image")

    # Decompress if needed
    if comp_method == COMP_ZLIB:
        data = zlib.decompress(comp_bytes)
    elif comp_method == COMP_NONE:
        data = comp_bytes
    else:
        raise RuntimeError(f"unknown compression method {comp_method}")

    if len(data) != orig_size:
        raise RuntimeError(f"original size mismatch: expected {orig_size} got {len(data)}")

    # Write output
    with open(out_path, 'wb') as f:
        f.write(data)
    print(f"Decoded {in_path} -> {out_path} ({len(data)} bytes)")


#---------------------Main + Subcommands--------------------------#
def main():
    p = argparse.ArgumentParser(description="Encode any file into PNG and decode it back.")
    sp = p.add_subparsers(dest='cmd', required=True)

    enc = sp.add_parser('encode', help='Encode a file to PNG')
    enc.add_argument('input', help='input file to encode')
    enc.add_argument('output', help='output PNG image')
    enc.add_argument('-l', '--level', type=int, default=6, help='zlib compression level 0-9 (default 6)')
    enc.add_argument('--no-compress', action='store_true', help='do not compress payload (store raw bytes)')

    dec = sp.add_parser('decode', help='Decode PNG to original file')
    dec.add_argument('input', help='input PNG produced by this tool')
    dec.add_argument('output', help='output file to write')

    args = p.parse_args()

    if args.cmd == 'encode':
        if not os.path.isfile(args.input):
            raise SystemExit("input file not found")
        encode_file_to_png(args.input, args.output, compress_level=args.level, no_compress=args.no_compress)
    elif args.cmd == 'decode':
        if not os.path.isfile(args.input):
            raise SystemExit("input file not found")
        decode_png_to_file(args.input, args.output)

if __name__ == '__main__':
    main()
