# 🎵 Jukebox-python (Maxi Music Box Replica)

[🇨🇿 Česká verze](#-česká-verze) | [🇬🇧 English version](#-english-version)

---

## 🇨🇿 Česká verze

Digitální replika legendárního českého hospodského jukeboxu napsaná v Pythonu. Aplikace je navržena tak, aby běžela jak na klasickém počítači (Windows, Linux, macOS), tak na **Raspberry Pi 4** s připojeným LCD displejem, hardwarovými tlačítky a infračerveným (IR) dálkovým ovládáním.

### ✨ Hlavní funkce
* **Autentické rozhraní:** Rychlé listování podle interpretů, alb, abecedního rejstříku nebo žebříčku **TOP 50** nejhranějších skladeb.
* **Rozdělení knihovny:** Automatická detekce a přepínání mezi **Českou/Slovenskou** a **Zahraniční** hudbou, plus podpora videoklipů.
* **Chytrý skener (`scan.py`):** Automaticky čte ID3 tagy, sjednocuje jména interpretů (odstraňuje duplicity, `feat.`, diakritiku) a stahuje obaly alb online (Deezer, iTunes, CoverArtArchive, volitelně Discogs).
* **Režim Auto-DJ:** Automatické doplňování a přehrávání náhodných skladeb, když je fronta přání prázdná.
* **Flexibilní ovládání:** Podpora klávesnice, myši, 4 fyzických tlačítek na GPIO i 21tlačítkového IR dálkového ovladače.

---

### 💻 Instalace podle operačního systému

#### 1. Stažení projektu
```bash
git clone [https://github.com/TomMiga/Jukebox-python.git](https://github.com/TomMiga/Jukebox-python.git)
cd Jukebox-python