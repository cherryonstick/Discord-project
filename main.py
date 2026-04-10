# main.py  —  host this on GitHub, edit here to update the app
# Users never need a new .exe — the launcher fetches this automatically.

import customtkinter as ctk
import pyautogui
import pyperclip
import time
import random
from threading import Thread, Event

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

DISCORD_BLUE = "#5865F2"
SUCCESS_GREEN = "#23D18B"
DANGER_RED    = "#E74C3C"
BG      = "#0d0d0f"
SURFACE = "#17171a"
BORDER  = "#2a2a2e"

APP_VERSION = "1.0.0"   # bump this string whenever you push an update

class DiscordAutoTyper(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"Discord AutoTyper Pro  v{APP_VERSION}")
        self.geometry("560x680")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.running = False
        self.stop_event = Event()
        self.messages = []
        self.current_index = 0

        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────

    def _build_ui(self):
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(pady=(22, 4), padx=30, fill="x")
        ctk.CTkLabel(title_frame, text="AUTOTYPER PRO",
                     font=ctk.CTkFont(family="Consolas", size=26, weight="bold"),
                     text_color=DISCORD_BLUE).pack(side="left")
        ctk.CTkLabel(title_frame, text=f"v{APP_VERSION}",
                     font=ctk.CTkFont(size=12), text_color="gray").pack(side="left", padx=8, pady=6)

        self._divider()

        self._label("Messages  (comma-separated)")
        self.msg_entry = ctk.CTkEntry(self, placeholder_text="hey, what's up, lol, same",
                                      height=40, font=ctk.CTkFont(size=14),
                                      fg_color=SURFACE, border_color=BORDER)
        self.msg_entry.pack(pady=(4, 10), padx=30, fill="x")
        self.msg_entry.bind("<KeyRelease>", lambda e: self._refresh_preview())

        row = self._row()
        self._mini_label(row, "Prefix")
        self.prefix_entry = ctk.CTkEntry(row, width=75, placeholder_text="!!",
                                         fg_color=SURFACE, border_color=BORDER)
        self.prefix_entry.pack(side="left", padx=(4, 14))
        self.prefix_entry.bind("<KeyRelease>", lambda e: self._refresh_preview())

        self._mini_label(row, "Suffix")
        self.suffix_entry = ctk.CTkEntry(row, width=75, placeholder_text="😂",
                                         fg_color=SURFACE, border_color=BORDER)
        self.suffix_entry.pack(side="left", padx=(4, 14))
        self.suffix_entry.bind("<KeyRelease>", lambda e: self._refresh_preview())

        self._mini_label(row, "Mode")
        self.mode_var = ctk.StringVar(value="Sequential")
        ctk.CTkOptionMenu(row, values=["Sequential", "Random"], variable=self.mode_var,
                          width=120, fg_color=SURFACE, button_color=DISCORD_BLUE).pack(side="left")

        row2 = self._row()
        self._mini_label(row2, "Send method")
        self.method_var = ctk.StringVar(value="Clipboard (Unicode safe)")
        ctk.CTkOptionMenu(row2, values=["Clipboard (Unicode safe)", "Typewrite (ASCII only)"],
                          variable=self.method_var, width=220,
                          fg_color=SURFACE, button_color=DISCORD_BLUE).pack(side="left", padx=4)

        self._divider()

        delay_row = self._row()
        self._mini_label(delay_row, "Min delay (s)")
        self.min_delay = self._num_entry(delay_row, "0.8", 70)
        ctk.CTkLabel(delay_row, text="", width=20).pack(side="left")
        self._mini_label(delay_row, "Max delay (s)")
        self.max_delay = self._num_entry(delay_row, "1.5", 70)
        ctk.CTkLabel(delay_row, text="", width=20).pack(side="left")
        self._mini_label(delay_row, "Total (0 = ∞)")
        self.count_entry = self._num_entry(delay_row, "0", 70)

        speed_frame = ctk.CTkFrame(self, fg_color="transparent")
        speed_frame.pack(pady=(10, 4), padx=30, fill="x")
        self._mini_label(speed_frame, "Typewrite speed (sec/char)  —  ignored in Clipboard mode")
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=0.0, to=0.08, number_of_steps=16,
                                          command=self._update_speed_label)
        self.speed_slider.set(0.03)
        self.speed_slider.pack(fill="x", pady=(4, 0))
        self.speed_label = ctk.CTkLabel(speed_frame, text="0.030 s/char", text_color="gray",
                                        font=ctk.CTkFont(size=12))
        self.speed_label.pack(anchor="e")

        self._divider()

        self._label("Preview  (first message)")
        self.preview_label = ctk.CTkLabel(self, text="—",
                                          font=ctk.CTkFont(family="Consolas", size=13),
                                          text_color=SUCCESS_GREEN, fg_color=SURFACE,
                                          corner_radius=6, anchor="w")
        self.preview_label.pack(pady=(4, 12), padx=30, fill="x", ipady=8, ipadx=10)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=6)
        self.start_btn = ctk.CTkButton(btn_frame, text="▶  START", width=170, height=48,
                                        font=ctk.CTkFont(size=16, weight="bold"),
                                        fg_color=DISCORD_BLUE, hover_color="#4752C4",
                                        command=self._start)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn  = ctk.CTkButton(btn_frame, text="■  STOP", width=170, height=48,
                                        font=ctk.CTkFont(size=16, weight="bold"),
                                        fg_color=DANGER_RED, hover_color="#C0392B",
                                        state="disabled", command=self._stop)
        self.stop_btn.pack(side="left", padx=8)

        self.status_label = ctk.CTkLabel(self,
                                          text="● Ready  —  focus Discord chat before starting",
                                          font=ctk.CTkFont(size=13), text_color=SUCCESS_GREEN)
        self.status_label.pack(pady=(10, 2))
        self.sent_label = ctk.CTkLabel(self, text="SENT  0",
                                        font=ctk.CTkFont(family="Consolas", size=22, weight="bold"),
                                        text_color=DISCORD_BLUE)
        self.sent_label.pack(pady=(0, 16))

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _divider(self):
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(fill="x", padx=30, pady=8)

    def _label(self, text):
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(size=13),
                     text_color="gray").pack(anchor="w", padx=30)

    def _mini_label(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12),
                     text_color="gray").pack(side="left")

    def _row(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(pady=5, padx=30, fill="x")
        return f

    def _num_entry(self, parent, default, width):
        e = ctk.CTkEntry(parent, width=width, fg_color=SURFACE, border_color=BORDER,
                         font=ctk.CTkFont(family="Consolas"))
        e.pack(side="left", padx=(4, 0))
        e.insert(0, default)
        return e

    def _update_speed_label(self, val):
        self.speed_label.configure(text=f"{float(val):.3f} s/char")

    def _refresh_preview(self):
        raw = self.msg_entry.get().strip()
        if not raw:
            self.preview_label.configure(text="—")
            return
        first = raw.split(",")[0].strip()
        full = self.prefix_entry.get() + first + self.suffix_entry.get()
        self.preview_label.configure(text=(full[:60] + ("…" if len(full) > 60 else "")) or "—")

    def _set_status(self, text, color=SUCCESS_GREEN):
        self.status_label.configure(text=text, text_color=color)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _parse_inputs(self):
        raw = self.msg_entry.get().strip()
        if not raw:
            raise ValueError("Enter at least one message.")
        messages = [m.strip() for m in raw.split(",") if m.strip()]
        min_d  = float(self.min_delay.get())
        max_d  = float(self.max_delay.get())
        if min_d < 0 or max_d < min_d:
            raise ValueError("Delays must be ≥ 0 and min ≤ max.")
        total    = int(self.count_entry.get())
        interval = self.speed_slider.get()
        return messages, min_d, max_d, total, interval

    def _start(self):
        if self.running:
            return
        try:
            messages, min_d, max_d, total, interval = self._parse_inputs()
        except ValueError as e:
            self._set_status(f"✗  {e}", DANGER_RED)
            return

        self.messages = messages
        self.current_index = 0
        self.running = True
        self.stop_event.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status("Starting in 3 seconds — switch to Discord now!", DISCORD_BLUE)
        Thread(target=self._spam_loop,
               args=(min_d, max_d, total, interval, self.method_var.get()),
               daemon=True).start()

    def _spam_loop(self, min_d, max_d, total, interval, method):
        for i in range(3, 0, -1):
            if self.stop_event.is_set():
                self.after(0, self._finish)
                return
            self.after(0, lambda n=i: self._set_status(f"Starting in {n}…", DISCORD_BLUE))
            time.sleep(1)

        sent = 0
        while (total == 0 or sent < total) and not self.stop_event.is_set():
            msg = (random.choice(self.messages) if self.mode_var.get() == "Random"
                   else self.messages[self.current_index % len(self.messages)])
            self.current_index += 1
            full_msg = self.prefix_entry.get() + msg + self.suffix_entry.get()

            try:
                if method.startswith("Clipboard"):
                    pyperclip.copy(full_msg)
                    pyautogui.hotkey("ctrl", "v")
                else:
                    safe = full_msg.encode("ascii", errors="replace").decode("ascii")
                    pyautogui.typewrite(safe, interval=interval)
                pyautogui.press("enter")
            except Exception as e:
                self.after(0, lambda err=e: self._set_status(f"✗ Error: {err}", DANGER_RED))
                break

            sent += 1
            total_str = "∞" if total == 0 else str(total)
            preview = full_msg[:28] + ("…" if len(full_msg) > 28 else "")
            self.after(0, lambda s=sent, ts=total_str: self.sent_label.configure(text=f"SENT  {s} / {ts}"))
            self.after(0, lambda t=preview: self._set_status(f"Sent: {t}", SUCCESS_GREEN))

            time.sleep(random.uniform(min_d, max_d))

        self.after(0, self._finish)

    def _finish(self):
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        if self.stop_event.is_set():
            self._set_status("■ Stopped.", "orange")
        else:
            self._set_status("✓ All messages sent!", SUCCESS_GREEN)

    def _stop(self):
        self.stop_event.set()
        self._set_status("Stopping…", "orange")


if __name__ == "__main__":
    app = DiscordAutoTyper()
    app.mainloop()
