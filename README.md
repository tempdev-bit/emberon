# emberon v2.5 🦕
 Emberon, a weird tool I made for converting **ANY** file into a .png for some reason.

![logo](logo.jpeg)

 It is a Python tool that lets you turn any binary file inside a PNG image in a fully lossless way — and later recover it perfectly.
 
 TESTED WITH:- .txt, .zip, .AppImage (more will be done later)
 
 It packs your file’s bytes directly into pixels, optionally compresses them, and stores integrity information so decoding is safe.
 
  Great for:
 - Sharing binary data via image-friendly platforms.
 - Preserving files inside an a png (archive type)
 - Piracy.
 
 FULL 150 PARAGRAPHS OF LOREM IPSUM LOOKS LIKE THIS: (original text and image is in repo)
 
 Encoded lorem_ipsum.txt (90195 bytes) -> lorem_ipsum_encoded2.png (78x78, 6084 pixels).
 Compression: zlib (orig 90195(~90kb) -> comp 24139(~24kb) bytes)
 
 
![lorem_ipsum_1000_paragraphs](encoded.png)

---

## commands 💾
 
 ### Encoding images
 ```py
 python3 emberon.py encode <filename> <output_png_name>.png
 ```
 ### Decoding images
 v2.5
 ```py
 python3 emberon.py decode <encoded_file>.png <optional_output_filename>
 ```
 ### Inspect (Important)
 ```py
 python3 emberon.py inspect <encoded_file>.png
 ```

---

## usage. 💽
 
 ### Encoding 
  See above for the actual command.
 
 ### Decoding
  You might want to use the 'inspect' command before decoding to ensure that .png is actually a valid .png file (check for b'EMBERONV3' in output)
 
  See above for the actual command
 
 ### Inspecting 🔮
  *VERY* important new feture implemented in v2. 
 
  It gives: The MAGIC string (used by emberon to identify that the file was made by emberon), the compression method, original size, compressed size and the SHA-256 (along with the reserved tag)
 
  For example, this is the header information for encoded.png in the repo:
  ```MD
  [Header Information]
   Magic: b'EMBERON3'
   Compression: zlib
   Original size: 88.08 KB
   Compressed size: 23.57 KB
   Original filename: lorem_ipsum.txt
   SHA-256: abb5f85061b5860a88f9676aa31577179d4bd268ed9f489e9fac52e63434ab9f
   Reserved: 0
  ```
 
 ### Flags 🫥
  - -l', '--level' - Sets the zlib compression level (default: 6, range: 0 - 9)
  - --no-compress' - Completely skips zlib compression; stores the EXACT data you give it
 
  (note: setting --level 0 is practically the same as --no-compress, zlib doesn't compress data at level 0 BUT the zlib header/structure will be around the data.)
 
---

## Why YOU should you emberon 🎁
 For sharing files and stuff with your friends.

 If you want to make a large digital archive

 Piracy.

 (Please avoid using this until v3, it's going to finalize the header structure.)

---

## features?? 🔎
 - **Any file type** — works with text, binaries, archives, executables, etc.
 - **Lossless PNG output** — original data is 100% preserved.
 - **Optional zlib compression** for smaller images.
 - **Built-in integrity check** (SHA-256).
 - **Shows Error if image was changed**
 - **Simple encode/decode commands**.
 - **Near-square image dimensions** for practicality.

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
2. Install Pillow, Tqdm, Colorama OR use req,txt >>

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

 - Better errors & hints (!)
 - Alternate compression algorithms (!)
 - Configurable aspect ratio (?)
 - Parallel chunk compression (*)
 - Encryption with AES-256 (*)
 - Checksum redundancy (*)
 - Multi-file support (?)
 - GUI fork (?)

---

## technical stuff. ⚓️ (W.I.P)
 For the header in the .png's:
 
 ```
+-----------------+----------+------------------------------------------------------+
| Field           | Size     | Description                                          |
+-----------------+----------+------------------------------------------------------+
| MAGIC           | 8 bytes  | Identifier + version (b'EMBERON3')                   |
| comp_method     | 1 byte   | Compression type (0=none, 1=zlib)                    |
| reserved        | 1 byte   | Reserved for future features                         |
| orig_size       | 8 bytes  | Original uncompressed file size (bytes)              |
| comp_size       | 8 bytes  | Compressed data size (bytes)                         |
| name_len        | 2 bytes  | Length of original filename (no extension) in bytes  |
| ext_len         | 2 bytes  | Length of original file extension (no dot) in bytes  |
| filename        | var.     | UTF-8 encoded original filename                      |
| extension       | var.     | UTF-8 encoded file extension                         |
| sha256_digest   | 32 bytes | SHA-256 hash of orig_size followed by data bytes     |
| padding         | var.     | Zero padding to reach 256 bytes total header size    |
+-----------------+----------+------------------------------------------------------+
TOTAL: 256 bytes (including padding)
```


<sup> Made with ❤️ by solar. <sup>


