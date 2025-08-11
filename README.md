# emberon
Emberon, a weird tool I made for converting any file into a .png for some reason.

It is a Python tool that lets you hide any binary file inside a PNG image in a fully lossless way — and later recover it perfectly.

It packs your file’s bytes directly into pixels, optionally compresses them, and stores integrity information so decoding is safe.

 Great for:
- Sharing binary data via image-friendly platforms.
- Fun steganography-like experiments.
- Preserving files inside an image container format.

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


