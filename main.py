import customtkinter as ctk
import pyautogui
import pyperclip
import time
import random
import keyboard
from threading import Thread, Event

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

BG       = "#0d0d0f"
SURFACE  = "#141416"
SURFACE2 = "#1c1c20"
BORDER   = "#2a2a2e"
BLUE     = "#5865F2"
BLUE2    = "#4752C4"
GREEN    = "#23D18B"
RED      = "#E74C3C"
ORANGE   = "#F0A500"
GRAY     = "#888890"

APP_VERSION = "1.1.0"

class AutoTyper(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"AutoTyper Pro  v{APP_VERSION}")
        self.geometry("540x620")
        self.resizable(False, False)
        self.configure(fg_color=BG)

        self.running = False
        self.stop_event = Event()
        self.messages = []
        self.current_index = 0

        self._build_ui()
        self._bind_hotkey()

    def _build_ui(self):
        # ── Header ──
        hdr = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        hdr.pack(fill="x")
        inner = ctk.CTkFrame(hdr, fg_color="transparent")
        inner.pack(pady=14, padx=24, fill="x")
        ctk.CTkLabel(inner, text="AUTOTYPER", font=ctk.CTkFont(family="Consolas", size=22, weight="bold"), text_color=BLUE).pack(side="left")
        ctk.CTkLabel(inner, text=f"PRO  v{APP_VERSION}", font=ctk.CTkFont(family="Consolas", size=12), text_color=GRAY).pack(side="left", padx=8, pady=4)
        self.hotkey_label = ctk.CTkLabel(inner, text="F6 to stop", font=ctk.CTkFont(size=11), text_color=GRAY)
        self.hotkey_label.pack(side="right")

        # ── Messages ──
        self._section("MESSAGES")
        self.msg_entry = ctk.CTkEntry(self, placeholder_text="hey, what's up, lol, same",
                                      height=38, font=ctk.CTkFont(size=13),
                                      fg_color=SURFACE2, border_color=BORDER, border_width=1)
        self.msg_entry.pack(pady=(2, 8), padx=24, fill="x")

        # ── Options row ──
        r1 = self._row()
        self._tag(r1, "MODE")
        self.mode_var = ctk.StringVar(value="Sequential")
        ctk.CTkOptionMenu(r1, values=["Sequential", "Random"], variable=self.mode_var,
                          width=130, height=32, fg_color=SURFACE2, button_color=BLUE,
                          button_hover_color=BLUE2, font=ctk.CTkFont(size=12)).pack(side="left", padx=(4,16))

        self._tag(r1, "METHOD")
        self.method_var = ctk.StringVar(value="Clipboard")
        ctk.CTkOptionMenu(r1, values=["Clipboard", "Typewrite"],
                          variable=self.method_var, width=120, height=32,
                          fg_color=SURFACE2, button_color=BLUE, button_hover_color=BLUE2,
                          font=ctk.CTkFont(size=12)).pack(side="left", padx=4)

        # ── Prefix / Suffix ──
        r2 = self._row()
        self._tag(r2, "PREFIX")
        self.prefix_entry = ctk.CTkEntry(r2, width=90, height=32, placeholder_text="!!",
                                          fg_color=SURFACE2, border_color=BORDER, border_width=1)
        self.prefix_entry.pack(side="left", padx=(4,16))
        self._tag(r2, "SUFFIX")
        self.suffix_entry = ctk.CTkEntry(r2, width=90, height=32, placeholder_text="😂",
                                          fg_color=SURFACE2, border_color=BORDER, border_width=1)
        self.suffix_entry.pack(side="left", padx=4)

        self._divider()

        # ── Timing ──
        self._section("TIMING")
        r3 = self._row()
        self._tag(r3, "MIN DELAY")
        self.min_delay = self._numbox(r3, "0.8")
        self._tag(r3, "MAX DELAY", pad=16)
        self.max_delay = self._numbox(r3, "1.5")
        self._tag(r3, "TOTAL  (0=∞)", pad=16)
        self.count_entry = self._numbox(r3, "0")

        # Typewrite speed
        r4 = self._row()
        self._tag(r4, "TYPEWRITE SPEED")
        self.speed_slider = ctk.CTkSlider(r4, from_=0.0, to=0.08, number_of_steps=16,
                                           width=160, button_color=BLUE, button_hover_color=BLUE2,
                                           command=self._update_speed)
        self.speed_slider.set(0.03)
        self.speed_slider.pack(side="left", padx=(8,8))
        self.speed_val = ctk.CTkLabel(r4, text="0.030s", font=ctk.CTkFont(family="Consolas", size=11), text_color=GRAY)
        self.speed_val.pack(side="left")

        self._divider()

        # ── Burst control ──
        self._section("BURST CONTROL")
        r5 = self._row()
        self._tag(r5, "BURST SIZE")
        self.burst_entry = self._numbox(r5, "0", tip="msgs before pause (0=off)")
        self._tag(r5, "BURST PAUSE (s)", pad=16)
        self.burst_pause = self._numbox(r5, "5.0")

        self._divider()

        # ── Buttons ──
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(pady=12)
        self.start_btn = ctk.CTkButton(bf, text="▶  START", width=160, height=44,
                                        font=ctk.CTkFont(size=15, weight="bold"),
                                        fg_color=BLUE, hover_color=BLUE2, command=self._start)
        self.start_btn.pack(side="left", padx=8)
        self.stop_btn = ctk.CTkButton(bf, text="■  STOP", width=160, height=44,
                                       font=ctk.CTkFont(size=15, weight="bold"),
                                       fg_color=RED, hover_color="#B03030",
                                       state="disabled", command=self._stop)
        self.stop_btn.pack(side="left", padx=8)

        # ── Status bar ──
        sb = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0, height=56)
        sb.pack(fill="x", side="bottom")
        sb.pack_propagate(False)
        sbi = ctk.CTkFrame(sb, fg_color="transparent")
        sbi.pack(fill="both", expand=True, padx=20, pady=8)
        self.status_label = ctk.CTkLabel(sbi, text="Ready  —  focus Discord before starting",
                                          font=ctk.CTkFont(size=12), text_color=GREEN, anchor="w")
        self.status_label.pack(side="left", fill="x", expand=True)
        self.sent_label = ctk.CTkLabel(sbi, text="0", font=ctk.CTkFont(family="Consolas", size=20, weight="bold"), text_color=BLUE)
        self.sent_label.pack(side="right")

    # ── Helpers ──

    def _section(self, text):
        ctk.CTkLabel(self, text=text, font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                     text_color=GRAY).pack(anchor="w", padx=24, pady=(8,0))

    def _divider(self):
        ctk.CTkFrame(self, height=1, fg_color=BORDER).pack(fill="x", padx=24, pady=6)

    def _row(self):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.pack(pady=3, padx=24, fill="x")
        return f

    def _tag(self, parent, text, pad=0):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(family="Consolas", size=10),
                     text_color=GRAY).pack(side="left", padx=(pad, 0))

    def _numbox(self, parent, default, tip=None, width=70):
        e = ctk.CTkEntry(parent, width=width, height=32, fg_color=SURFACE2,
                         border_color=BORDER, border_width=1,
                         font=ctk.CTkFont(family="Consolas", size=12))
        e.pack(side="left", padx=(4, 0))
        e.insert(0, default)
        return e

    def _update_speed(self, val):
        self.speed_val.configure(text=f"{float(val):.3f}s")

    def _set_status(self, text, color=GREEN):
        self.status_label.configure(text=text, text_color=color)

    def _bind_hotkey(self):
        try:
            keyboard.add_hotkey("f6", self._stop)
        except Exception:
            self.hotkey_label.configure(text="(hotkey unavailable)")

    # ── Logic ──

    def _parse(self):
        raw = self.msg_entry.get().strip()
        if not raw:
            raise ValueError("Enter at least one message.")
        msgs = [m.strip() for m in raw.split(",") if m.strip()]
        min_d = float(self.min_delay.get())
        max_d = float(self.max_delay.get())
        if min_d < 0 or max_d < min_d:
            raise ValueError("Delays must be >= 0 and min <= max.")
        total = int(self.count_entry.get())
        burst = int(self.burst_entry.get())
        bpause = float(self.burst_pause.get())
        interval = self.speed_slider.get()
        return msgs, min_d, max_d, total, interval, burst, bpause

    def _start(self):
        if self.running:
            return
        try:
            msgs, min_d, max_d, total, interval, burst, bpause = self._parse()
        except ValueError as e:
            self._set_status(f"Error: {e}", RED)
            return
        self.messages = msgs
        self.current_index = 0
        self.running = True
        self.stop_event.clear()
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self._set_status("Starting in 3s — switch to Discord!", BLUE)
        Thread(target=self._loop, args=(min_d, max_d, total, interval, burst, bpause), daemon=True).start()

    def _loop(self, min_d, max_d, total, interval, burst, bpause):
        for i in range(3, 0, -1):
            if self.stop_event.is_set():
                self.after(0, self._finish)
                return
            self.after(0, lambda n=i: self._set_status(f"Starting in {n}...", BLUE))
            time.sleep(1)

        # Click the active window to make sure Discord is focused
        try:
            pyautogui.click()
            time.sleep(0.2)
        except Exception:
            pass

        sent = 0
        burst_count = 0

        while (total == 0 or sent < total) and not self.stop_event.is_set():
            msg = (random.choice(self.messages) if self.mode_var.get() == "Random"
                   else self.messages[self.current_index % len(self.messages)])
            self.current_index += 1
            full = self.prefix_entry.get() + msg + self.suffix_entry.get()

            try:
                if self.method_var.get() == "Clipboard":
                    pyperclip.copy(full)
                    pyautogui.hotkey("ctrl", "v")
                else:
                    safe = full.encode("ascii", errors="replace").decode("ascii")
                    pyautogui.typewrite(safe, interval=interval)
                pyautogui.press("enter")
            except Exception as e:
                self.after(0, lambda err=str(e): self._set_status(f"Error: {err}", RED))
                break

            sent += 1
            burst_count += 1
            total_str = "inf" if total == 0 else str(total)
            self.after(0, lambda s=sent: self.sent_label.configure(text=str(s)))
            short = full[:32] + ("..." if len(full) > 32 else "")
            self.after(0, lambda t=short, ts=total_str, s=sent: self._set_status(f"{t}  [{s}/{ts}]", GREEN))

            # Burst pause
            if burst > 0 and burst_count >= burst:
                burst_count = 0
                self.after(0, lambda: self._set_status(f"Burst pause {bpause}s...", ORANGE))
                time.sleep(bpause)
                continue

            time.sleep(random.uniform(min_d, max_d))

        self.after(0, self._finish)

    def _finish(self):
        self.running = False
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        if self.stop_event.is_set():
            self._set_status("Stopped.", ORANGE)
        else:
            self._set_status("Done!", GREEN)

    def _stop(self):
        if self.running:
            self.stop_event.set()
            self._set_status("Stopping...", ORANGE)


if __name__ == "__main__":
    app = AutoTyper()
    app.mainloop()
