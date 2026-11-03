#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 TB375FC LK patch tool contributors
"""
TB375FC_LK_patch.py

Converts the stock lk.img from the official TB375FC ZUX 1.5.10.103 firmware
package into the region-check-disabled variant.

Usage:
    python3 TB375FC_LK_patch.py <stock_lk.img> [-o OUTPUT]

Steps:
    1. Verify the input matches the stock ZUX 1.5.10.103 lk.img (md5).
    2. Apply the patch (byte-level, fully deterministic).
    3. Verify the result matches the expected reference build (md5).

The tool aborts and writes nothing if any check fails.
No MTK firmware is included here; obtain the official package yourself.
"""
import argparse
import hashlib
import struct
import sys

__version__ = "1.0.0"

FACTORY_MD5 = "d7c52a4508828df41b43742641c8968e"
REF_MD5 = "9f1076942879fbf9e588e2a516c5b8da"

_OFF_A = 0x1065C
_OFF_B = 0x103BC0
_OFF_C = 0x1039C0
_A_OLD = b"\xff\x03\x01\xd1"
_A_NEW = b"\xc0\x03\x5f\xd6"
_B_BLOCK = bytes.fromhex(
    "a05806076086769316020403210095d997ba0e81289aac0e65aaf0d5e1b2b24fff31d903071da2d0fffb8b6622a7060760867693160201"
    "032100bb7cb135755fb921eadeabb65e8a68676549be7684a8c4196f41dda9eeb8d3d0")


def die(msg):
    print("[ABORT] " + msg, file=sys.stderr)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(
        description="Patch the stock ZUX 1.5.10.103 lk.img (TB375FC).")
    ap.add_argument("image", help="stock lk.img from the official package")
    ap.add_argument("-o", "--out", default="lk103_patched.img",
                    help="output file (default: lk103_patched.img)")
    ap.add_argument("--version", action="version",
                    version="TB375FC_LK_patch {}".format(__version__))
    a = ap.parse_args()
    out = a.out

    print("TB375FC_LK_patch {}".format(__version__), flush=True)
    data = open(a.image, "rb").read()
    got = hashlib.md5(data).hexdigest()
    if got != FACTORY_MD5 or data[_OFF_A:_OFF_A + 4] != _A_OLD:
        die("input is not the stock ZUX 1.5.10.103 lk.img\n"
            "  expected md5 {}\n"
            "  got      md5 {}".format(FACTORY_MD5, got))
    print("[1/3] input verified: stock ZUX 1.5.10.103 lk.img")

    buf = bytearray(data[:_OFF_B] + _B_BLOCK + data[_OFF_B:_OFF_B + 995]
                    + b"\x00" * 3 + data[_OFF_B + 1008:])
    struct.pack_into("<I", buf, _OFF_C + 4, len(_B_BLOCK) + 995)
    buf[_OFF_A:_OFF_A + 4] = _A_NEW
    patched = bytes(buf)
    print("[2/3] patch applied")

    got = hashlib.md5(patched).hexdigest()
    if got != REF_MD5:
        die("output does not match the reference build (md5 {}); do NOT use it."
            .format(got))
    print("[3/3] output verified against reference build")

    open(out, "wb").write(patched)
    print("\nDone: {}  (md5 {})".format(out, hashlib.md5(patched).hexdigest()))
    print("Write it to the lk_a (and lk_b) partition with SP Flash Tool "
          "(Download Only) or equivalent.")


if __name__ == "__main__":
    main()
