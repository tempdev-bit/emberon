# emberon.py - v2
# Encode any file into a lossless PNG image and decode it back.
# Now with: streaming decode, PNG mode validation, progress bar, colored CLI output,
# human-readable sizes, and pretty header dump.

import argparse
import math
import os
import struct
import hashlib
import zlib
from PIL import Image
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init

# Initialize color output
colorama_init(autoreset=True)


#---------------Header Stuff------------------#
MAGIC = b'EMBERON2'

# Struct format string defining the binary layout of the PNG header.
HEADER_FMT = '>8sB B Q Q 32s' # Big-endian PNG header format: magic(8s), comp_method(B), reserved(B), orig_size(Q), comp_size(Q), sha256_digest(32s)

HEADER_SIZE = struct.calcsize(HEADER_FMT)
HEADER_PAD_TO = 64

COMP_ZLIB = 1 #Zlib compression is set to none
COMP_NONE = 0 #Comp mode set

CHUNK_ENCODE_SIZE = 128 * 1024 * 1024  # 128 MB
CHUNK_DECODE_SIZE = 64 * 1024 * 1024   # 68 MB

HEADER_RESERVED_BYTE = 0
BYTES_PER_PIXEL = 4  # RGBA

#----------------------------Helpers------------------------------#
def pretty_size(num_bytes: int) -> str:

    # Convert bytes to human-readable string.
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def calc_header(orig_size: int, comp_bytes: bytes, comp_method: int = COMP_ZLIB) -> bytes:
    sha = hashlib.sha256() # Create a new SHA-256 hash object

    # Ensures files of the same content but different sizes won't produce the same hash
    sha.update(f"{orig_size}:".encode())

    # Add the compressed file data to the hash input
    # This covers the actual content so any corruption will change the hash
    sha.update(comp_bytes)

    digest = sha.digest()

    comp_size = len(comp_bytes)
    header = struct.pack(
        HEADER_FMT,
        MAGIC,
        comp_method,
        HEADER_RESERVED_BYTE,
        orig_size,
        comp_size,
        digest
    )

    if len(header) > HEADER_PAD_TO:
        raise RuntimeError("header unexpectedly too large")
    header += b'\x00' * (HEADER_PAD_TO - len(header))
    return header

def choose_dimensions(num_pixels: int):
    w = int(math.ceil(math.sqrt(num_pixels)))
    h = int(math.ceil(num_pixels / w))
    return w, h

def print_header_info(unpacked):
    magic, comp_method, reserved, orig_size, comp_size, digest = unpacked
    print(Fore.CYAN + "[Header Information]")
    print(f" Magic: {magic}")
    print(f" Compression: {'zlib' if comp_method == COMP_ZLIB else 'none'}")
    print(f" Original size: {pretty_size(orig_size)}")
    print(f" Compressed size: {pretty_size(comp_size)}")
    print(f" SHA-256: {digest.hex()}")
    print(f" Reserved: {reserved}")


#------------------------ENCODE---------------------#
def encode_file_to_png(in_path: str, out_path: str, compress_level: int = 6, no_compress=False):
    if not no_compress:
        comp_obj = zlib.compressobj(level=compress_level)
        comp_chunks = []
        with open(in_path, 'rb') as f, tqdm(total=os.path.getsize(in_path), unit='B', unit_scale=True, desc="Compressing") as pbar:
            while True:
                chunk = f.read(CHUNK_ENCODE_SIZE)
                if not chunk:
                    break
                comp_chunks.append(comp_obj.compress(chunk))
                pbar.update(len(chunk))
            comp_chunks.append(comp_obj.flush())
        comp_bytes = b''.join(comp_chunks)
        comp_method = COMP_ZLIB
        orig_size = os.path.getsize(in_path)
    else:
        with open(in_path, 'rb') as f:
            comp_bytes = f.read()
        comp_method = COMP_NONE
        orig_size = len(comp_bytes)

    header = calc_header(orig_size, comp_bytes, comp_method=comp_method)
    payload = header + comp_bytes

    pad_len = (-len(payload)) % BYTES_PER_PIXEL
    if pad_len:
        payload += b'\x00' * pad_len

    num_pixels = len(payload) // BYTES_PER_PIXEL
    width, height = choose_dimensions(num_pixels)

    total_pixels = width * height
    extra_pixels = total_pixels - num_pixels
    if extra_pixels:
        payload += b'\x00' * (extra_pixels * BYTES_PER_PIXEL)

    img = Image.frombytes('RGBA', (width, height), payload)
    img.save(out_path, format='PNG', optimize=False)

    print(Fore.GREEN + f"✓ Encoded {in_path} -> {out_path} [{width}x{height}]")
    print(Fore.YELLOW + f"   Compression: {'none' if comp_method == COMP_NONE else 'zlib'} "
                        f"(orig {pretty_size(orig_size)} → comp {pretty_size(len(comp_bytes))})")


