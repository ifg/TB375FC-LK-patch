#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 TB375FC LK patch tool contributors
"""
TB375FC_LK_patch.py

Converts the stock lk.img from an official firmware package into a build that
skips the bootloader region check.

Usage:
    python3 TB375FC_LK_patch.py <stock lk.img> [-o OUTPUT]

The stock file is identified by checksum, the matching patch data is applied,
and the result is checked against the reference build for that stock file.
Nothing is written unless both checks pass.

Supported stock files are listed in KNOWN. Anything else is not supported:

    python3 TB375FC_LK_patch.py --list

No MTK firmware is included here; obtain the official package yourself.
"""
import argparse
import hashlib
import struct
import sys

__version__ = "1.1.0"

# The supported builds share one layout, so the edit positions below apply to
# all of them; each stock file brings its own data block for edit 2.
_E1_OFF = 0x1065C
_E1_OLD = b"\xff\x03\x01\xd1"
_E1_NEW = b"\xc0\x03\x5f\xd6"
_E2_OFF = 0x103BC0
_E2_LEN = 995         # bytes kept from the stock file
_E2_OLD_PAD = 1008    # old total size of that area
_E2_NEW_PAD = 1088    # new total size, after the inserted data
_E3_OFF = 0x1039C0
_E3_VAL = 1085        # logical size recorded for the new area

KNOWN = [
    {
        "label": "ZUX 1.5.10.103 (TB375FC, CN)",
        "stock_md5": "d7c52a4508828df41b43742641c8968e",
        "data": (
            "a05806076086769316020403210095d997ba0e81289aac0e65aaf0d5e1b2b24fff31d90307"
            "1da2d0fffb8b6622a7060760867693160201032100bb7cb135755fb921eadeabb65e8a6867"
            "6549be7684a8c4196f41dda9eeb8d3d0"),
        "patched_md5": "9f1076942879fbf9e588e2a516c5b8da",
    },
    {
        "label": "ZUI 17.5.10.084 (TB373FU, global)",
        "stock_md5": "c4a48acd946962d7ad9c4f11f52d49b6",
        "data": (
            "a05806076086769316020403210095d997ba0e81289aac0e65aaf0d5e1b2b24fff31d90307"
            "1da2d0fffb8b6622a7060760867693160201032100a4fa2095475ed73fcb0c17502290a35d"
            "4b1a354a10039f046332cb038829d71c"),
        "patched_md5": "e2f258b200bec58694e9e531fbba8a61",
    },
]


def die(msg):
    print("[ABORT] " + msg, file=sys.stderr)
    sys.exit(1)


def find_entry(digest):
    for entry in KNOWN:
        if entry["stock_md5"] == digest:
            return entry
    return None


def main():
    ap = argparse.ArgumentParser(
        description="Patch a stock lk.img (TB375FC / TB373FU).")
    ap.add_argument("image", nargs="?", help="stock lk.img from an official package")
    ap.add_argument("-o", "--out", default="lk_patched.img",
                    help="output file (default: lk_patched.img)")
    ap.add_argument("--list", action="store_true",
                    help="list the supported stock files and exit")
    ap.add_argument("--version", action="version",
                    version="TB375FC_LK_patch {}".format(__version__))
    a = ap.parse_args()

    if a.list:
        for e in KNOWN:
            print("{}  {}  ->  {}".format(e["label"], e["stock_md5"],
                                          e["patched_md5"]))
        return

    if not a.image:
        die("no input file given; try --help, or --list to see what is supported")

    print("TB375FC_LK_patch {}".format(__version__), flush=True)
    data = open(a.image, "rb").read()
    digest = hashlib.md5(data).hexdigest()
    entry = find_entry(digest)
    if entry is None:
        die("unrecognised stock lk.img\n"
            "  md5 {}\n"
            "  run --list to see the supported files."
            .format(digest))
    if data[_E1_OFF:_E1_OFF + 4] != _E1_OLD:
        die("0x{:x} does not hold the expected bytes; refusing to touch this "
            "file.".format(_E1_OFF))
    print("[1/3] input verified: {}".format(entry["label"]))

    blob = bytes.fromhex(entry["data"])
    area = blob + data[_E2_OFF:_E2_OFF + _E2_LEN]
    area += b"\x00" * (_E2_NEW_PAD - len(area))
    patched = bytearray(data[:_E2_OFF] + area + data[_E2_OFF + _E2_OLD_PAD:])
    struct.pack_into("<I", patched, _E3_OFF + 4, _E3_VAL)
    patched[_E1_OFF:_E1_OFF + 4] = _E1_NEW
    patched = bytes(patched)
    print("[2/3] patch applied")

    digest = hashlib.md5(patched).hexdigest()
    if digest != entry["patched_md5"]:
        die("output does not match the reference build (md5 {}); do NOT use it."
            .format(digest))
    print("[3/3] output verified against reference build")

    open(a.out, "wb").write(patched)
    print("\nDone: {}  (md5 {})".format(a.out, hashlib.md5(patched).hexdigest()))
    print("Write it to the lk_a (and lk_b) partition with SP Flash Tool "
          "(Download Only) or equivalent.")


if __name__ == "__main__":
    main()
