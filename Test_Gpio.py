#!/usr/bin/env python3
#Test GPIO pin status (read-only). Run: python3 test_gpio.py
#Really need test cause couldn't find documentation on /dev/gpiomem
#also using gpiozero apparently resets the pins so can't use that

import mmap, os, subprocess

FUNCS = {0: "INPUT", 1: "OUTPUT", 4: "ALT0", 5: "ALT1", 6: "ALT2", 7: "ALT3", 3: "ALT4", 2: "ALT5"}
HEADER = ["3V3", "5V", 2, "5V", 3, "GND", 4, 14, "GND", 15, 17, 18, 27, "GND", 22, 23, "3V3", 24,
          10, "GND", 9, 25, 11, 8, "GND", 7, 0, 1, 5, "GND", 6, 12, 13, "GND", 19, 16, 26, 20, "GND", 21]

def get_header_status():
    fd = os.open("/dev/gpiomem", os.O_RDONLY | os.O_SYNC)
    mem = mmap.mmap(fd, 4096, mmap.MAP_SHARED, mmap.PROT_READ)
    os.close(fd)
    regs = memoryview(mem).cast("I")
    fsel, lev = [regs[i] for i in range(6)], regs[0x34 // 4]
    regs.release(); mem.close()
    return [(p, b, FUNCS[(fsel[b // 10] >> (b % 10 * 3)) & 7], "HIGH" if lev >> b & 1 else "LOW")
            if not isinstance(b, str) else (p, None, b, None)
            for p, b in enumerate(HEADER, 1)]

if __name__ == "__main__":
    print(f"{'PIN':>3} {'BCM':>4} {'FUNCTION':<8} LEVEL     (hash FUNCTION only, not LEVEL)")
    for phys, bcm, func, level in get_header_status():
        print(f"{phys:>3} {'-' if bcm is None else bcm:>4} {func:<8} {level or '-'}")
    print("\nCross-check: pinctrl get   (or raspi-gpio get on older OS)")
    print(subprocess.run(["pinctrl", "get"], capture_output=True, text=True).stdout.strip()[:400])