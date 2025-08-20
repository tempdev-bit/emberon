# emberon v2.5 🦕
 Emberon, a weird tool I made for converting **ANY** file into a .png for some reason.

![logo](logo.jpeg)

 It is a Python tool that lets you turn any binary file inside a PNG image in a fully lossless way — and later recover it perfectly.

(NOTE: If you are using [emberon-web](https://emberon.pages.dev), then only use ZLIB!)

 It packs your file’s bytes directly into pixels, optionally compresses them, and stores integrity information so decoding is safe.
 
  Great for:
 - Sharing binary data via image-friendly platforms.
 - Preserving files inside an a png (archive type)
 - Piracy.

---

## size 💾 
 Emberon provides three different compression algorithms. (zlib, zstd, lzma)</br>
 Here's all three compared for lorem_ipsum.txt (150 paargraphs) with MAX compression applied (lossless):

 1. Zlib: 
 ✓ Encoded sample_document.txt -> example_zlib.png [80x79]
   Compression: zlib (orig **88.84** KB → comp **24.41** KB)
   ![zlib_comp](example_zlib.png)

 2. Zstd:
 ✓ Encoded sample_document.txt -> example_zstd.png [79x79]
   Compression: zstd (orig **88.84** KB → comp **23.89** KB)
   ![zstd_comp](example_zstd.png)

 3. Lzma:
 ✓ Encoded sample_document.txt -> example_lzma.png [75x75]
   Compression: lzma (orig **88.84** KB → comp **21.56** KB)
   ![lzma_comp](example_lzma.png)

Lzma has the lowest post-compress file size</br>
CURRENTLY LZMA IS OPTIONAL, USE --ZLIB, --ZSTD FOR THE OTHERS

--- 

## Why YOU should you emberon 🎁
 1. For sharing files and stuff with your friends.

 2. If you want to make a large digital archive

 3. Piracy.

 ~~(Please avoid using this until v3, it's going to finalize the header structure.)~~ v2.5 has finalized the header structure, i.e. ***v2.5 and onwards will probably have no breaking changes***

---

## features?? 🔎
 - **Any file type** — works with text, binaries, archives, executables, etc.
 - **Lossless PNG output** — original data is 100% preserved.
 - **Optional zlib compression** for smaller images.
 - **Built-in integrity check** (SHA-256).
 - **Shows Error if image was changed**
 - **Simple encode/decode commands**.
 - **Near-square image dimensions** for practicality.
 - **Automatic restoration of filename and extension on decoding**
 - **Colored CLI output** because *pretty*
 - **Streaming encode/decode** so that it runs on potato's

---

## commands 💾
 ### Simplified commands
  #### Encoding
  ```py
    # Encode lorem_ipsum.txt -> lorem_ipsum.txt.png
    python emberon.py e lorem_ipsum.txt
  ```

  #### Decoding
  ```py
   # Decode encoded.png -> original name inside header
   python emberon.py d encoded.png
  ```

  #### Inspecting
  ```py
   # Inspect encoded.png
   python emberon.py i encoded.png
  ```
  #### Output name
  Uses the ``` -o ``` tag for setting file names for encoding and decoding </br>
  for example:</br>

  Encoding ->

  ```py
   #Encode lorem_ipsum.txt into a .png with name encoded.png
   python3 emberon.py e example.txt -o example.png

  ```

  Decoding ->
  ```py
   #Decode encoded.png into a .txt with name lorem_ipsum_text.txt
   python emberon.py d encoded.png -o lorem_ipsum_text.txt
  ```
  
 ### Verbose commands
   #### Encoding images
   Is this good yet??
   ```py
    python3 emberon.py encode <filename> -o <optional_output_png_name>.png
   ```
   ***No.*** Don't use these please
   #### Decoding images
   ```py
    python3 emberon.py decode <encoded_file>.png -o <optional_output_filename>
   ```
   #### Inspect (Important)
   Isn't as bad as i thought it would be
   ```py
    python3 emberon.py inspect <encoded_file>.png
  ```
  ####Different compression models
   **use --lzma, --zlib, --zstd for models & -l or --level for setting the level of compression.**

  ### flags. 🫥
   #### -l or --level
   Used to set the level for compression algorithm (scale 0-9) (default:9)</br>
   The larger the level, the more time it will take, although still even at level 9, large files don't take much time.</br>
   USE LEVEL 9 FOR OPTIMIZATION'S SAKE

   #### --no-compress
   avoids compression entirely (don't 'use this, all compression happening is LOSSLESS)
   (note: setting --level 0 is practically the same as --no-compress, zlib doesn't compress data at level 0 BUT the zlib header/structure will be around the data.)
 
---

## usage. 💽
 
 ### Encoding 
  See above for the actual command. </br>
 
  Keywords: encode, e
 
  If no name is provided for output file, it will settle on <filename.extension>.png
 
 ### Decoding
  See above for the actual command </br>

  Keywords: decode, d

  You might want to use the 'inspect' command before decoding to ensure that .png is actually a valid .png file (check for b'EMBERONV3' in output) </br>
  You can pass a name for output file, which is completely optional. (it defaults the names to the original file which was compressed)

 ### Inspecting 🔮
  *VERY* important new feture implemented in v2. 
 
  Keywords: inspect, i

  It gives: The MAGIC string (used by emberon to identify that the file was made by emberon), the compression method, original size, compressed size and the SHA-256 (along with the reserved tag)
 
  For example, this is the header information for encoded.png in the repo:

  ```py
  [Header Information]
   Magic: b'EMBERON3'
   Compression: zlib
   Original size: 88.08 KB
   Compressed size: 23.57 KB
   Original filename: lorem_ipsum.txt
   SHA-256: abb5f85061b5860a88f9676aa31577179d4bd268ed9f489e9fac52e63434ab9f
   Reserved: 0
  ```

---

## What's New in Emberon v2.5 ✨ (W.I.P)
 - **Original filename & extension storage**(Max length: 175; practical limit: 194) — headers now store original file name and extension for automatic restoration on decode.
 - *(Note on above point: name_len and ext_len are stored in 2-byte unsigned shorts (max 65535),but practical limit is 190 bytes for filename if extension is ~4 bytes, due to 256-byte header.)*
 - **Automatic output naming** — if no output filename is specified during decoding, Emberon uses the stored original name + extension.
 - **Expanded header format** — header size increased to 256 bytes to accommodate filename metadata safely.
 - **Updated magic signature** — changed from EMBERON2 → EMBERON3 to avoid accidental decoding of older v2  files.
 - **Unified header parser** — new parser function simplifies inspect and decode commands.
 - **Inspect mode enhancements** — view original filename, extension, and other metadata without decoding.
 - **Safety checks for filename lengths** — prevents oversized metadata from breaking PNG encoding.

---

## What's New in Emberon v2 🎉
- **Streaming encode/decode** — handles very large files without loading them fully into RAM. 
- **PNG mode validation** — ensures you only decode supported RGBA PNGs. 
- **Progress bars** — visible encoding/decoding progress for large files. 
- **Colored CLI output** — errors, warnings, and success messages are now color-coded. 
- **Human-readable sizes** — file sizes shown DYNAMICALLY in KB, MB, GB instead of raw bytes. 
- **Pretty header inspection** — new `inspect` command to view header metadata without decoding. 

---

## Installation ⛓️‍💥

1. Make sure you have **Python 3.7+** installed.
2. Install Pillow, Tqdm, Colorama, Zstandard OR use req,txt >>

```bash
pip install -r req.txt
```
---

## future plans?? 📡
 piracy.

 Notations:
  - (!) - important/definitely/working on currently
  - (?) - maybe
  - (*) - planned, but later

 - Configurable aspect ratio (?)
 - Parallel chunk compression (*)
 - Encryption with AES-256 (*)
 - Checksum redundancy (*)
 - Multi-file support (?)
 - GUI fork (?)

---

## technical stuff. ⚓️ (W.I.P)
 For the header in the .png's:
 
 
 
 | Field             | Size       | Description |
 |-------------------|------------|-------------|
 | **MAGIC**         | 8 bytes    | File signature + version (always `b'EMBERON3'`) |
 | **comp_method**   | 1 byte     | Compression type:<br>• `0` = None<br>• `1` = zlib<br>• `2` = Zstandard (if available)<br>• `3` = LZMA |
 | **reserved**      | 1 byte     | Reserved for future use (always `0`) |
 | **orig_size**     | 8 bytes    | Original, uncompressed file size in bytes |
 | **comp_size**     | 8 bytes    | Compressed data size in bytes |
 | **name_len**      | 2 bytes    | Length (in bytes) of original filename (UTF-8, no extension) |
 | **ext_len**       | 2 bytes    | Length (in bytes) of original file extension (UTF-8, no dot) |
 | **filename**      | variable   | UTF-8 encoded original filename (no extension) |
 | **extension**     | variable   | UTF-8 encoded file extension (no dot) |
 | **sha256_digest** | 32 bytes   | SHA-256 of: ASCII string `"{orig_size}:"` + compressed data bytes |
 | **padding**       | variable   | Zero (`0x00`) padding to align total header size to **256 bytes** |
 
 **Notes:**
 - `HEADER_PREFIX_FMT` = `>8sBBQQHH` (big-endian).
 - `HEADER_PAD_TO` = `256` bytes (total fixed header size, including padding).
 - Maximum filename length: **175 bytes**; maximum extension length: **20 bytes**.
 - The compressed payload begins immediately after the 256-byte header.



<sup> Made with ❤️ by solar. <sup>


