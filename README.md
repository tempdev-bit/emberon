# emberon
Emberon, a weird tool I made for converting any file into a .png for some reason.

![logo](logo.jpeg)

It is a Python tool that lets you hide any binary file inside a PNG image in a fully lossless way — and later recover it perfectly.

TESTED WITH:- .txt, .zip, .png (more will be done later)

It packs your file’s bytes directly into pixels, optionally compresses them, and stores integrity information so decoding is safe.

 Great for:
- Sharing binary data via image-friendly platforms.
- Fun steganography-like experiments.
- Preserving files inside an image container format.

FULL 150 PARAGRAPHS OF LOREM IPSUM LOOKS LIKE THIS: (original text and image is in repo)

Encoded lorem_ipsum.txt (90195 bytes) -> lorem_ipsum_encoded2.png (78x78, 6084 pixels).
Compression: zlib (orig 90195(~90kb) -> comp 24139(~24kb) bytes)


![lorem_ipsum_1000_paragraphs](lorem_ipsum_encoded.png)


---

## Why YOU should you emberon
 Don't. I made this in 1 hr as a fun project, it's still very basic and not very good

---

## features??
 - **Any file type** — works with text, binaries, archives, executables, etc.
- **Lossless PNG output** — original data is 100% preserved.
- **Optional zlib compression** for smaller images.
- **Built-in integrity check** (SHA-256).
- **Shows Error if image was changed**
- **Simple encode/decode commands**.
- **Near-square image dimensions** for practicality.

---

## Installation

1. Make sure you have **Python 3.7+** installed.
2. Install the only required dependency ([Pillow](https://pypi.org/project/Pillow/)):

```bash
pip install pillow
```
---

<sup> Made with ❤️ by solar. <sup>


