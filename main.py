import json
import os
import threading
import time
from dataclasses import dataclass, asdict
from pathlib import Path
import sys
import tkinter as tk
from tkinter import messagebox

import pyautogui
import keyboard
from PIL import Image, ImageTk
from playsound import playsound


# -----------------------------
# Config / Paths
# -----------------------------

APP_DIR = Path.home() / ".desktop_automation_utility"
SETTINGS_PATH = APP_DIR / "settings.json"

DEFAULT_TARGET_KEY = "1"
DEFAULT_HOTKEY = "alt+1"
DEFAULT_DELAY_MS = 100

SHOW_WINDOW_HOTKEY = "alt+`"  # bring UI back


def resource_path(rel_path: str) -> Path:
    """
    Resolve a resource path that works both in normal execution and when bundled
    (e.g., PyInstaller onefile).
    """
    if getattr(sys, "frozen", False):
        base = Path(getattr(sys, "_MEIPASS"))
    else:
        base = Path(__file__).parent
    return base / rel_path


ACTIVATE_WAV = resource_path("activate.wav")
DEACTIVATE_WAV = resource_path("deactivate.wav")
ICON_PATH = resource_path("alliance_icon.ico")


# -----------------------------
# Settings
# -----------------------------

@dataclass
class AppSettings:
    target_key: str = DEFAULT_TARGET_KEY
    hotkey: str = DEFAULT_HOTKEY
    delay_ms: int = DEFAULT_DELAY_MS

    @staticmethod
    def load() -> "AppSettings":
        try:
            if SETTINGS_PATH.exists():
                data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
                return AppSettings(
                    target_key=str(data.get("key", DEFAULT_TARGET_KEY)),
                    hotkey=str(data.get("combo", DEFAULT_HOTKEY)),
                    delay_ms=int(data.get("delay", DEFAULT_DELAY_MS)),
                )
        except Exception as e:
            print(f"[settings] Failed to load settings: {e}")
        return AppSettings()

    def save(self) -> None:
        try:
            APP_DIR.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(json.dumps({
                "key": self.target_key,
                "combo": self.hotkey,
                "delay": self.delay_ms
            }, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"[settings] Failed to save settings: {e}")


# -----------------------------
# Sound (non-blocking)
# -----------------------------

def play_sound(path: Path) -> None:
    """Play sound without blocking UI; ignore if missing."""
    if not path.exists():
        return
    threading.Thread(target=playsound, args=(str(path),), daemon=True).start()


# -----------------------------
# Core automation
# -----------------------------

class AutoKeyPresser:
    """
    Hotkey-driven key press loop.
    Uses an Event for clean stop and a single worker thread.
    """
    def __init__(self, on_toggle=None):
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None

        self.is_active = False
        self.delay_s = DEFAULT_DELAY_MS / 1000.0
        self.target_key = DEFAULT_TARGET_KEY
        self.hotkey = DEFAULT_HOTKEY

        self.on_toggle = on_toggle
        self._register_hotkey(self.hotkey)

    def _register_hotkey(self, combo: str) -> None:
        try:
            keyboard.add_hotkey(combo, self.toggle)
        except Exception as e:
            print(f"[hotkey] Failed to register hotkey '{combo}': {e}")

    def _unregister_hotkey(self, combo: str) -> None:
        try:
            keyboard.remove_hotkey(combo)
        except Exception:
            pass

    def set_target_key(self, key: str) -> None:
        self.target_key = key

    def set_delay_ms(self, delay_ms: int) -> None:
        self.delay_s = max(1, delay_ms) / 1000.0

    def set_hotkey(self, combo: str) -> None:
        if not combo:
            return
        # remove old, add new
        self._unregister_hotkey(self.hotkey)
        self.hotkey = combo
        self._register_hotkey(combo)

    def toggle(self) -> None:
        if self.is_active:
            self.stop()
        else:
            self.start()

    def start(self) -> None:
        if self.is_active:
            return
        self.is_active = True
        self._stop_event.clear()
        if self.on_toggle:
            self.on_toggle(True)

        self._worker = threading.Thread(target=self._loop, daemon=True)
        self._worker.start()

    def stop(self) -> None:
        if not self.is_active:
            return
        self.is_active = False
        self._stop_event.set()
        if self.on_toggle:
            self.on_toggle(False)

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                pyautogui.press(self.target_key)
            except Exception as e:
                print(f"[press] Key press failed: {e}")
            time.sleep(self.delay_s)


# -----------------------------
# UI
# -----------------------------

class DesktopAutomationUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Desktop Automation Utility")
        self.root.geometry("420x520")
        self.root.configure(bg="#0e1a40")

        self.settings = AppSettings.load()

        self.presser = AutoKeyPresser(on_toggle=self.update_status)

        # Apply loaded settings to core
        self.presser.set_target_key(self.settings.target_key)
        self.presser.set_delay_ms(self.settings.delay_ms)
        self.presser.set_hotkey(self.settings.hotkey)

        self._logo = None  # keep reference
        self.hotkey_candidate: str | None = self.settings.hotkey

        self.build_ui()
        self.populate_fields()

        keyboard.add_hotkey(SHOW_WINDOW_HOTKEY, self.show_window)

        # Clean shutdown
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def build_ui(self) -> None:
        # Header / icon
        try:
            img = Image.open(ICON_PATH).resize((64, 64))
            self._logo = ImageTk.PhotoImage(img)
            tk.Label(self.root, image=self._logo, bg="#0e1a40").pack(pady=8)
        except Exception:
            tk.Label(
                self.root,
                text="⚙ Desktop Automation Utility ⚙",
                bg="#0e1a40",
                fg="gold",
                font=("Segoe UI", 14, "bold"),
            ).pack(pady=10)

        # Target key
        tk.Label(self.root, text="Target Key:", bg="#0e1a40", fg="gold").pack()
        self.key_entry = tk.Entry(self.root)
        self.key_entry.pack(pady=4)

        # Hotkey
        tk.Label(self.root, text="Hotkey Combo:", bg="#0e1a40", fg="gold").pack()
        self.combo_label = tk.Label(self.root, text="", bg="#0e1a40", fg="white")
        self.combo_label.pack()

        self.combo_button = tk.Button(
            self.root, text="🎮 Listen for Hotkey", command=self.capture_combo_async
        )
        self.combo_button.pack(pady=8)

        # Delay
        tk.Label(self.root, text="Delay Between Presses (ms):", bg="#0e1a40", fg="gold").pack()
        self.delay_entry = tk.Entry(self.root)
        self.delay_entry.pack(pady=6)

        # Apply
        tk.Button(self.root, text="🛠 Apply Settings", command=self.apply_settings).pack(pady=12)

        # Status
        self.status_button = tk.Button(
            self.root,
            text="⛔ Macro Inactive",
            state="disabled",
            bg="#333333",
            fg="white",
            font=("Segoe UI", 10, "bold"),
        )
        self.status_button.pack(pady=10, ipadx=10, ipady=6)

        tk.Label(
            self.root,
            text=f"Use your hotkey to toggle. Show window: {SHOW_WINDOW_HOTKEY}",
            bg="#0e1a40",
            fg="lightgray",
        ).pack(pady=6)

    def populate_fields(self) -> None:
        self.key_entry.delete(0, tk.END)
        self.key_entry.insert(0, self.settings.target_key)

        self.delay_entry.delete(0, tk.END)
        self.delay_entry.insert(0, str(self.settings.delay_ms))

        self.combo_label.config(text=f"Hotkey set to: {self.settings.hotkey} (loaded)")
        self.hotkey_candidate = self.settings.hotkey

    # ----- window helpers -----

    def hide_window(self) -> None:
        self.root.withdraw()

    def show_window(self) -> None:
        self.root.deiconify()
        self.root.after(0, lambda: self.root.attributes("-topmost", True))
        self.root.after(10, lambda: self.root.attributes("-topmost", False))

    def on_close(self) -> None:
        # Stop the presser so it doesn't keep running after UI closes.
        self.presser.stop()
        self.root.destroy()

    # ----- hotkey capture (non-blocking) -----

    def capture_combo_async(self) -> None:
        self.combo_label.config(text="Listening... press your hotkey combo now.")
        self.combo_button.config(state="disabled")

        def worker():
            try:
                combo = keyboard.read_hotkey(suppress=False)
            except Exception as e:
                combo = None
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to capture hotkey: {e}"))

            def finish():
                self.combo_button.config(state="normal")
                if combo:
                    self.hotkey_candidate = combo
                    self.combo_label.config(text=f"Hotkey captured: {combo} (not applied yet)")
                else:
                    self.combo_label.config(text="Hotkey capture failed. Try again.")

            self.root.after(0, finish)

        threading.Thread(target=worker, daemon=True).start()

    # ----- apply settings -----

    def apply_settings(self) -> None:
        key = self.key_entry.get().strip()
        delay_text = self.delay_entry.get().strip()
        combo = self.hotkey_candidate or DEFAULT_HOTKEY

        if not key:
            messagebox.showerror("Missing Key", "Please enter a target key.")
            return

        try:
            delay_ms = int(delay_text)
            if delay_ms < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Delay", "Please enter a valid number greater than 0.")
            return

        try:
            self.presser.set_target_key(key)
            self.presser.set_delay_ms(delay_ms)
            self.presser.set_hotkey(combo)

            self.settings = AppSettings(target_key=key, hotkey=combo, delay_ms=delay_ms)
            self.settings.save()

            self.combo_label.config(text=f"Hotkey set to: {combo} (Ready!)")
            messagebox.showinfo("Success", f"Hotkey: {combo}\nKey: {key}\nDelay: {delay_ms} ms")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {e}")

    # ----- status callback -----

    def update_status(self, is_active: bool) -> None:
        if is_active:
            play_sound(ACTIVATE_WAV)
            self.status_button.config(text="✅ Macro Active", bg="#3aff5a", fg="black")
            self.hide_window()
        else:
            play_sound(DEACTIVATE_WAV)
            self.status_button.config(text="⛔ Macro Inactive", bg="#333333", fg="white")
            # stays hidden by design (use alt+` to show)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    DesktopAutomationUI().run()
