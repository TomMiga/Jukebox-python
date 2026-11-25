import library
import player
import ui
import config
import os

def main():
    print("Maxi Music Box – startuji...")
    print(f"Databáze: {config.DB_PATH}")

    if not os.path.exists(config.DB_PATH):
        print("\n!!! Databáze ještě neexistuje !!!")
        print("Nejdřív spusť skener:  python3 scan.py")
        return

    # Jen ověříme, že tabulka existuje
    library.init_db()

    p = player.Player()
    app = ui.UI(p)
    app.run()

if __name__ == "__main__":
    main()
