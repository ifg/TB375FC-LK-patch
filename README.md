# TB375FC LK patch tool

Command-line tool that converts a **stock `lk.img` from an official Lenovo
firmware package** into a build that skips the region check, so a TB375FC can
boot TB373FU (global / international) system images from the `17.5.10.084` line
onward **without changing the device's region**.

Normal use: take the `image/lk.img` from the package you are about to flash
(one of the supported builds), patch it, and write it back in place of that
package's own file. The `lk.img` from the Chinese ZUX 1.5.10.103 toolkit works
too, for people who already have it.

This repository ships **no MTK firmware**. You supply the official package
yourself; the tool transforms it and verifies the result.

This is aimed at people who already flash MediaTek devices. If you do not, read
the community threads for this tablet first and come back.

## What it is for

`ZUI 17.5.10.084` and later rotate the AVB root key to RSA-4096 and add a
region check to the bootloader: on boot it verifies the image's region against
the device's own. On a PRC (China) TB375FC a mismatch stops the boot and puts
the device into what is commonly called **"Red State"** — instead of starting
Android, the tablet shows a failure / cannot-boot screen. That is why flashing a
global ROM over the stock Chinese bootloader on a PRC unit fails.

The bootloaders of that same line already carry the new RSA-4096 root key, so
the AVB stage is not the problem; the only thing that still blocks a global ROM
is the region check itself. This tool produces a version of such a bootloader
with that check skipped, so the global ROM boots on a unit whose region is
unchanged. The Chinese ZUX 1.5.10.103 bootloader is in the same position and is
supported as an alternative input.

## Requirements

- A Lenovo **TB375FC** (Xiaoxin Pad Pro 12.7, MT6897). Do **not** run this on
  any other model.
- A supported stock `lk.img` — `python3 TB375FC_LK_patch.py --list` prints
  them. Currently: ZUI 17.5.10.084 (global) and ZUX 1.5.10.103 (CN).
  **Anything else is not supported.**
- System images from the `17.5.10.084` generation or later, never earlier.
  Earlier global builds — `17.0.04.266` (Android 15) and `17.5.10.020` /
  `.043` / `.057` — are signed with the old AVB root key and will not boot
  behind this bootloader.
- Python 3 (standard library only, no third-party packages).
- No bootloader unlock is needed.

## Usage

```bash
python3 TB375FC_LK_patch.py image/lk.img      # from the package you will flash
```

The tool runs three steps and writes nothing unless the checks pass:

1. The input is a stock `lk.img` it knows, matched by checksum.
2. The patch is applied.
3. The output matches the reference build for that input (checksum).

On success it produces `lk_patched.img`: 3,372,448 bytes, i.e. the stock image
plus 80 bytes. The `lk` partition is 16 MB, so there is ample room.

Current version: `1.1.0` — `python3 TB375FC_LK_patch.py --version` prints it, and
it appears as the first line of every run. Quote it when reporting problems.
`--list` prints the supported stock files and what each should produce:

| Stock input | md5 | Patched output md5 |
|---|---|---|
| ZUI 17.5.10.084, global (`TB373FU`) | `c4a48acd946962d7ad9c4f11f52d49b6` | `e2f258b200bec58694e9e531fbba8a61` |
| ZUX 1.5.10.103, CN (`TB375FC`) | `d7c52a4508828df41b43742641c8968e` | `9f1076942879fbf9e588e2a516c5b8da` |

That list is the support matrix. Anything not listed is not supported.

## Flashing

Everything below comes from the **global** package — including the `lk.img` you
patch, so one package is enough.

Use the SP Flash Tool that comes inside the global package
(`SPFlashToolV6.exe`); on Linux, the same writes go through mtkclient instead.

Do not open the `flash.xml` that sits in the package root — it belongs to a
different chip and is not the configuration for this tablet. The right one is
`image/download_agent/flash.xml`; it points at a scatter named
`image/MT6897_Android_scatter.xml`. From the 17.5.10.084 line the packages ship
that scatter encrypted (`MT6897_Android_scatter.t` / `.x`), so put a decrypted
scatter for your storage size at exactly `image/MT6897_Android_scatter.xml`
before loading `flash.xml` — or load the decrypted scatter directly in the
tool.

Then, in **Download Only** mode:

1. Load the package whose `lk.img` you patched. Do not mix in an older global
   package: those will not boot behind this bootloader.
2. Set the **`lk_a`** row's file to `lk_patched.img` and keep that row
   selected. Do not let the package write its own `lk`: if the stock `lk` lands,
   the patched bootloader is gone and the tablet goes back to Red State. (The
   package has no file at all for `lk_b`. If you want both slots covered up
   front, community guides cover this by editing the decrypted scatter to map
   `lk_b` to the patched image as well.)
