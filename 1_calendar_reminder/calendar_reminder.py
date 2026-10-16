"""Task 1: Calendar and Reminder App (Tkinter, no extra installs)."""
import calendar, json, os, tkinter as tk
from datetime import datetime, date
from tkinter import ttk, messagebox

FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")

class CalendarApp:
    def __init__(self, root):
        self.root = root
        root.title("Calendar & Reminders")
        today = date.today()
        self.year, self.month, self.selected = today.year, today.month, today
        self.reminders = self.load()
        self.build()
        self.draw()
        self.check_due()

    # ---------- storage ----------
    def load(self):
        try:
            with open(FILE, encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save(self):
        with open(FILE, "w", encoding="utf-8") as f:
            json.dump(self.reminders, f, indent=2)

    # ---------- UI ----------
    def build(self):
        left = ttk.Frame(self.root, padding=10); left.grid(row=0, column=0)
        right = ttk.Frame(self.root, padding=10); right.grid(row=0, column=1, sticky="n")

        nav = ttk.Frame(left); nav.pack(fill="x")
        ttk.Button(nav, text="<", width=3, command=lambda: self.shift(-1)).pack(side="left")
        self.title = ttk.Label(nav, font=("Arial", 14, "bold"), anchor="center")
        self.title.pack(side="left", expand=True, fill="x")
        ttk.Button(nav, text=">", width=3, command=lambda: self.shift(1)).pack(side="right")

        self.grid_frame = ttk.Frame(left); self.grid_frame.pack(pady=8)

        self.sel_label = ttk.Label(right, font=("Arial", 12, "bold")); self.sel_label.pack(anchor="w")
        self.listbox = tk.Listbox(right, width=38, height=12); self.listbox.pack(pady=5)
        row = ttk.Frame(right); row.pack(fill="x")
        ttk.Label(row, text="Time (HH:MM)").pack(side="left")
        self.time_var = tk.StringVar(value="09:00")
        ttk.Entry(row, textvariable=self.time_var, width=7).pack(side="left", padx=5)
        self.text_var = tk.StringVar()
        ttk.Entry(right, textvariable=self.text_var, width=40).pack(pady=4)
        ttk.Button(right, text="Add reminder", command=self.add).pack(fill="x")
        ttk.Button(right, text="Delete selected", command=self.delete).pack(fill="x", pady=3)

    def shift(self, d):
        self.month += d
        if self.month == 0: self.month, self.year = 12, self.year - 1
        if self.month == 13: self.month, self.year = 1, self.year + 1
        self.draw()

    def draw(self):
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.title.config(text=f"{calendar.month_name[self.month]} {self.year}")
        for c, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            ttk.Label(self.grid_frame, text=name, width=5, anchor="center").grid(row=0, column=c)
        marked = {r["date"] for r in self.reminders}
        for r, week in enumerate(calendar.monthcalendar(self.year, self.month), start=1):
            for c, day in enumerate(week):
                if not day: continue
                d = date(self.year, self.month, day)
                bg = "#ffd966" if d.isoformat() in marked else "white"
                if d == date.today(): bg = "#9fe29f"
                if d == self.selected: bg = "#7aa7ff"
                tk.Button(self.grid_frame, text=day, width=4, bg=bg,
                          command=lambda d=d: self.select(d)).grid(row=r, column=c, padx=1, pady=1)
        self.refresh_list()

    def select(self, d):
        self.selected = d
        self.draw()

    def day_items(self):
        return sorted((r for r in self.reminders if r["date"] == self.selected.isoformat()),
                      key=lambda r: r["time"])

    def refresh_list(self):
        self.sel_label.config(text=self.selected.strftime("Reminders for %A, %d %B %Y"))
        self.listbox.delete(0, "end")
        for r in self.day_items():
            self.listbox.insert("end", f"{'✔' if r['done'] else '•'} {r['time']}  {r['text']}")

    # ---------- actions ----------
    def add(self):
        text, t = self.text_var.get().strip(), self.time_var.get().strip()
        try:
            datetime.strptime(t, "%H:%M")
        except ValueError:
            return messagebox.showerror("Invalid time", "Use 24-hour HH:MM, e.g. 14:30")
        if not text:
            return messagebox.showerror("Missing text", "Enter a reminder message.")
        self.reminders.append({"date": self.selected.isoformat(), "time": t, "text": text, "done": False})
        self.save(); self.text_var.set(""); self.draw()

    def delete(self):
        sel = self.listbox.curselection()
        if not sel: return
        self.reminders.remove(self.day_items()[sel[0]])
        self.save(); self.draw()

    def check_due(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for r in self.reminders:
            if not r["done"] and f"{r['date']} {r['time']}" <= now:
                r["done"] = True
                self.save(); self.draw()
                self.root.bell()
                messagebox.showinfo("Reminder", f"{r['time']} - {r['text']}")
        self.root.after(15000, self.check_due)

if __name__ == "__main__":
    root = tk.Tk()
    CalendarApp(root)
    root.mainloop()
