#!/usr/bin/env python3
import library


def main():
    print("Inicializuji a čistím databázi interpretů...")
    library.init_db()
    conn = library.get_db()
    c = conn.cursor()

    rows = c.execute("SELECT id, artist FROM tracks").fetchall()
    print(f"Zpracovávám {len(rows)} skladeb...")

    c.execute("DELETE FROM track_artists")

    for row in rows:
        track_id = row["id"]
        raw_artist = row["artist"]
        artists = library.split_artists(raw_artist)
        primary = artists[0]

        c.execute("UPDATE tracks SET artist = ? WHERE id = ?", (primary, track_id))
        for art in artists:
            c.execute(
                "INSERT OR IGNORE INTO track_artists (track_id, artist) VALUES (?, ?)",
                (track_id, art),
            )

    merged = library.unify_artists_in_db(conn)
    conn.commit()

    total_unique = c.execute("SELECT COUNT(DISTINCT artist) AS cnt FROM track_artists").fetchone()["cnt"]
    conn.close()

    print("-" * 50)
    print(f"Hotovo!")
    print(f"Sloučené duplicitní varianty : {merged}")
    print(f"Počet unikátních interpretů  : {total_unique}")


if __name__ == "__main__":
    main()