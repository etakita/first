#!/usr/bin/env python3
"""D1: запись line-in приёмника в wav.

Команды:
  python d1_record.py --probe          # 3-с пробная запись на ВСЕХ входах:
                                       #   какой вход живой видно по peak
  python d1_record.py --list           # список устройств
  python d1_record.py -d <n> -t 45 -o d1_107_silence.wav
"""
import argparse
import sys

import numpy as np
import sounddevice as sd
from scipy.io import wavfile

FS = 44100


def inputs():
    dev = sd.query_devices()
    return [(i, d["name"]) for i, d in enumerate(dev) if d["max_input_channels"] > 0]


def probe():
    print("Пробная запись 3 с на каждом входе (включите музыку, если хотите увидеть сигнал):")
    for i, name in inputs():
        try:
            data, _ = sd.read(int(3 * FS), samplerate=FS, channels=1, dtype="float32", device=i)
            x = data[:, 0]
            peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
            mark = "  <-- сигнал" if peak > -60 else ""
            print(f"  {i}: {name}   peak {peak:7.1f} dBFS{mark}")
        except Exception as e:
            print(f"  {i}: {name}   ERROR {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("-d", type=int, default=None, help="входное устройство (см. --probe)")
    ap.add_argument("-t", type=float, default=45.0, help="длительность, с (по умолчанию 45)")
    ap.add_argument("-o", help="имя выходного wav")
    a = ap.parse_args()

    if a.list:
        for i, n in inputs():
            print(f"  {i}: {n}")
        return
    if a.probe:
        probe()
        return
    if not a.o:
        ap.error("нужно -o <файл.wav> (или --probe / --list)")

    if a.d is None:
        cands = [i for i, n in inputs() if "realtek" in n.lower()]
        if len(cands) == 1:
            a.d = cands[0]
        else:
            print("Несколько/нет Realtek-входов. Запустите:  python d1_record.py --probe")
            print("и укажите живой вход через -d.")
            sys.exit(1)

    dev = sd.query_devices()
    print(f"Запись {a.t:.0f} с с устройства {a.d} ({dev[a.d]['name']}) -> {a.o}")
    print("Идёт запись, не трогайте звук...")
    data, _ = sd.read(int(a.t * FS), samplerate=FS, channels=1, dtype="float32", device=a.d)
    x = data[:, 0]
    wavfile.write(a.o, FS, x)
    peak = 20 * np.log10(np.max(np.abs(x)) + 1e-12)
    rms = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
    print(f"Сохранено {a.o}: {len(x) / FS:.1f} с, peak {peak:.1f} dBFS, rms {rms:.1f} dBFS")


if __name__ == "__main__":
    main()
