import ctypes
import pygame
import vlc
import config
from library import increment_play_count, get_random_track


VideoLockCb = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
VideoUnlockCb = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
VideoDisplayCb = ctypes.CFUNCTYPE(None, ctypes.c_void_p, ctypes.c_void_p)


class Player:
    def __init__(self):
        self.instance = vlc.Instance("--no-xlib")
        self.player = self.instance.media_player_new()
        self.queue = []
        self.current = None
        self.auto_dj = False
        self.volume = 85
        self.muted = False
        self.player.audio_set_volume(self.volume)

        # Rozlišení interního bufferu videa
        self.video_w = config.SCREEN_WIDTH
        self.video_h = config.SCREEN_HEIGHT
        self.video_pitch = self.video_w * 4
        self._buf_size = self.video_pitch * self.video_h
        self._video_buf = ctypes.create_string_buffer(self._buf_size)
        self._buf_ptr = ctypes.cast(self._video_buf, ctypes.c_void_p)

        self.video_surface = pygame.Surface((self.video_w, self.video_h))
        self.has_new_frame = False
        self._frame_dirty = False

        self._lock_cb = VideoLockCb(self._on_video_lock)
        self._unlock_cb = VideoUnlockCb(self._on_video_unlock)
        self._display_cb = VideoDisplayCb(self._on_video_display)

        self.player.video_set_callbacks(self._lock_cb, self._unlock_cb, self._display_cb, None)
        self.player.video_set_format("RV32", self.video_w, self.video_h, self.video_pitch)

    def _on_video_lock(self, opaque, planes):
        planes[0] = self._buf_ptr
        return None

    def _on_video_unlock(self, opaque, picture, planes):
        pass

    def _on_video_display(self, opaque, picture):
        self._frame_dirty = True

    def get_video_surface(self):
        if not self.is_playing_video():
            return None
        if self._frame_dirty:
            self._frame_dirty = False
            try:
                raw_bytes = ctypes.string_at(self._buf_ptr, self._buf_size)
                surf = pygame.image.frombuffer(raw_bytes, (self.video_w, self.video_h), "BGRA")
                self.video_surface.blit(surf, (0, 0))
                self.has_new_frame = True
            except Exception:
                pass
        return self.video_surface if self.has_new_frame else None

    def toggle_auto_dj(self):
        self.auto_dj = not self.auto_dj
        if self.auto_dj and not self.is_playing() and self.current is None and not self.queue:
            self.play_next()

    def change_volume(self, delta):
        self.muted = False
        self.player.audio_set_mute(False)
        self.volume = max(0, min(100, self.volume + delta))
        self.player.audio_set_volume(self.volume)

    def toggle_mute(self):
        self.muted = not self.muted
        self.player.audio_set_mute(self.muted)

    def toggle_pause(self):
        if self.current:
            self.player.pause()

    def add_to_queue(self, track):
        self.queue.append(track)
        if not self.is_playing() and self.current is None:
            self.play_next()

    def play_next(self):
        self.has_new_frame = False
        self._frame_dirty = False
        self.video_surface.fill((0, 0, 0))

        if not self.queue:
            if self.auto_dj:
                rnd = get_random_track()
                if rnd:
                    rnd["is_auto_dj"] = True
                    self.current = rnd
                    media = self.instance.media_new(self.current["path"])
                    self.player.set_media(media)
                    self.player.play()
                    return
            self.current = None
            return

        self.current = self.queue.pop(0)
        if not self.current.get("is_video") and not self.current.get("is_auto_dj"):
            increment_play_count(self.current.get("path"))

        media = self.instance.media_new(self.current["path"])
        self.player.set_media(media)
        self.player.play()

    def is_playing(self):
        state = self.player.get_state()
        return state in (vlc.State.Playing, vlc.State.Paused, vlc.State.Buffering, vlc.State.Opening)

    def is_paused(self):
        return self.player.get_state() == vlc.State.Paused

    def is_playing_video(self):
        return bool(self.current and self.current.get("is_video"))

    def get_time(self):
        t = self.player.get_time()
        return t // 1000 if t > 0 else 0

    def get_length(self):
        length = self.player.get_length()
        return length // 1000 if length > 0 else 0

    def skip_current(self):
        self.has_new_frame = False
        self._frame_dirty = False
        self.player.stop()
        self.play_next()

    def stop(self):
        self.has_new_frame = False
        self._frame_dirty = False
        self.player.stop()
        self.current = None
        self.queue.clear()

    def update(self):
        if self.current and not self.is_playing():
            state = self.player.get_state()
            if state in (vlc.State.Ended, vlc.State.Error):
                self.play_next()
        elif not self.current and self.auto_dj:
            self.play_next()