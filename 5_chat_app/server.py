"""Task 5 (server): Real-time chat server using sockets + threads. Run first: python server.py"""
import json, socket, threading

HOST, PORT = "0.0.0.0", 5555
lock = threading.Lock()
clients = {}   # socket -> {"name":..., "bio":..., "room":...}

def send(sock, **msg):
    try: sock.sendall((json.dumps(msg) + "\n").encode())
    except OSError: pass

def broadcast_room(room_name, **msg):
    with lock:
        targets = [s for s, u in clients.items() if u["room"] == room_name]
    for s in targets: send(s, **msg)

def rooms():
    with lock: return sorted({u["room"] for u in clients.values()})

def handle(sock):
    f = sock.makefile("r", encoding="utf-8")
    try:
        hello = json.loads(f.readline())
        name = hello["name"].strip()[:20] or "guest"
        with lock:
            if any(u["name"].lower() == name.lower() for u in clients.values()):
                name += str(len(clients) + 1)
            clients[sock] = {"name": name, "bio": hello.get("bio", ""), "room": "lobby"}
        send(sock, type="info", text=f"Welcome {name}! Commands: /join <room>, /rooms, /who, /whois <name>, /pm <name> <msg>, /bio <text>")
        broadcast_room("lobby", type="info", text=f"{name} joined #lobby")
        for line in f:
            text = json.loads(line).get("text", "").strip()
            if not text: continue
            user = clients[sock]
            if text.startswith("/join "):
                old, new = user["room"], text[6:].strip()[:20] or "lobby"
                broadcast_room(old, type="info", text=f"{name} left #{old}")
                user["room"] = new
                send(sock, type="info", text=f"You are now in #{new}")
                broadcast_room(new, type="info", text=f"{name} joined #{new}")
            elif text == "/rooms": send(sock, type="info", text="Active rooms: " + ", ".join("#" + r for r in rooms()))
            elif text == "/who":
                with lock: names = [u["name"] for u in clients.values() if u["room"] == user["room"]]
                send(sock, type="info", text=f"In #{user['room']}: " + ", ".join(names))
            elif text.startswith("/whois "):
                with lock: m = [u for u in clients.values() if u["name"].lower() == text[7:].strip().lower()]
                send(sock, type="info", text=(f"{m[0]['name']} - {m[0]['bio'] or 'no bio'} (in #{m[0]['room']})" if m else "No such user."))
            elif text.startswith("/bio "):
                user["bio"] = text[5:][:100]; send(sock, type="info", text="Profile updated.")
            elif text.startswith("/pm "):
                parts = text.split(" ", 2)
                with lock: dest = [s for s, u in clients.items() if len(parts) == 3 and u["name"].lower() == parts[1].lower()]
                if dest: send(dest[0], type="pm", name=name, text=parts[2]); send(sock, type="pm", name=f"to {parts[1]}", text=parts[2])
                else: send(sock, type="info", text="Usage: /pm <name> <message> (user must be online)")
            else:
                broadcast_room(user["room"], type="msg", name=name, room=user["room"], text=text)
    except (ValueError, KeyError, OSError):
        pass
    finally:
        with lock: user = clients.pop(sock, None)
        if user: broadcast_room(user["room"], type="info", text=f"{user['name']} left.")
        sock.close()

def main():
    srv = socket.socket(); srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, PORT)); srv.listen()
    print(f"Chat server listening on port {PORT}")
    while True:
        s, _ = srv.accept()
        threading.Thread(target=handle, args=(s,), daemon=True).start()

if __name__ == "__main__":
    main()
