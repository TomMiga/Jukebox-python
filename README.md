Markdown
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
2. Instalace závislostí (Python 3.9+)
🪟 Windows:

Nainstaluj Python 3 (zaškrtni Add Python to PATH) a přehrávač MPV (nebo VLC).

V příkazovém řádku (PowerShell) nainstaluj Python knihovny:

PowerShell
pip install pygame mutagen Pillow requests python-mpv
🐧 Linux (Ubuntu / Debian / Raspberry Pi OS):

Bash
sudo apt update
sudo apt install -y python3-pip python3-pygame python3-pil python3-requests libmpv-dev mpv
pip3 install mutagen python-mpv --break-system-packages
🍎 macOS:

Pomocí Homebrew nainstaluj Python a MPV:

Bash
brew install python mpv
Nainstaluj Python balíčky:

Bash
pip3 install pygame mutagen Pillow requests python-mpv
🚀 První spuštění (ukázková knihovna)
Součástí repozitáře jsou dvě volně šiřitelné ukázkové skladby ve složce music/, na kterých si můžeš jukebox okamžitě vyzkoušet:

Naskenování hudby a stažení obalů alb:

Bash
python scan.py
(Volitelně: pro stahování obalů i z Discogs vlož svůj bezplatný token do config.py do proměnné DISCOGS_TOKEN.)

Spuštění jukeboxu:

Bash
python main.py
⌨️ Ovládání přes klávesnici
Klávesa	Funkce
Šipka Nahoru / Dolů	Pohyb v seznamu interpretů, alb nebo skladeb
Šipka Vlevo / Vpravo	Přepínání mezi sloupci / kategoriemi (CZ-SK / Zahraniční / TOP 50 / Videa)
Enter / Mezerník	Výběr interpreta / alba nebo přidání skladby do fronty přání
Backspace / Esc	Návrat o úroveň zpět (z alba na interprety, zavření okna)
N	Přeskočit na další skladbu ve frontě (Next)
P	Pozastavit / obnovit přehrávání (Play / Pause)
+ / -	Zvýšení / snížení hlasitosti
D	Zapnout / vypnout režim Auto-DJ
A – Z	Rychlý skok na interpreta podle počátečního písmene
Q / Alt+F4	Ukončení aplikace
🔌 Zapojení hardwaru pro Raspberry Pi 4 (GPIO + IR)
Jukebox lze vestavět do vlastní skříně s 15,6" LCD displejem, 4 fyzickými tlačítky a infračerveným přijímačem (HX1838 / CHQ1838 / TSOP4838).

⚠️ UPOZORNĚNÍ: IR přijímač i tlačítka zapojuj výhradně na napájecí větev 3,3 V (Pin 1 nebo Pin 17). Připojení 5 V na GPIO piny nenávratně poškodí procesor Raspberry Pi!

Tabulka zapojení pinů (RPi 4)
Součástka	Pin součástky	Pin na Raspberry Pi 4	Poznámka
IR přijímač (HX1838)	OUT (Data)	GPIO 18 (Pin 12)	Datový výstup
IR přijímač (HX1838)	GND	GND (Pin 6)	Společná zem
IR přijímač (HX1838)	VCC	3.3V (Pin 1)	Doporučen RC filtr (100 Ω do série + 100 nF proti GND)
Tlačítko NAHORU	Kontakt 1 / 2	GPIO 5 (Pin 29) / GND	Spíná proti zemi (interní pull-up)
Tlačítko DOLŮ	Kontakt 1 / 2	GPIO 6 (Pin 31) / GND	Spíná proti zemi (interní pull-up)
Tlačítko ENTER	Kontakt 1 / 2	GPIO 13 (Pin 33) / GND	Spíná proti zemi (interní pull-up)
Tlačítko ZPĚT	Kontakt 1 / 2	GPIO 19 (Pin 35) / GND	Spíná proti zemi (interní pull-up)
Aktivace IR přijímače v Raspberry Pi OS
Do konfiguračního souboru /boot/firmware/config.txt (u starších verzí /boot/config.txt) přidej na konec řádek:

Ini, TOML
dtoverlay=gpio-ir,gpio_pin=18
Po restartu Raspberry Pi systém automaticky rozpozná IR přijímač a jednotlivá tlačítka dálkového ovladače lze namapovat pomocí nástroje ir-keytable.

🇬🇧 English Version
A Python-based digital replica of a classic Czech pub jukebox. Designed to run seamlessly on desktop operating systems (Windows, Linux, macOS) as well as on a Raspberry Pi 4 equipped with an LCD screen, physical arcade/panel pushbuttons, and an infrared (IR) remote control.

✨ Key Features
Authentic UI: Fast browsing by artist, album, alphabetical index, or TOP 50 most-played tracks.

Smart Library Organization: Automatic separation of domestic (CZ/SK) and International music, plus music video support.

