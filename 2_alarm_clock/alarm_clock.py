import sys, threading, time, tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk, messagebox

try:
    import winsound
except ImportError:
    winsound = None

TONES = {
    "Classic": [(1000, 200), (0, 100)] * 4,
    "Rising": [(500, 150), (700, 150), (900, 150), (1200, 250)],
    "Siren": [(900, 300), (600, 300)] * 3,
    "Pulse": [(1500, 80), (0, 80)] * 8,
}

def play(tone, root):
    def run():
        for freq, ms in TONES[tone]:
            if winsound:
                winsound.Beep(freq, ms) if freq else time.sleep(ms / 1000)
            else:
                root.bell()
                time.sleep(ms / 1000 + 0.1)
    threading.Thread(target=run, daemon=True).start()

class AlarmClock:
    def __init__(self, root):
        self.root, self.alarms = root, []
        root.title("Alarm Clock")
        self.clock = ttk.Label(root, font=("Arial", 32, "bold"))
        self.clock.pack(pady=10)

        f = ttk.Frame(root, padding=8)
        f.pack()

        self.hour = tk.Spinbox(f, from_=0, to=23, width=3, format="%02.0f")
        self.hour.grid(row=0, column=0)

        ttk.Label(f, text=":").grid(row=0, column=1)

        self.minute = tk.Spinbox(f, from_=0, to=59, width=3, format="%02.0f")
        self.minute.grid(row=0, column=2)

        self.tone = ttk.Combobox(
            f,
            values=list(TONES),
            state="readonly",
            width=10
        )
        self.tone.current(0)
        self.tone.grid(row=0, column=3, padx=8)

        ttk.Label(f, text="Snooze (min)").grid(
            row=1, column=0, columnspan=2, pady=6
        )

        self.snooze = tk.Spinbox(f, from_=1, to=30, width=3)
        self.snooze.delete(0, "end")
        self.snooze.insert(0, "5")
        self.snooze.grid(row=1, column=2)

        self.label = ttk.Entry(f, width=14)
        self.label.insert(0, "Alarm")
        self.label.grid(row=1, column=3)

        ttk.Button(
            f,
            text="Set alarm",
            command=self.add
        ).grid(row=2, column=0, columnspan=4, pady=6, sticky="we")

        ttk.Button(
            f,
            text="Preview tone",
            command=lambda: play(self.tone.get(), root)
        ).grid(row=3, column=0, columnspan=4, sticky="we")

        self.box = tk.Listbox(root, width=45, height=6)
        self.box.pack(padx=8)

        ttk.Button(
            root,
            text="Delete selected",
            command=self.delete
        ).pack(pady=6)

        self.tick()

    def add(self):
        h, m = int(self.hour.get()), int(self.minute.get())
        now = datetime.now()

        when = now.replace(
            hour=h,
            minute=m,
            second=0,
            microsecond=0
        )

        if when <= now:
            when += timedelta(days=1)

        self.alarms.append({
            "when": when,
            "tone": self.tone.get(),
            "snooze": int(self.snooze.get()),
            "label": self.label.get() or "Alarm"
        })

        self.refresh()

    def delete(self):
        sel = self.box.curselection()

        if sel:
            self.alarms.pop(sel[0])
            self.refresh()

    def refresh(self):
        self.alarms.sort(key=lambda a: a["when"])
        self.box.delete(0, "end")

        for a in self.alarms:
            self.box.insert(
                "end",
                f"{a['when']:%d %b %H:%M}  {a['label']}  "
                f"[{a['tone']}, snooze {a['snooze']}m]"
            )

    def tick(self):
        now = datetime.now()
        self.clock.config(text=now.strftime("%H:%M:%S"))

        for a in list(self.alarms):
            if now >= a["when"]:
                self.alarms.remove(a)
                self.refresh()
                self.ring(a)

        self.root.after(500, self.tick)

    def ring(self, a):
        win = tk.Toplevel(self.root)
        win.title("Alarm!")

        ttk.Label(
            win,
            text=f"⏰ {a['label']}",
            font=("Arial", 20)
        ).pack(padx=30, pady=15)

        stop = {"on": True}

        def loop():
            if stop["on"]:
                play(a["tone"], self.root)
                win.after(3000, loop)

        def dismiss():
            stop["on"] = False
            win.destroy()

        def snooze():
            a["when"] = datetime.now() + timedelta(minutes=a["snooze"])
            self.alarms.append(a)
            self.refresh()
            dismiss()

        ttk.Button(
            win,
            text=f"Snooze {a['snooze']} min",
            command=snooze
        ).pack(fill="x", padx=20)

        ttk.Button(
            win,
            text="Dismiss",
            command=dismiss
        ).pack(fill="x", padx=20, pady=10)

        win.protocol("WM_DELETE_WINDOW", dismiss)
        loop()

if __name__ == "__main__":
    root = tk.Tk()
    AlarmClock(root)
    root.mainloop()