#--------------------------------DECODE-----------------------------#
def decode_png_to_file(in_path: str, out_path: str):
    img = Image.open(in_path)

    # Validate PNG mode
    if img.mode != 'RGBA':
        raise RuntimeError(f"Unsupported PNG mode: {img.mode}, expected RGBA")

    raw = img.tobytes("raw", "RGBA")

    if len(raw) < HEADER_PAD_TO:
        raise RuntimeError("image too small to contain header")

    header_bytes = raw[:HEADER_PAD_TO]
    unpacked = struct.unpack(HEADER_FMT, header_bytes[:HEADER_SIZE])
    magic, comp_method, reserved, orig_size, comp_size, digest = unpacked

    if magic != MAGIC:
        raise RuntimeError("magic mismatch: not a file produced by this encoder")

    comp_start = HEADER_PAD_TO
    comp_end = comp_start + comp_size
    if comp_end > len(raw):
        raise RuntimeError("image does not contain full compressed payload (truncated?)")

    comp_bytes = raw[comp_start:comp_end]

    sha = hashlib.sha256()
    sha.update(f"{orig_size}:".encode())
    sha.update(comp_bytes)
    if sha.digest() != digest:
        raise RuntimeError("SHA-256 mismatch: data corrupted or wrong image")

    # Streaming decode
    with open(out_path, 'wb') as f_out, tqdm(total=orig_size, unit='B', unit_scale=True, desc="Decompressing") as pbar:
        if comp_method == COMP_ZLIB:
            d = zlib.decompressobj()
            for i in range(0, len(comp_bytes), CHUNK_DECODE_SIZE):
                chunk = comp_bytes[i:i+CHUNK_DECODE_SIZE]
                data = d.decompress(chunk)
                f_out.write(data)
                pbar.update(len(data))
            f_out.write(d.flush())
        elif comp_method == COMP_NONE:
            f_out.write(comp_bytes)
            pbar.update(len(comp_bytes))
        else:
            raise RuntimeError(f"unknown compression method {comp_method}")

    print(Fore.GREEN + f"✓ Decoded {in_path} -> {out_path} ({pretty_size(orig_size)})")


#---------------------Main--------------------------#
def main():
    p = argparse.ArgumentParser(description="Encode any file into PNG and decode it back.")
    sp = p.add_subparsers(dest='cmd', required=True)

    enc = sp.add_parser('encode', help='Encode a file to PNG')
    enc.add_argument('input')
    enc.add_argument('output')
    enc.add_argument('-l', '--level', type=int, default=6, help='zlib compression level 0-9')
    enc.add_argument('--no-compress', action='store_true')

    dec = sp.add_parser('decode', help='Decode PNG to original file')
    dec.add_argument('input')
    dec.add_argument('output')

    insp = sp.add_parser('inspect', help='Inspect PNG header without decoding')
    insp.add_argument('input')

    args = p.parse_args()

    try:
        if args.cmd == 'encode':
            if not os.path.isfile(args.input):
                raise SystemExit(Fore.RED + "input file not found")
            encode_file_to_png(args.input, args.output, compress_level=args.level, no_compress=args.no_compress)
        elif args.cmd == 'decode':
            if not os.path.isfile(args.input):
                raise SystemExit(Fore.RED + "input file not found")
            decode_png_to_file(args.input, args.output)
        elif args.cmd == 'inspect':
            if not os.path.isfile(args.input):
                raise SystemExit(Fore.RED + "input file not found")
            img = Image.open(args.input)
            if img.mode != 'RGBA':
                raise SystemExit(Fore.RED + f"Unsupported PNG mode: {img.mode}")
            raw = img.tobytes("raw", "RGBA")
            if len(raw) < HEADER_PAD_TO:
                raise SystemExit(Fore.RED + "image too small to contain header")
            header_bytes = raw[:HEADER_PAD_TO]
            unpacked = struct.unpack(HEADER_FMT, header_bytes[:HEADER_SIZE])
            print_header_info(unpacked)
    except Exception as e:
        print(Fore.RED + f"Error: {e}")


if __name__ == '__main__':
    main()
