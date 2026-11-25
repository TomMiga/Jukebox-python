import os
from datetime import datetime
import pygame
import config
from library import (
    get_genres,
    get_artists,
    get_albums,
    get_tracks,
    get_cover_for_artist_album,
    get_total_tracks,
    get_videos,
    get_top_tracks,
)


class UI:
    def __init__(self, player):
        pygame.init()
        flags = pygame.FULLSCREEN if config.FULLSCREEN else 0
        self.screen = pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
        pygame.display.set_caption("Maxi Music Box")
        self.clock = pygame.time.Clock()

        pygame.key.set_repeat(350, 65)

        self.font_header = pygame.font.SysFont("tahoma", 24, bold=True)
        self.font_menu = pygame.font.SysFont("tahoma", 25, bold=True)
        self.font_sub = pygame.font.SysFont("tahoma", 19, bold=True)
        self.font_small = pygame.font.SysFont("tahoma", 17, bold=True)
        self.font_tiny = pygame.font.SysFont("tahoma", 15)
        self.font_clock = pygame.font.SysFont("tahoma", 44, bold=True)
        self.font_enter = pygame.font.SysFont("arial", 24, bold=True)
        self.font_side = pygame.font.SysFont("impact", 42)

        self.player = player

        self.state = "main"
        self.origin = None
        self.genre = None
        self.letter = None
        self.artist = None
        self.album = None
        self.items = []
        self.selected = 0

        self.cover_surface = None
        self.last_playing_path = None
        self.total_tracks = get_total_tracks()
        self.osd_message = ""
        self.osd_until = 0

        self.memory = {
            "main": 0,
            "scene_menu": 0,
            "letters": 0,
            "genres": 0,
            "artists": 0,
            "albums": 0,
            "tracks": 0,
            "top50": 0,
            "videos": 0,
            "queue": 0,
        }

        self.btn_up_rect = pygame.Rect(652, 130, 56, 62)
        self.btn_enter_rect = pygame.Rect(652, 225, 56, 230)
        self.btn_down_rect = pygame.Rect(652, 488, 56, 62)

        self.load_main_menu()

    def show_osd(self, text, duration_ms=2000):
        self.osd_message = text
        self.osd_until = pygame.time.get_ticks() + duration_ms

    def format_time(self, seconds):
        if not seconds or seconds < 0:
            return "0:00"
        m = int(seconds) // 60
        s = int(seconds) % 60
        return f"{m}:{s:02d}"

    def save_position(self):
        self.memory[self.state] = self.selected

    def restore_position(self):
        self.selected = self.memory.get(self.state, 0)
        if self.selected >= len(self.items):
            self.selected = max(0, len(self.items) - 1)
        if self.items and self.items[self.selected] is None:
            self.selected = 0

    def load_main_menu(self):
        self.save_position()
        self.state = "main"
        self.origin = None
        self.genre = None
        self.letter = None
        # None slouží jako prázdné oddělovací místo mezi hlavní nabídkou a Auto-DJ úplně dole
        self.items = [
            "Domácí scéna (CZ & SK)",
            "Světová scéna (Zahraniční)",
            "Hudební CD (Vše)",
            "Hudební CD podle žánrů",
            "Podle abecedy",
            "TOP 50 – Hitparáda jukeboxu",
            "Videoklipy",
            "Připraveno k přehrávání",
            None,
            None,
            None,
            None,
            "AUTO_DJ_TOGGLE",
        ]
        self.restore_position()
        self.sync_now_playing_cover()

    def load_scene_menu(self):
        self.save_position()
        self.state = "scene_menu"
        self.genre = None
        self.letter = None
        self.items = [
            "Všichni interpreti",
            "Podle abecedy",
            "Podle žánrů",
        ]
        self.restore_position()

    def load_letters(self):
        self.save_position()
        self.state = "letters"
        self.items = [chr(i) for i in range(ord("A"), ord("Z") + 1)] + ["#"]
        self.restore_position()

    def load_genres(self):
        self.save_position()
        self.state = "genres"
        self.items = ["VŠE"] + get_genres(origin=self.origin)
        self.restore_position()

    def load_artists(self, filter_letter=None, filter_genre=None):
        self.save_position()
        self.state = "artists"
        all_artists = get_artists(genre=filter_genre, origin=self.origin)

        if filter_letter:
            from library import strip_diacritics
            if filter_letter == "#":
                filtered = [a for a in all_artists if not a or not a[0].isalpha()]
            else:
                filtered = [
                    a for a in all_artists
                    if strip_diacritics(a).upper().startswith(filter_letter)
                ]
            self.items = filtered
        else:
            self.items = all_artists

        self.restore_position()

    def load_albums(self):
        self.save_position()
        self.state = "albums"
        albums = get_albums(self.artist, origin=self.origin)
        self.items = albums + ["VŠE"]
        self.restore_position()
        if self.items and self.selected < len(self.items):
            item = self.items[self.selected]
            if item != "VŠE":
                self.update_cover(self.artist, item)

    def load_tracks(self):
        self.save_position()
        self.state = "tracks"
        self.items = get_tracks(self.artist, self.album, origin=self.origin)
        self.restore_position()

    def load_top50(self):
        self.save_position()
        self.state = "top50"
        self.items = get_top_tracks(limit=50)
        self.restore_position()

    def load_videos(self):
        self.save_position()
        self.state = "videos"
        self.items = get_videos()
        self.restore_position()

    def _build_queue_items(self):
        return ["ZPĚT"] + list(self.player.queue)

    def load_queue_view(self):
        self.save_position()
        self.state = "queue"
        self.items = self._build_queue_items()
        self.selected = 1 if len(self.items) > 1 else 0

    def remove_selected_from_queue(self):
        if self.state != "queue" or self.selected <= 0:
            return
        q_index = self.selected - 1
        if 0 <= q_index < len(self.player.queue):
            self.player.queue.pop(q_index)
            self.items = self._build_queue_items()
            if self.selected >= len(self.items):
                self.selected = max(0, len(self.items) - 1)

    def update_cover(self, artist, album):
        path = get_cover_for_artist_album(artist, album) if album else None
        if path and os.path.exists(path):
            try:
                img = pygame.image.load(path).convert()
                self.cover_surface = pygame.transform.smoothscale(img, (325, 325))
            except Exception:
                self.cover_surface = None
        else:
            self.cover_surface = None

    def sync_now_playing_cover(self):
        if self.state in ("albums", "tracks"):
            return
        if self.player.current:
            cur_path = self.player.current.get("path")
            if cur_path != self.last_playing_path:
                self.last_playing_path = cur_path
                cover_path = self.player.current.get("cover_path")
                if cover_path and os.path.exists(cover_path):
                    try:
                        img = pygame.image.load(cover_path).convert()
                        self.cover_surface = pygame.transform.smoothscale(img, (325, 325))
                    except Exception:
                        self.cover_surface = None
                else:
                    self.update_cover(
                        self.player.current.get("artist"),
                        self.player.current.get("album"),
                    )
        else:
            self.last_playing_path = None
            self.cover_surface = None

    def move_up(self):
        if not self.items:
            return
        idx = self.selected - 1
        while idx >= 0 and self.items[idx] is None:
            idx -= 1
        if idx >= 0:
            self.selected = idx

        if self.state == "albums":
            item = self.items[self.selected]
            if item != "VŠE":
                self.update_cover(self.artist, item)

    def move_down(self):
        if not self.items:
            return
        idx = self.selected + 1
        while idx < len(self.items) and self.items[idx] is None:
            idx += 1
        if idx < len(self.items):
            self.selected = idx

        if self.state == "albums":
            item = self.items[self.selected]
            if item != "VŠE":
                self.update_cover(self.artist, item)

    def handle_input(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.player.is_playing_video():
                self.player.skip_current()
                return

            pos = event.pos
            if self.btn_up_rect.collidepoint(pos):
                self.move_up()
            elif self.btn_down_rect.collidepoint(pos):
                self.move_down()
            elif self.btn_enter_rect.collidepoint(pos):
                self.select()
            return

        if event.type != pygame.KEYDOWN:
            return

        # Dálkové ovládání výčepního / IR ovladač
        if event.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
            self.player.change_volume(5)
            self.show_osd(f"Hlasitost: {self.player.volume} %")
            return
        elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.player.change_volume(-5)
            self.show_osd(f"Hlasitost: {self.player.volume} %")
            return
        elif event.key == pygame.K_m:
            self.player.toggle_mute()
            self.show_osd("ZVUK ZTLUMEN (MUTE)" if self.player.muted else f"Hlasitost: {self.player.volume} %")
            return
        elif event.key in (pygame.K_p, pygame.K_SPACE):
            self.player.toggle_pause()
            self.show_osd("PAUZA" if self.player.is_paused() else "PŘEHRÁVÁNÍ")
            return
        elif event.key == pygame.K_n:
            self.player.skip_current()
            self.show_osd("Další skladba")
            return

        if event.key == pygame.K_UP:
            self.move_up()
        elif event.key == pygame.K_DOWN:
            self.move_down()
        elif event.key == pygame.K_PAGEUP:
            for _ in range(10):
                self.move_up()
        elif event.key == pygame.K_PAGEDOWN:
            for _ in range(10):
                self.move_down()
        elif event.key == pygame.K_DELETE:
            if self.state == "queue" and self.selected > 0:
                self.remove_selected_from_queue()
        elif event.key == pygame.K_RETURN:
            if not self.player.is_playing_video():
                self.select()
        elif event.key in (pygame.K_ESCAPE, pygame.K_BACKSPACE):
            if self.player.is_playing_video():
                self.player.skip_current()
            else:
                self.back()

    def select(self):
        if self.state == "queue":
            if self.selected == 0:
                self.back()
            else:
                self.remove_selected_from_queue()
            return

        if not self.items:
            return

        item = self.items[self.selected]
        if item is None:
            return

        self.save_position()

        if self.state == "main":
            if item == "Domácí scéna (CZ & SK)":
                self.origin = "CZ"
                self.load_scene_menu()
            elif item == "Světová scéna (Zahraniční)":
                self.origin = "Foreign"
                self.load_scene_menu()
            elif item == "Hudební CD (Vše)":
                self.origin = None
                self.genre = None
                self.letter = None
                self.load_artists()
            elif item == "Hudební CD podle žánrů":
                self.origin = None
                self.load_genres()
            elif item == "Podle abecedy":
                self.origin = None
                self.load_letters()
            elif item == "TOP 50 – Hitparáda jukeboxu":
                self.load_top50()
            elif item == "Videoklipy":
                self.load_videos()
            elif item == "Připraveno k přehrávání":
                self.load_queue_view()
            elif item == "AUTO_DJ_TOGGLE":
                self.player.toggle_auto_dj()
                self.show_osd("Auto-DJ ZAPNUT" if self.player.auto_dj else "Auto-DJ VYPNUT")

        elif self.state == "scene_menu":
            if item == "Všichni interpreti":
                self.letter = None
                self.genre = None
                self.load_artists()
            elif item == "Podle abecedy":
                self.load_letters()
            elif item == "Podle žánrů":
                self.load_genres()

        elif self.state == "letters":
            self.letter = item
            self.load_artists(filter_letter=item)

        elif self.state == "genres":
            self.genre = item
            self.load_artists(filter_genre=None if item == "VŠE" else item)

        elif self.state == "artists":
            self.artist = item
            self.load_albums()

        elif self.state == "albums":
            self.album = item
            self.load_tracks()

        elif self.state in ("tracks", "top50", "videos"):
            self.player.add_to_queue(dict(item))
            self.sync_now_playing_cover()
            self.show_osd(f"Přidáno: {item['title']}")

    def back(self):
        self.save_position()

        if self.state == "tracks":
            self.load_albums()
        elif self.state == "albums":
            self.load_artists(filter_letter=self.letter, filter_genre=self.genre)
        elif self.state == "artists":
            if self.letter:
                self.load_letters()
            elif self.genre:
                self.load_genres()
            elif self.origin:
                self.load_scene_menu()
            else:
                self.load_main_menu()
        elif self.state in ("letters", "genres"):
            if self.origin:
                self.load_scene_menu()
            else:
                self.load_main_menu()
        elif self.state in ("scene_menu", "queue", "videos", "top50"):
            self.load_main_menu()

    def draw_bevel_panel(self, rect, fill_color, light_color, dark_color, border=4):
        pygame.draw.rect(self.screen, fill_color, rect)
        pygame.draw.polygon(
            self.screen,
            light_color,
            [
                (rect.left, rect.top),
                (rect.right, rect.top),
                (rect.right - border, rect.top + border),
                (rect.left + border, rect.top + border),
                (rect.left + border, rect.bottom - border),
                (rect.left, rect.bottom),
            ],
        )
        pygame.draw.polygon(
            self.screen,
            dark_color,
            [
                (rect.right, rect.top),
                (rect.right, rect.bottom),
                (rect.left, rect.bottom),
                (rect.left + border, rect.bottom - border),
                (rect.right - border, rect.bottom - border),
                (rect.right - border, rect.top + border),
            ],
        )

    def draw_video_icon(self, x, y):
        pygame.draw.rect(self.screen, (35, 35, 45), (x + 2, y + 5, 20, 18))
        pygame.draw.rect(self.screen, (70, 175, 245), (x + 6, y + 8, 12, 12))
        for dy in (7, 13, 19):
            pygame.draw.rect(self.screen, (235, 235, 235), (x + 3, y + dy, 2, 2))
            pygame.draw.rect(self.screen, (235, 235, 235), (x + 19, y + dy, 2, 2))

    def draw_menu_icon(self, x, y, index, item_raw, item_text):
        cx, cy = x + 12, y + 14
        if self.state == "main":
            if item_raw == "AUTO_DJ_TOGGLE":
                col = (25, 165, 55) if self.player.auto_dj else (150, 40, 40)
                pygame.draw.circle(self.screen, col, (cx, cy), 10)
                pygame.draw.circle(self.screen, (255, 255, 255), (cx, cy), 10, 2)
            elif "Domácí" in item_text:
                pygame.draw.rect(self.screen, (255, 255, 255), (x + 2, y + 5, 20, 9))
                pygame.draw.rect(self.screen, (210, 20, 20), (x + 2, y + 14, 20, 9))
                pygame.draw.polygon(self.screen, (20, 60, 170), [(x + 2, y + 5), (x + 12, y + 14), (x + 2, y + 23)])
            elif "Světová" in item_text:
                pygame.draw.circle(self.screen, (30, 110, 210), (cx, cy), 10)
                pygame.draw.circle(self.screen, (60, 190, 80), (cx - 3, cy - 2), 4)
                pygame.draw.circle(self.screen, (60, 190, 80), (cx + 4, cy + 3), 3)
            elif "TOP 50" in item_text:
                pygame.draw.polygon(
                    self.screen,
                    (225, 150, 0),
                    [(cx, y + 4), (x + 15, y + 11), (x + 22, y + 11), (x + 16, y + 16),
                     (x + 18, y + 23), (cx, y + 19), (x + 6, y + 23), (x + 8, y + 16),
                     (x + 2, y + 11), (x + 9, y + 11)],
                )
            elif "Videoklipy" in item_text:
                self.draw_video_icon(x, y)
            elif "Připraveno" in item_text:
                pygame.draw.polygon(self.screen, (220, 120, 0), [(x + 4, y + 5), (x + 21, y + 14), (x + 4, y + 23)])
            else:
                pygame.draw.circle(self.screen, (215, 225, 235), (cx, cy), 10)
                pygame.draw.circle(self.screen, (80, 90, 110), (cx, cy), 10, 1)
                pygame.draw.circle(self.screen, (40, 40, 40), (cx, cy), 3)
        elif self.state == "queue":
            if index == 0:
                pygame.draw.polygon(
                    self.screen,
                    (200, 30, 30),
                    [(x + 3, y + 14), (x + 13, y + 6), (x + 13, y + 11), (x + 21, y + 11),
                     (x + 21, y + 17), (x + 13, y + 17), (x + 13, y + 22)],
                )
            else:
                pygame.draw.line(self.screen, (190, 20, 20), (x + 6, y + 8), (x + 18, y + 20), 3)
                pygame.draw.line(self.screen, (190, 20, 20), (x + 18, y + 8), (x + 6, y + 20), 3)
        elif self.state == "videos":
            self.draw_video_icon(x, y)
        elif self.state in ("tracks", "top50"):
            pygame.draw.circle(self.screen, (180, 20, 20), (x + 8, y + 20), 4)
            pygame.draw.line(self.screen, (180, 20, 20), (x + 11, y + 20), (x + 11, y + 7), 2)
            pygame.draw.line(self.screen, (180, 20, 20), (x + 11, y + 7), (x + 18, y + 10), 3)
        else:
            pygame.draw.circle(self.screen, (225, 230, 240), (cx, cy), 8)
            pygame.draw.circle(self.screen, (60, 60, 60), (cx, cy), 8, 1)
            pygame.draw.circle(self.screen, (30, 30, 30), (cx, cy), 2)

    def draw_cd_jewel_case(self, x, y, size=325):
        spine_w = 34
        case_rect = pygame.Rect(x, y, size + spine_w, size)

        pygame.draw.rect(self.screen, (10, 10, 12), case_rect)
        pygame.draw.rect(self.screen, (95, 100, 110), case_rect, 2)

        spine_rect = pygame.Rect(x + 2, y + 2, spine_w - 2, size - 4)
        pygame.draw.rect(self.screen, (24, 24, 28), spine_rect)
        for ry in range(y + 6, y + size - 6, 5):
            pygame.draw.line(self.screen, (52, 54, 60), (x + 4, ry), (x + spine_w - 3, ry), 2)

        art_rect = pygame.Rect(x + spine_w, y + 2, size - 2, size - 4)
        if self.cover_surface:
            self.screen.blit(self.cover_surface, (art_rect.x, art_rect.y))
        else:
            pygame.draw.rect(self.screen, (18, 22, 28), art_rect)
            cx, cy = art_rect.centerx, art_rect.centery
            pygame.draw.circle(self.screen, (45, 55, 70), (cx, cy), 95, 4)
            pygame.draw.circle(self.screen, (30, 38, 48), (cx, cy), 28)
            if self.state == "videos" or self.player.is_playing_video():
                t1 = self.font_header.render("VIDEOKLIPY", True, (70, 195, 245))
                t2 = self.font_tiny.render("Maxi Music Box TV", True, (160, 175, 190))
            else:
                t1 = self.font_header.render("MAXI MUSIC BOX", True, (242, 206, 48))
                t2 = self.font_tiny.render("Digitální Jukebox", True, (160, 175, 190))
            self.screen.blit(t1, (cx - t1.get_width() // 2, cy - 18))
            self.screen.blit(t2, (cx - t2.get_width() // 2, cy + 16))

        pygame.draw.line(
            self.screen,
            (130, 135, 145),
            (art_rect.left, art_rect.top),
            (art_rect.right, art_rect.top),
            1,
        )

    def get_header_title(self):
        origin_tag = ""
        if self.origin == "CZ":
            origin_tag = " [CZ & SK]"
        elif self.origin == "Foreign":
            origin_tag = " [Zahraniční]"

        if self.state == "main":
            return "Hlavní nabídka"
        if self.state == "scene_menu":
            return "Domácí scéna (CZ & SK)" if self.origin == "CZ" else "Světová scéna (Zahraniční)"
        if self.state == "letters":
            return f"Podle abecedy{origin_tag}"
        if self.state == "genres":
            return f"Podle žánrů{origin_tag}"
        if self.state == "artists":
            extra = ""
            if self.letter:
                extra = f" – {self.letter}"
            elif self.genre and self.genre != "VŠE":
                extra = f" – {self.genre}"
            return f"Interpreti{origin_tag}{extra}"
        if self.state == "albums":
            return f"{self.artist}"
        if self.state == "tracks":
            return f"{self.artist} – {self.album}"
        if self.state == "top50":
            return f"TOP 50 – Hitparáda jukeboxu ({len(self.items)})"
        if self.state == "videos":
            return f"Videoklipy ({len(self.items)})"
        if self.state == "queue":
            return f"Připraveno k přehrávání ({len(self.player.queue)})"
        return ""

    def draw(self):
        if self.player.is_playing_video():
            self.screen.fill((0, 0, 0))
            vsurf = self.player.get_video_surface()
            if vsurf:
                self.screen.blit(vsurf, (0, 0))

            bar_h = 34
            bar_surf = pygame.Surface((config.SCREEN_WIDTH, bar_h), pygame.SRCALPHA)
            bar_surf.fill((0, 0, 0, 165))
            self.screen.blit(bar_surf, (0, config.SCREEN_HEIGHT - bar_h))

            cur = self.player.current
            now_txt = f"► {cur['artist']} – {cur['title']}"
            t_str = f"{self.format_time(self.player.get_time())} / {self.format_time(self.player.get_length())}   [ESC / klik = ukončit video]"
            s_left = self.font_small.render(now_txt[:60], True, (242, 206, 48))
            s_right = self.font_tiny.render(t_str, True, (220, 220, 220))
            self.screen.blit(s_left, (16, config.SCREEN_HEIGHT - bar_h + 6))
            self.screen.blit(s_right, (config.SCREEN_WIDTH - s_right.get_width() - 16, config.SCREEN_HEIGHT - bar_h + 8))

            pygame.display.flip()
            return

        self.sync_now_playing_cover()
        self.screen.fill(config.COLOR_BG)

        # 1. Levý svislý bordó pruh
        strip_rect = pygame.Rect(0, 0, 56, config.SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, config.COLOR_SIDE_STRIP, strip_rect)
        pygame.draw.line(self.screen, (140, 35, 40), (55, 0), (55, config.SCREEN_HEIGHT), 2)

        side_surf = self.font_side.render("MAXI MUSIC BOX", True, config.COLOR_SIDE_TEXT)
        side_rot = pygame.transform.rotate(side_surf, 90)
        self.screen.blit(side_rot, (6, (config.SCREEN_HEIGHT - side_rot.get_height()) // 2))

        # 2. Levý žlutý 3D panel
        left_rect = pygame.Rect(68, 16, 570, 688)
        self.draw_bevel_panel(
            left_rect,
            config.COLOR_PANEL_YELLOW,
            config.COLOR_PANEL_YELLOW_LIGHT,
            config.COLOR_PANEL_YELLOW_DARK,
            border=5,
        )

        header_txt = self.get_header_title()
        header_surf = self.font_header.render(header_txt[:36], True, config.COLOR_TEXT_DARK)
        self.screen.blit(header_surf, (88, 28))
        pygame.draw.line(self.screen, config.COLOR_PANEL_YELLOW_DARK, (82, 64), (624, 64), 2)
        pygame.draw.line(self.screen, config.COLOR_PANEL_YELLOW_LIGHT, (82, 66), (624, 66), 2)

        list_top = 76
        row_h = 38
        visible_rows = 14

        if self.state == "queue":
            self.items = self._build_queue_items()
            if self.selected >= len(self.items):
                self.selected = max(0, len(self.items) - 1)

        if not self.items:
            if self.state == "videos":
                empty_msg = "Složka videos je prázdná"
            elif self.state == "top50":
                empty_msg = "Zatím nebyly přehrány žádné skladby"
            else:
                empty_msg = "Žádné položky k zobrazení"
            emp = self.font_sub.render(empty_msg, True, (90, 75, 10))
            self.screen.blit(emp, (95, 120))
        else:
            start = max(0, self.selected - (visible_rows // 2))
            if start + visible_rows > len(self.items):
                start = max(0, len(self.items) - visible_rows)
            end = min(len(self.items), start + visible_rows)

            y = list_top
            for i in range(start, end):
                item = self.items[i]

                # Prázdné oddělovací řádky (mezera nad Auto-DJ dole v menu)
                if item is None:
                    y += row_h
                    continue

                dur_text = None

                if item == "AUTO_DJ_TOGGLE":
                    stav = "ZAPNUTO" if self.player.auto_dj else "VYPNUTO"
                    label = f"Auto-DJ (náhodná hudba): {stav}"
                elif self.state == "tracks":
                    tnum = item["track_num"] if item["track_num"] else 0
                    label = f"{tnum:02d}. {item['title']}"
                    dur_val = item["duration"] if "duration" in item.keys() else 0
                    if dur_val and dur_val > 0:
                        dur_text = self.format_time(dur_val)
                elif self.state == "top50":
                    plays = item["play_count"] if "play_count" in item.keys() else 0
                    label = f"{i + 1}. {item['artist']} – {item['title']}"
                    dur_val = item["duration"] if "duration" in item.keys() else 0
                    dur_part = f" • {self.format_time(dur_val)}" if dur_val and dur_val > 0 else ""
                    dur_text = f"{plays}×{dur_part}"
                elif self.state == "videos":
                    label = item["display_name"]
                elif self.state == "queue":
                    if i == 0:
                        label = "ZPĚT do hlavní nabídky"
                    else:
                        prefix = "[VIDEO] " if item.get("is_video") else ""
                        label = f"{i}. {prefix}{item['artist']} – {item['title']}"
                        dur_val = item.get("duration", 0)
                        if dur_val and dur_val > 0:
                            dur_text = self.format_time(dur_val)
                else:
                    label = str(item)

                is_selected = (i == self.selected)
                row_rect = pygame.Rect(82, y - 2, 542, row_h - 2)

                if is_selected:
                    pygame.draw.rect(self.screen, config.COLOR_SELECT_BG, row_rect)
                    txt_color = config.COLOR_SELECT_TEXT
                    dur_color = (220, 230, 255)
                else:
                    txt_color = config.COLOR_TEXT_DARK
                    dur_color = (75, 65, 15)

                self.draw_menu_icon(88, y + 2, i, item, label)

                max_text_w = 415 if dur_text else 495
                display_label = label
                surf = self.font_menu.render(display_label, True, txt_color)
                if surf.get_width() > max_text_w:
                    while len(display_label) > 4 and self.font_menu.size(display_label + "…")[0] > max_text_w:
                        display_label = display_label[:-1]
                    surf = self.font_menu.render(display_label + "…", True, txt_color)

                self.screen.blit(surf, (120, y + 1))

                if dur_text:
                    dur_surf = self.font_tiny.render(dur_text, True, dur_color)
                    self.screen.blit(dur_surf, (row_rect.right - dur_surf.get_width() - 10, y + 8))

                y += row_h

            if self.state == "queue" and len(self.items) == 1:
                emp = self.font_sub.render("Fronta skladeb je prázdná", True, (90, 75, 10))
                self.screen.blit(emp, (120, y + 14))

        # Dolní stavový řádek
        pygame.draw.line(self.screen, config.COLOR_PANEL_YELLOW_DARK, (82, 622), (624, 622), 2)
        pygame.draw.line(self.screen, config.COLOR_PANEL_YELLOW_LIGHT, (82, 624), (624, 624), 2)

        if self.state == "queue":
            foot1 = self.font_small.render("ENTER na skladbě = odebrat z fronty", True, config.COLOR_TEXT_DARK)
            foot2 = self.font_sub.render(f"Ve frontě čeká: {len(self.player.queue)} skladeb", True, config.COLOR_TEXT_RED)
            self.screen.blit(foot1, (165, 634))
            self.screen.blit(foot2, (200, 658))
        elif self.state == "top50":
            foot1 = self.font_small.render("Nejhranější skladby v tomto jukeboxu", True, config.COLOR_TEXT_DARK)
            foot2 = self.font_sub.render(f"TOP {len(self.items)} hitparáda", True, config.COLOR_TEXT_RED)
            self.screen.blit(foot1, (175, 634))
            self.screen.blit(foot2, (255, 658))
        elif self.state == "videos":
            foot1 = self.font_small.render("Ve složce videoklipů je:", True, config.COLOR_TEXT_DARK)
            foot2 = self.font_sub.render(f"{len(self.items)} videoklipů", True, config.COLOR_TEXT_RED)
            self.screen.blit(foot1, (215, 634))
            self.screen.blit(foot2, (255, 658))
        else:
            foot1 = self.font_small.render("V Maxi Music Boxu je celkem:", True, config.COLOR_TEXT_DARK)
            foot2 = self.font_sub.render(f"{self.total_tracks} písniček", True, config.COLOR_TEXT_RED)
            self.screen.blit(foot1, (195, 634))
            self.screen.blit(foot2, (255, 658))

        hint_back = self.font_tiny.render("ESC = zpět", True, (85, 70, 10))
        self.screen.blit(hint_back, (535, 672))

        # 3. Středový ovládací sloupec
        self.draw_bevel_panel(
            self.btn_up_rect,
            config.COLOR_PANEL_YELLOW,
            config.COLOR_PANEL_YELLOW_LIGHT,
            config.COLOR_PANEL_YELLOW_DARK,
            border=4,
        )
        cx_u, cy_u = self.btn_up_rect.centerx, self.btn_up_rect.centery
        pygame.draw.polygon(
            self.screen,
            config.COLOR_ARROW_CYAN,
            [(cx_u, cy_u - 18), (cx_u + 16, cy_u), (cx_u + 7, cy_u), (cx_u + 7, cy_u + 18),
             (cx_u - 7, cy_u + 18), (cx_u - 7, cy_u), (cx_u - 16, cy_u)],
        )
        pygame.draw.polygon(
            self.screen,
            (10, 40, 80),
            [(cx_u, cy_u - 18), (cx_u + 16, cy_u), (cx_u + 7, cy_u), (cx_u + 7, cy_u + 18),
             (cx_u - 7, cy_u + 18), (cx_u - 7, cy_u), (cx_u - 16, cy_u)],
            2,
        )

        self.draw_bevel_panel(
            self.btn_enter_rect,
            config.COLOR_BTN_PINK,
            config.COLOR_BTN_PINK_LIGHT,
            config.COLOR_BTN_PINK_DARK,
            border=4,
        )
        for idx, ch in enumerate("ENTER"):
            ch_surf = self.font_enter.render(ch, True, (255, 255, 255))
            self.screen.blit(
                ch_surf,
                (self.btn_enter_rect.centerx - ch_surf.get_width() // 2, self.btn_enter_rect.y + 24 + idx * 38),
            )

        self.draw_bevel_panel(
            self.btn_down_rect,
            config.COLOR_PANEL_YELLOW,
            config.COLOR_PANEL_YELLOW_LIGHT,
            config.COLOR_PANEL_YELLOW_DARK,
            border=4,
        )
        cx_d, cy_d = self.btn_down_rect.centerx, self.btn_down_rect.centery
        pygame.draw.polygon(
            self.screen,
            config.COLOR_ARROW_CYAN,
            [(cx_d, cy_d + 18), (cx_d + 16, cy_d), (cx_d + 7, cy_d), (cx_d + 7, cy_d - 18),
             (cx_d - 7, cy_d - 18), (cx_d - 7, cy_d), (cx_d - 16, cy_d)],
        )
        pygame.draw.polygon(
            self.screen,
            (10, 40, 80),
            [(cx_d, cy_d + 18), (cx_d + 16, cy_d), (cx_d + 7, cy_d), (cx_d + 7, cy_d - 18),
             (cx_d - 7, cy_d - 18), (cx_d - 7, cy_d), (cx_d - 16, cy_d)],
            2,
        )

        # 4. Pravý panel
        right_x = 724
        right_w = 536

        cd_size = 325
        cd_x = right_x + (right_w - (cd_size + 34)) // 2
        self.draw_cd_jewel_case(cd_x, 16, size=cd_size)

        red_rect = pygame.Rect(right_x, 356, right_w, 128)
        self.draw_bevel_panel(
            red_rect,
            config.COLOR_BOX_RED,
            config.COLOR_BOX_RED_LIGHT,
            config.COLOR_BOX_RED_DARK,
            border=5,
        )

        now = datetime.now()
        days_cz = ["Pondělí", "Úterý", "Středa", "Čtvrtek", "Pátek", "Sobota", "Neděle"]
        day_name = days_cz[now.weekday()]
        date_str = now.strftime("%d.%m.%Y")
        time_str = now.strftime("%H:%M:%S")

        status_line = "Hraji zdarma • Auto-DJ" if self.player.auto_dj else "Hraji zdarma"
        free_surf = self.font_header.render(status_line, True, (255, 240, 120))
        day_surf = self.font_sub.render(day_name, True, (255, 255, 255))
        date_surf = self.font_sub.render(date_str, True, (255, 255, 255))
        time_surf = self.font_clock.render(time_str, True, (255, 255, 255))

        self.screen.blit(free_surf, (red_rect.x + 24, red_rect.y + 18))
        self.screen.blit(day_surf, (red_rect.x + 24, red_rect.y + 56))
        self.screen.blit(date_surf, (red_rect.x + 24, red_rect.y + 84))
        self.screen.blit(time_surf, (red_rect.right - time_surf.get_width() - 26, red_rect.y + 38))

        green_rect = pygame.Rect(right_x, 498, right_w, 206)
        self.draw_bevel_panel(
            green_rect,
            config.COLOR_BOX_GREEN,
            config.COLOR_BOX_GREEN_LIGHT,
            config.COLOR_BOX_GREEN_DARK,
            border=5,
        )

        inner_q = pygame.Rect(green_rect.x + 12, green_rect.y + 12, green_rect.width - 24, green_rect.height - 24)
        pygame.draw.rect(self.screen, config.COLOR_QUEUE_BG, inner_q)
        pygame.draw.rect(self.screen, config.COLOR_BOX_GREEN_DARK, inner_q, 2)

        q_title = self.font_small.render("Připraveno k přehrávání", True, config.COLOR_TEXT_DARK)
        q_count = self.font_small.render(f"Ve frontě: {len(self.player.queue)}", True, config.COLOR_TEXT_DARK)
        self.screen.blit(q_title, (inner_q.x + 10, inner_q.y + 6))
        self.screen.blit(q_count, (inner_q.right - q_count.get_width() - 10, inner_q.y + 6))
        pygame.draw.line(
            self.screen,
            config.COLOR_BOX_GREEN_DARK,
            (inner_q.x + 6, inner_q.y + 30),
            (inner_q.right - 6, inner_q.y + 30),
            2,
        )

        qy = inner_q.y + 36
        if self.player.current:
            cur = self.player.current
            if cur.get("is_video"):
                vtag = "[VIDEO] "
            elif cur.get("is_auto_dj"):
                vtag = "[Auto-DJ] "
            else:
                vtag = ""
            cur_txt = f"► {vtag}{cur['artist']} – {cur['title']}"
            cur_time = f"{self.format_time(self.player.get_time())}/{self.format_time(self.player.get_length())}"
            c_surf = self.font_small.render(cur_txt[:34], True, (180, 15, 15))
            t_surf = self.font_tiny.render(cur_time, True, (180, 15, 15))
            self.screen.blit(c_surf, (inner_q.x + 10, qy))
            self.screen.blit(t_surf, (inner_q.right - t_surf.get_width() - 10, qy + 2))
        else:
            idle_surf = self.font_small.render("Nic nehraje – vyber skladbu...", True, (70, 90, 70))
            self.screen.blit(idle_surf, (inner_q.x + 10, qy))

        qy += 28
        for idx, qtrack in enumerate(self.player.queue[:4]):
            vtag = "[VIDEO] " if qtrack.get("is_video") else ""
            q_line = f"{idx + 1}. {vtag}{qtrack['artist']} – {qtrack['title']}"
            q_dur = self.format_time(qtrack.get("duration", 0))
            qs = self.font_tiny.render(q_line[:40], True, config.COLOR_TEXT_DARK)
            ds = self.font_tiny.render(q_dur, True, (50, 70, 50))
            self.screen.blit(qs, (inner_q.x + 12, qy))
            self.screen.blit(ds, (inner_q.right - ds.get_width() - 10, qy))
            qy += 24

        if len(self.player.queue) > 4:
            more = self.font_tiny.render(f"... a dalších {len(self.player.queue) - 4} skladeb", True, (40, 80, 40))
            self.screen.blit(more, (inner_q.x + 12, qy))

        # Krátký OSD proužek při ovládání hlasitosti / pauzy / Auto-DJ
        if self.osd_message and pygame.time.get_ticks() < self.osd_until:
            osd_surf = self.font_header.render(self.osd_message, True, (255, 255, 255))
            box_w = osd_surf.get_width() + 40
            box_h = 46
            box_rect = pygame.Rect((config.SCREEN_WIDTH - box_w) // 2, 24, box_w, box_h)
            pygame.draw.rect(self.screen, (15, 25, 95), box_rect)
            pygame.draw.rect(self.screen, (255, 240, 120), box_rect, 3)
            self.screen.blit(osd_surf, (box_rect.x + 20, box_rect.y + 9))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self.handle_input(event)

            self.player.update()
            self.draw()
            self.clock.tick(config.FPS)

        pygame.quit()