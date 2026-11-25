#!/usr/bin/env python3
"""
Kompletní správce knihovny Maxi Music Box.
Jedním spuštěním:
  1. Naskenuje novou / změněnou hudbu a smaže chybějící soubory
  2. Opraví kódování, rozdělí duety a sjednotí interprety
  3. Dostahuje chybějící obaly alb z iTunes (CZ/US) a MusicBrainz
"""

import os
import config
import library
import sys

def main():
    print("=" * 55)
    print("  MAXI MUSIC BOX – Aktualizace knihovny a obalů")
    print("=" * 55)
    print(f"Složka s hudbou : {config.MUSIC_DIR}")
    print(f"Databáze        : {config.DB_PATH}\n")

    if not os.path.exists(config.MUSIC_DIR):
        print("Chyba: složka s hudbou neexistuje!")
        return

    library.scan_library()

    cmd = "python main.py" if sys.platform == "win32" else "python3 main.py"
    print(f"Vše hotovo! Můžeš spustit jukebox:  {cmd}")


if __name__ == "__main__":
    main()
