"""Task 4: Basic Calculator (Tkinter, no extra installs). Supports keyboard input."""
import tkinter as tk

class Calculator:
    def __init__(self, root):
        self.root = root
        root.title("Calculator"); root.resizable(False, False)
        self.expr = ""
        self.var = tk.StringVar(value="0")
        tk.Entry(root, textvariable=self.var, font=("Arial", 24), justify="right",
                 state="readonly", width=16).grid(row=0, column=0, columnspan=4, padx=6, pady=6)
        keys = [["C", "⌫", "%", "/"], ["7", "8", "9", "*"], ["4", "5", "6", "-"],
                ["1", "2", "3", "+"], ["±", "0", ".", "="]]
        for r, row in enumerate(keys, start=1):
            for c, k in enumerate(row):
                tk.Button(root, text=k, width=5, height=2, font=("Arial", 14),
                          command=lambda k=k: self.press(k)).grid(row=r, column=c, padx=2, pady=2)
        root.bind("<Key>", self.key)

    def key(self, e):
        if e.char in "0123456789.+-*/%": self.press(e.char)
        elif e.keysym in ("Return", "KP_Enter"): self.press("=")
        elif e.keysym == "BackSpace": self.press("⌫")
        elif e.keysym == "Escape": self.press("C")

    def show(self, text): self.var.set(text or "0")

    def press(self, k):
        if k == "C": self.expr = ""
        elif k == "⌫": self.expr = self.expr[:-1]
        elif k == "±": self.negate()
        elif k == "=": self.equals(); return
        else:
            if self.expr and self.expr[-1] in "+-*/%" and k in "+*/%":
                self.expr = self.expr[:-1]  # replace operator
            self.expr += k
        self.show(self.expr)

    def negate(self):
        i = max(self.expr.rfind(o) for o in "+-*/%")
        head, tail = self.expr[:i + 1], self.expr[i + 1:]
        if tail: self.expr = head + (tail[1:] if tail.startswith("-") else "-" + tail)

    def equals(self):
        try:
            result = evaluate(self.expr)
            self.expr = "" if result is None else format_num(result)
            self.show(self.expr)
        except ZeroDivisionError:
            self.expr = ""; self.show("Cannot divide by 0")
        except Exception:
            self.expr = ""; self.show("Error")

def format_num(x):
    return str(int(x)) if float(x).is_integer() else str(round(x, 10))

def evaluate(expr):
    """Safe evaluator for + - * / % with precedence (no eval())."""
    import re
    tokens = re.findall(r"\d+\.?\d*|\.\d+|[+\-*/%]", expr)
    if not tokens: return None
    nums, ops, i, expect_num = [], [], 0, True
    while i < len(tokens):
        t = tokens[i]
        if expect_num:
            if t == "-": # unary minus
                i += 1; t = "-" + tokens[i]
            nums.append(float(t)); expect_num = False
        else:
            ops.append(t); expect_num = True
        i += 1
    def apply(a, op, b):
        if op == "+": return a + b
        if op == "-": return a - b
        if op == "*": return a * b
        if op == "/": return a / b
        return a % b
    # first pass: * / %
    n2, o2 = [nums[0]], []
    for op, n in zip(ops, nums[1:]):
        if op in "*/%": n2[-1] = apply(n2[-1], op, n)
        else: o2.append(op); n2.append(n)
    out = n2[0]
    for op, n in zip(o2, n2[1:]): out = apply(out, op, n)
    return out

if __name__ == "__main__":
    root = tk.Tk(); Calculator(root); root.mainloop()