3. **Deselect `preloader_a` and `preloader_b`** (both are on by default).
   Nothing is gained by writing them — the Chinese and global preloaders are the
   same program built on different dates — and a failed or interrupted preloader
   write costs you the normal, preloader-level download mode, leaving only the
   BootROM level to recover from.
4. **Deselect `userdata`** if you want to keep your files (also on by default).
   Writing it erases everything on the tablet.
5. Leave the rest of the list as the package sets it, then run the download.

**Never run `Rescue.cmd` from the package, and never use Firmware Upgrade
mode.** On a Chinese unit that touches the preloader and the partition table
and leaves the tablet unbootable.

`fastboot flash` is not the right path here: fastboot refuses to write while
the device is locked.

You can verify your output against the reference checksum for your input; the
table in [Usage](#usage) lists them, and the tool checks it for you.

## Limitations

- **Not a full conversion.** This only makes the bootloader skip its region
  check; it does not rewrite the device's region data. It is a compatibility
  shim, not the same as a genuine global unit.
- **Flashing the package's `userdata` erases it.** See step 4 above.
- **Anything that writes the stock `lk` undoes it.** That includes a system
  update: an OTA fills the inactive slot, then boots it — and that slot now
  holds the stock `lk`, so the tablet goes back to Red State. The symptom is the
  error screen appearing and the tablet restarting by itself every few seconds.
  Two ways out, in this order:
  1. Try fastboot (power off, then power on holding **Volume Up**, pick fastboot
     at the logo). If it comes up, `fastboot getvar current-slot`, then
     `fastboot set_active a` (or `b`) to boot the slot that still has the patched
     image, then `fastboot reboot`. This leaves you on the older system build.
  2. If fastboot does not come up, the package cannot help — it has no file for
     `lk_b`, and after an update the patched image is not in the active slot.
     Use a partition writer such as mtkclient and write `lk_patched.img` to
     **both** `lk_a` and `lk_b`, since without fastboot there is no easy way to
     tell which slot is active. That takes the update and keeps the patch.
- **If something goes wrong, recover in Download mode, not fastboot.** Only one
  of the two failure modes gives you fastboot:
  - The bootloader runs but Android does not start (stuck at the boot
    animation): fastboot is reachable — power off, power on holding **Volume
    Up**, pick fastboot at the logo — then check the slot as described above.
  - The tablet does not come up at all (no logo, no fastboot): the bootloader
    image was rejected, so there is no fastboot to enter. Use SP Flash Tool in
    **Download mode**; that interface sits below the bootloader and connects
    even when the tablet will not boot. Note that writing the stock `lk.img`
    back does not by itself give you a working tablet: the stock bootloader
    refuses a global system while the region is unchanged, so you land in Red
    State again (an older-generation CN `lk` lands there too, for a different
    reason). To get back to a working tablet, re-flash the CN package from the
    full archive you started from, SP Flash Tool and scatter included — and
    deselect `userdata` there as well if that data matters to you.
- Fully re-regioning the device is a different procedure and out of scope here.

## Verification status

- Offline: the patched image was run through the same checks the tablet itself
  applies to a bootloader image, on a copy of those checks, and passed. The tool
  also refuses to emit anything that does not match this validated build.
- Not done: this specific image has not been tested end to end on a tablet
  whose region is still stock. Please report results if you try it.

## Disclaimer

Published for interoperability and personal use on hardware you own.

- **No warranty.** The tool and the image it produces come with no warranty of
  any kind, express or implied, including fitness for a particular purpose.
  What is verified here is one specific firmware build against one specific
  device family; anything else may simply not work.
- **You carry the risk.** Writing a bootloader partition can leave the tablet
  unbootable, and recovery is not guaranteed even with the notes below. Damage,
  data loss, a voided warranty, a dropped Widevine level or any other
  consequence is yours. Make a full readback of your own partitions before you
  start — an official package is not a substitute for your device's own data
  (`proinfo`, `nvram`, `persist`, `seccfg`).
- **No firmware is distributed here.** Obtain the official packages yourself
  from official or community mirrors. What you do with them, and whether that
  is lawful where you are, is your responsibility.
- **Not affiliated, not endorsed.** This project has no connection to Lenovo,
  Motorola or MediaTek; product names and trademarks belong to their owners.
  Nothing here is intended to give you access to content, services or
  warranties you are not entitled to.
- **Not a supported product.** There is no support commitment, and no promise
  that these notes stay correct as new firmware is released or that a future
  package will still pair with this patch. Do not rely on any of it for
  anything critical.

## License

MIT — see [`LICENSE`](LICENSE). Its scope, spelled out because a license file
cannot:

- It covers the source in this repository only. Firmware images remain the
  property of their respective owners; nothing here grants rights to them, and
  no firmware is distributed.
- The tool is meant for hardware you own, for interoperability. Rules about
  modifying a device's verification behaviour differ by jurisdiction; complying
  with them is your responsibility.
- Images produced by the tool are not covered by this license.
