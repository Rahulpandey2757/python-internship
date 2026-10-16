"""Task 5 (client): GUI chat client. Run one per user: python client.py"""
import json, socket, threading, tkinter as tk
from tkinter import simpledialog, scrolledtext

HOST, PORT = "127.0.0.1", 5555   # change HOST to the server's IP for other computers

class Client:
    def __init__(self, root):
        self.root = root
        name = simpledialog.askstring("Login", "Username:", parent=root) or "guest"
        bio = simpledialog.askstring("Profile", "Short bio (optional):", parent=root) or ""
        root.title(f"Chat - {name}")
        self.log = scrolledtext.ScrolledText(root, width=70, height=22, state="disabled")
        self.log.pack(padx=8, pady=8)
        self.log.tag_config("info", foreground="gray"); self.log.tag_config("pm", foreground="purple")
        self.log.tag_config("me", foreground="green")
        self.entry = tk.Entry(root, width=60); self.entry.pack(side="left", padx=8, pady=(0, 8))
        self.entry.bind("<Return>", lambda e: self.send()); self.entry.focus()
        tk.Button(root, text="Send", command=self.send).pack(side="left", pady=(0, 8))
        self.name = name
        self.sock = socket.create_connection((HOST, PORT))
        self.raw({"name": name, "bio": bio})
        threading.Thread(target=self.listen, daemon=True).start()

    def raw(self, obj): self.sock.sendall((json.dumps(obj) + "\n").encode())

    def send(self):
        t = self.entry.get().strip(); self.entry.delete(0, "end")
        if t: self.raw({"text": t})

    def listen(self):
        for line in self.sock.makefile("r", encoding="utf-8"):
            m = json.loads(line)
            if m["type"] == "msg":
                tag = "me" if m["name"] == self.name else ""
                self.add(f"[#{m['room']}] {m['name']}: {m['text']}", tag)
            elif m["type"] == "pm": self.add(f"(private) {m['name']}: {m['text']}", "pm")
            else: self.add(f"* {m['text']}", "info")
        self.add("* Disconnected from server", "info")

    def add(self, text, tag=""):
        def do():
            self.log.config(state="normal"); self.log.insert("end", text + "\n", tag)
            self.log.config(state="disabled"); self.log.see("end")
        self.root.after(0, do)

if __name__ == "__main__":
    root = tk.Tk(); Client(root); root.mainloop()