Intelligent Scanner (scan.py): Reads ID3 tags, normalizes artist names (merging duplicates, stripping feat. tags and diacritics), and automatically fetches album cover art from Deezer, iTunes, CoverArtArchive, and optionally Discogs.

Auto-DJ Mode: Automatically queues and plays random tracks whenever the user request queue is empty.

Flexible Controls: Full support for keyboard, mouse, 4 physical GPIO pushbuttons, and a 21-key NEC IR remote control.

💻 Installation
1. Clone the Repository
Bash
git clone [https://github.com/TomMiga/Jukebox-python.git](https://github.com/TomMiga/Jukebox-python.git)
cd Jukebox-python
2. Install Dependencies (Python 3.9+)
🪟 Windows:

Install Python 3 (check Add Python to PATH) and MPV Player (or VLC).

Install required Python packages via PowerShell:

PowerShell
pip install pygame mutagen Pillow requests python-mpv
🐧 Linux (Ubuntu / Debian / Raspberry Pi OS):

Bash
sudo apt update
sudo apt install -y python3-pip python3-pygame python3-pil python3-requests libmpv-dev mpv
pip3 install mutagen python-mpv --break-system-packages
🍎 macOS:

Install Python and MPV via Homebrew:

Bash
brew install python mpv
Install Python packages:

Bash
pip3 install pygame mutagen Pillow requests python-mpv
🚀 Quick Start (Demo Library)
The repository includes sample Creative Commons tracks inside the music/ folder so you can test the jukebox right away:

Scan the music library and fetch cover art:

Bash
python scan.py
(Optional: To enable Discogs cover art fetching, add your free personal token to DISCOGS_TOKEN in config.py.)

Launch the jukebox:

Bash
python main.py
⌨️ Keyboard Controls
Key	Action
Up / Down Arrow	Navigate through artists, albums, or tracks
Left / Right Arrow	Switch categories / tabs (CZ-SK / International / TOP 50 / Videos)
Enter / Space	Open artist/album or add selected song to the queue
Backspace / Esc	Go back one level / close dialog
N	Skip to the next song in the queue
P	Play / Pause current playback
+ / -	Volume Up / Volume Down
D	Toggle Auto-DJ mode ON/OFF
A – Z	Quick-jump to artist by first letter
Q / Alt+F4	Exit application
🔌 Raspberry Pi 4 Hardware Wiring (GPIO + IR)
The jukebox can be built into a custom enclosure using a 15.6" LCD panel, 4 physical buttons, and an IR receiver module (HX1838 / CHQ1838 / TSOP4838).

⚠️ WARNING: Power the IR receiver and buttons strictly from the 3.3V rail (Pin 1 or Pin 17). Connecting 5V to any GPIO pin will permanently damage the Raspberry Pi!

Pinout Table (RPi 4)
Component	Component Pin	Raspberry Pi 4 Pin	Notes
IR Receiver (HX1838)	OUT (Data)	GPIO 18 (Pin 12)	Data signal
IR Receiver (HX1838)	GND	GND (Pin 6)	Common ground
IR Receiver (HX1838)	VCC	3.3V (Pin 1)	Recommended RC filter (100 Ω series + 100 nF to GND)
Button UP	Pin 1 / Pin 2	GPIO 5 (Pin 29) / GND	Active-low (internal pull-up)
Button DOWN	Pin 1 / Pin 2	GPIO 6 (Pin 31) / GND	Active-low (internal pull-up)
Button ENTER	Pin 1 / Pin 2	GPIO 13 (Pin 33) / GND	Active-low (internal pull-up)
Button BACK	Pin 1 / Pin 2	GPIO 19 (Pin 35) / GND	Active-low (internal pull-up)
Enabling the IR Receiver in Raspberry Pi OS
Add the following line to /boot/firmware/config.txt (or /boot/config.txt on older OS releases):

Ini, TOML
dtoverlay=gpio-ir,gpio_pin=18
Reboot the Raspberry Pi and map your remote buttons using ir-keytable.


---

### 2. Jak nahrát `README.md` na GitHub

Jakmile soubor `README.md` uložíš do složky `D:\jukebox\Jukebox-python`, otevři ve stejné složce PowerShell a zadej postupně (každý řádek zvlášť):

```powershell
git add README.md
PowerShell
git commit -m "Přidán podrobný návod v CZ a EN (README.md)"
PowerShell
git push
Po obnovení stránky na [https://github.com/TomMiga/Jukebox-python](https://github.com/TomMiga/Jukebox-python) se ti celý návod s formátováním a tabulkami zobrazí přímo na hlavní stránce repozitáře. (Pokud by ses ještě chtěl ujistit, že klávesové zkratky v tabulce přesně sedí s tím, co máš aktuálně v ui.py, klidně mi pošli ten kousek z ui.py a doladíme je na 100 %.)