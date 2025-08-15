# emberon.py - v2.5
# Encode any file into a lossless PNG image and decode it back.
# Now stores original filename and extension in header.

import argparse
import math
import os
import struct
import hashlib
import zlib
from PIL import Image
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init

colorama_init(autoreset=True)



# ========== SETUP ========== #
MAGIC = b'EMBERON3'  # updated magic to avoid collisions with old files

# New header format (variable-length filename + extension)
# Struct prefix before variable fields:
# magic(8s), comp_method(B), reserved(B),
# orig_size(Q), comp_size(Q), name_len(H), ext_len(H)
HEADER_PREFIX_FMT = '>8sBBQQHH'
HEADER_PREFIX_SIZE = struct.calcsize(HEADER_PREFIX_FMT)
HEADER_PAD_TO = 256  # increased to accommodate filenames

COMP_ZLIB = 1
COMP_NONE = 0

HEADER_RESERVED_BYTE = 0
BYTES_PER_PIXEL = 4

CHUNK_ENCODE_SIZE = 128 * 1024 * 1024
CHUNK_DECODE_SIZE = 64 * 1024 * 1024




# ============ HEADER STUFF =============== #

def pretty_size(num_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def calc_header(orig_size: int, comp_bytes: bytes, filename: str, comp_method: int = COMP_ZLIB) -> bytes:
    name = os.path.splitext(os.path.basename(filename))[0].encode('utf-8')
    ext = os.path.splitext(filename)[1].lstrip('.').encode('utf-8')

    if len(name) > 175 or len(ext) > 20:
        raise ValueError("Filename or extension too long for header storage")

    sha = hashlib.sha256()
    sha.update(f"{orig_size}:".encode())
    sha.update(comp_bytes)
    digest = sha.digest()

    prefix = struct.pack(
        HEADER_PREFIX_FMT,
        MAGIC,
        comp_method,
        HEADER_RESERVED_BYTE,
        orig_size,
        len(comp_bytes),
        len(name),
        len(ext)
    )

    header = prefix + name + ext + digest

    if len(header) > HEADER_PAD_TO:
        raise RuntimeError("header unexpectedly too large")
    header += b'\x00' * (HEADER_PAD_TO - len(header))
    return header


def parse_header(raw: bytes):
    if len(raw) < HEADER_PAD_TO:
        raise RuntimeError("image too small to contain header")

    prefix = raw[:HEADER_PREFIX_SIZE]
    magic, comp_method, reserved, orig_size, comp_size, name_len, ext_len = struct.unpack(HEADER_PREFIX_FMT, prefix)

    pos = HEADER_PREFIX_SIZE
    name = raw[pos:pos+name_len].decode('utf-8')

    pos += name_len
    ext = raw[pos:pos+ext_len].decode('utf-8')

    pos += ext_len
    digest = raw[pos:pos+32]


    #a bit of stuff for the header: 
    #unsigned short = 2 bytes → max value = 65535, 
    #but 8 (magic) + 1 (comp_method) + 1 (reserved) + 8 (orig_size) + 8 (comp_size) + 2 (name_len) + 2 (ext_len) = 30 bytes
    #header has total of 256 bytes, so 256 total - 30 prefix - 32 digest = 194 bytes
    #assuming that a extension is present(4 bytes)
    #THEORETICAL LIMIT FOR THE NAME STORED IN THE HEADER IS 190 CHARACTERS (190 bytes)
    return {
        "magic": magic,
        "comp_method": comp_method,
        "reserved": reserved,
        "orig_size": orig_size,
        "comp_size": comp_size,
        "name": name,  
        "ext": ext,
        "digest": digest
    }


def print_header_info(h):
    print(Fore.CYAN + "[Header Information]")
    print(f" Magic: {h['magic']}")
    print(f" Compression: {'zlib' if h['comp_method'] == COMP_ZLIB else 'none'}")
    print(f" Original size: {pretty_size(h['orig_size'])}")
    print(f" Compressed size: {pretty_size(h['comp_size'])}")
    print(f" Original filename and extension: {h['name']}.{h['ext']}")
    print(f" SHA-256: {h['digest'].hex()}")
    print(f" Reserved: {h['reserved']}")


def choose_dimensions(num_pixels: int):
    w = int(math.ceil(math.sqrt(num_pixels)))
    h = int(math.ceil(num_pixels / w))
    return w, h


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

    header = calc_header(orig_size, comp_bytes, filename=in_path, comp_method=comp_method)
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


def decode_png_to_file(in_path: str, out_path: str = None):
    img = Image.open(in_path)
    if img.mode != 'RGBA':
        raise RuntimeError(f"Unsupported PNG mode: {img.mode}, expected RGBA")

    raw = img.tobytes("raw", "RGBA")
    header_data = parse_header(raw)

    if header_data["magic"] != MAGIC:
        raise RuntimeError("magic mismatch: not a file produced by this encoder")

    comp_start = HEADER_PAD_TO
    comp_end = comp_start + header_data["comp_size"]
    if comp_end > len(raw):
        raise RuntimeError("image does not contain full compressed payload (truncated?)")

    comp_bytes = raw[comp_start:comp_end]

    sha = hashlib.sha256()
    sha.update(f"{header_data['orig_size']}:".encode())
    sha.update(comp_bytes)
    if sha.digest() != header_data["digest"]:
        raise RuntimeError("SHA-256 mismatch: data corrupted or wrong image")

    if not out_path:
        out_path = f"{header_data['name']}.{header_data['ext']}" if header_data["ext"] else header_data["name"]

    with open(out_path, 'wb') as f_out, tqdm(total=header_data["orig_size"], unit='B', unit_scale=True, desc="Decompressing") as pbar:
        if header_data["comp_method"] == COMP_ZLIB:
            d = zlib.decompressobj()
            for i in range(0, len(comp_bytes), CHUNK_DECODE_SIZE):
                chunk = comp_bytes[i:i+CHUNK_DECODE_SIZE]
                data = d.decompress(chunk)
                f_out.write(data)
                pbar.update(len(data))
            f_out.write(d.flush())
        elif header_data["comp_method"] == COMP_NONE:
            f_out.write(comp_bytes)
            pbar.update(len(comp_bytes))
        else:
            raise RuntimeError(f"unknown compression method {header_data['comp_method']}")

    print(Fore.GREEN + f"✓ Decoded {in_path} -> {out_path} ({pretty_size(header_data['orig_size'])})")


def main():
    p = argparse.ArgumentParser(description="Encode any file into PNG and decode it back.")
    sp = p.add_subparsers(dest='cmd', required=True)

    enc = sp.add_parser('encode', help='Encode a file to PNG')
    enc.add_argument('input')
    enc.add_argument('output')
    enc.add_argument('-l', '--level', type=int, default=9, help='zlib compression level 0-9')
    enc.add_argument('--no-compress', action='store_true')

    dec = sp.add_parser('decode', help='Decode PNG to original file')
    dec.add_argument('input')
    dec.add_argument('output', nargs='?', help='Optional output filename (defaults to original stored name)')

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
            h = parse_header(raw)
            print_header_info(h)
    except Exception as e:
        print(Fore.RED + f"Error: {e}")

if __name__ == '__main__':
    main()
