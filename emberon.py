# emberon.py - v2.5
# Encode any file into a lossless PNG image and decode it back.
# Default compression: Zstandard (zstd), with optional LZMA and zlib.
# Now stores original filename and extension in header.

import argparse
import math
import os
import struct
import hashlib
import zlib
import lzma
from PIL import Image
from tqdm import tqdm
from colorama import Fore, Style, init as colorama_init

# Try to import zstd
try:
    import zstandard as zstd
except ImportError:
    zstd = None

colorama_init(autoreset=True)

# ========== CONSTANTS ==========
MAGIC = b'EMBERON3'

HEADER_PREFIX_FMT = '>8sBBQQHH'
HEADER_PREFIX_SIZE = struct.calcsize(HEADER_PREFIX_FMT)
HEADER_PAD_TO = 256

COMP_NONE = 0
COMP_ZLIB = 1
COMP_ZSTD = 2
COMP_LZMA = 3

HEADER_RESERVED_BYTE = 0
BYTES_PER_PIXEL = 4

CHUNK_ENCODE_SIZE = 128 * 1024 * 1024
CHUNK_DECODE_SIZE = 64 * 1024 * 1024

# Compression registry
COMPRESSORS = {
    COMP_NONE: {
        "name": "none",
        "compress": lambda data, level: data,
        "decompress": lambda data: data
    },
    COMP_ZLIB: {
        "name": "zlib",
        "compress": lambda data, level: zlib.compress(data, level),
        "decompress": zlib.decompress
    },
    COMP_LZMA: {
        "name": "lzma",
        "compress": lambda data, level: lzma.compress(data, preset=level),
        "decompress": lzma.decompress
    },
}

if zstd:
    COMPRESSORS[COMP_ZSTD] = {
        "name": "zstd",
        "compress": lambda data, level: zstd.ZstdCompressor(level=level).compress(data),
        "decompress": lambda data: zstd.ZstdDecompressor().decompress(data)
    }

# ========== UTILS ==========
def pretty_size(num_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"

# ========== HEADER ==========
def calc_header(orig_size: int, comp_bytes: bytes, filename: str, comp_method: int) -> bytes:
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
    print(f" Compression: {COMPRESSORS.get(h['comp_method'], {'name': 'unknown'})['name']}")
    print(f" Original size: {pretty_size(h['orig_size'])}")
    print(f" Compressed size: {pretty_size(h['comp_size'])}")
    print(f" Original filename and extension: {h['name']}.{h['ext']}")
    print(f" SHA-256: {h['digest'].hex()}")
    print(f" Reserved: {h['reserved']}")

# ========== CORE ==========
def choose_dimensions(num_pixels: int):
    w = int(math.ceil(math.sqrt(num_pixels)))
    h = int(math.ceil(num_pixels / w))
    return w, h

def encode_file_to_png(in_path: str, out_path: str, comp_method: int, compress_level: int):
    with open(in_path, 'rb') as f:
        raw_data = f.read()

    comp_func = COMPRESSORS[comp_method]["compress"]
    comp_bytes = comp_func(raw_data, compress_level)

    header = calc_header(len(raw_data), comp_bytes, filename=in_path, comp_method=comp_method)
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
    print(Fore.YELLOW + f"   Compression: {COMPRESSORS[comp_method]['name']} "
                        f"(orig {pretty_size(len(raw_data))} → comp {pretty_size(len(comp_bytes))})")

def decode_png_to_file(in_path: str, out_path: str = None):
    img = Image.open(in_path)
    if img.mode != 'RGBA':
        raise RuntimeError(f"Unsupported PNG mode: {img.mode}, expected RGBA")

    raw = img.tobytes("raw", "RGBA")
    header_data = parse_header(raw)

    if header_data["magic"] != MAGIC:
        raise RuntimeError("File is not a valid Emberon PNG")

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

    if header_data["comp_method"] not in COMPRESSORS:
        raise RuntimeError(f"Unsupported compression method {header_data['comp_method']}")

    dec_func = COMPRESSORS[header_data["comp_method"]]["decompress"]
    with open(out_path, 'wb') as f_out:
        data = dec_func(comp_bytes)
        f_out.write(data)

    print(Fore.GREEN + f"✓ Decoded {in_path} -> {out_path} ({pretty_size(header_data['orig_size'])})")

# ========== CLI ==========
def main():
    p = argparse.ArgumentParser(description="Encode/decode files into lossless PNG images.")
    sp = p.add_subparsers(dest='cmd', required=True)

    # Encode
    enc = sp.add_parser("e", help="Encode a file to PNG")
    enc.add_argument("input", help="Input file")
    enc.add_argument("-o", "--output", help="Output PNG file")
    enc.add_argument("--lzma", action="store_true", help="Use LZMA compression")
    enc.add_argument("--zlib", action="store_true", help="Use zlib compression")
    enc.add_argument("--no-compress", action="store_true", help="Disable compression")
    enc.add_argument("-l", "--level", type=int, default=6, help="Compression level")

    # Decode
    dec = sp.add_parser("d", help="Decode PNG to file")
    dec.add_argument("input", help="Input PNG file")
    dec.add_argument("-o", "--output", help="Output file")

    # Inspect
    insp = sp.add_parser("i", help="Inspect PNG header")
    insp.add_argument("input", help="Input PNG file")

    args = p.parse_args()

    try:
        if args.cmd == "e":
            if not os.path.isfile(args.input):
                raise SystemExit(Fore.RED + "Input file not found")
            if args.lzma:
                comp_method = COMP_LZMA
            elif args.zlib:
                comp_method = COMP_ZLIB
            elif args.no_compress:
                comp_method = COMP_NONE
            else:
                if zstd:
                    comp_method = COMP_ZSTD
                else:
                    print(Fore.YELLOW + "zstd not available, falling back to zlib")
                    comp_method = COMP_ZLIB
            output_file = args.output or (args.input + ".png")
            encode_file_to_png(args.input, output_file, comp_method, args.level)

        elif args.cmd == "d":
            if not os.path.isfile(args.input):
                raise SystemExit(Fore.RED + "Input file not found")
            decode_png_to_file(args.input, args.output)

        elif args.cmd == "i":
            if not os.path.isfile(args.input):
                raise SystemExit(Fore.RED + "Input file not found")
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
