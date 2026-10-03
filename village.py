#!/usr/bin/env python3
"""The Village That Looks Back (terminal edition)
Quriosity / ISAQC, Option 01: Basis switching and measurement scrambling.

Pure Python, no dependencies.   python village.py          play
                                python village.py --test   run physics self-test
"""
import math
import random
import sys

RNG = random.SystemRandom()
S = math.sqrt(0.5)
H = ((S, S), (S, -S))      # Mirror
X = ((0, 1), (1, 0))       # Spin vane (bit flip)
Z = ((1, 0), (0, -1))      # Fog bell (phase flip)

READ = {"Z": ("faces you", "turns away"),
        "X": ("steps into the light", "slips into shadow")}
NAME = {"Z": "Plain", "X": "Dusk"}


class Reg:
    """State vector of n qubits. Qubit k is bit k of the basis index."""

    def __init__(self, n):
        self.n = n
        self.a = [0j] * (1 << n)
        self.a[0] = 1 + 0j

    def gate(self, k, m):
        b = 1 << k
        for i in range(len(self.a)):
            if i & b:
                continue
            j = i | b
            x, y = self.a[i], self.a[j]
            self.a[i] = m[0][0] * x + m[0][1] * y
            self.a[j] = m[1][0] * x + m[1][1] * y

    def link(self, c, t):
        """CNOT: flips t when c is 1."""
        cb, tb = 1 << c, 1 << t
        for i in range(len(self.a)):
            if (i & cb) and not (i & tb):
                j = i | tb
                self.a[i], self.a[j] = self.a[j], self.a[i]

    def p1(self, k):
        return sum(abs(v) ** 2 for i, v in enumerate(self.a) if i & (1 << k))

    def prob(self, i):
        return abs(self.a[i]) ** 2

    def look(self, k, lens="Z"):
        """Photograph qubit k through a lens. Z = plain, X = dusk.
        Collapses the state: the other basis' information is destroyed."""
        if lens == "X":
            self.gate(k, H)
        p = self.p1(k)
        out = 1 if RNG.random() < p else 0
        b = 1 << k
        norm = math.sqrt(p if out else 1 - p)
        for i in range(len(self.a)):
            if bool(i & b) != bool(out):
                self.a[i] = 0j
            else:
                self.a[i] /= norm
        if lens == "X":
            self.gate(k, H)
        return out


# ---------------------------------------------------------------- self-test
def selftest():
    T = []

    def ok(name, v):
        T.append((name, bool(v)))

    def run(f, n=300):
        return sum(f() for _ in range(n))

    r = Reg(1); r.gate(0, H); r.gate(0, H)
    ok("two mirrors return home", abs(r.a[0] - 1) < 1e-12)

    def dusk():
        r = Reg(1); r.gate(0, H); return r.look(0, "X")
    ok("dusk lens is certain on a dusk figure", run(dusk) == 0)

    def plain():
        r = Reg(1); r.gate(0, H); return r.look(0, "Z")
    ok("plain lens on it is a coin flip", 90 < run(plain) < 210)

    def again():
        r = Reg(1); r.gate(0, H); a = r.look(0, "Z"); return int(r.look(0, "Z") == a)
    ok("a second look repeats the first", run(again) == 300)

    def mfm():
        r = Reg(1); r.gate(0, H); r.gate(0, Z); r.gate(0, H); return r.look(0, "Z")
    ok("mirror, fog, mirror always arrives", run(mfm) == 300)

    def peek():
        r = Reg(1); r.gate(0, H); r.look(0, "Z"); r.gate(0, Z); r.gate(0, H)
        return r.look(0, "Z")
    ok("a look in the middle ruins it", 90 < run(peek) < 210)

    for la, lb, lo, hi in (("Z", "Z", 300, 300), ("X", "X", 300, 300), ("Z", "X", 90, 210)):
        def twins():
            r = Reg(2); r.gate(0, H); r.link(0, 1)
            return int(r.look(0, la) == r.look(1, lb))
        ok(f"twins {la}/{lb} agree", lo <= run(twins) <= hi)

    r = Reg(3)
    for i in range(3):
        r.gate(i, H)
    r.look(1, "Z")
    ok("total stays one", abs(sum(abs(v) ** 2 for v in r.a) - 1) < 1e-12)
    return T


# ------------------------------------------------------------------ helpers
def ask(prompt="> "):
    try:
        return input(prompt).strip().lower().split()
    except EOFError:
        print("\nYou walk away from the fog.")
        sys.exit(0)


def idx(parts, n):
    """Parse 'p 2' style (1-based) into a 0-based index, or None."""
    if len(parts) > 1 and parts[1].isdigit() and 1 <= int(parts[1]) <= n:
        return int(parts[1]) - 1
    print(f"  Give a number from 1 to {n}.")
    return None


def hearts(n):
    return "♥" * n + "♡" * (3 - n)


# ------------------------------------------------------------------- levels
def level1():
    note = ("Goal: ring the bell once all three statues are turned away.\n"
            "  p N = photograph statue N   s N = spin its vane   r = ring the bell")
    r = Reg(3)
    for i in range(3):
        r.gate(i, H)
    k = [None, None, None]
    print(note)
    while True:
        print("  " + " | ".join(f"{i+1}: " + ("veiled" if k[i] is None else READ["Z"][k[i]])
                                for i in range(3)))
        c = ask()
        if not c:
            continue
        if c[0] == "p" and (i := idx(c, 3)) is not None:
            k[i] = r.look(i, "Z")
            print(f"  Flash. Statue {i+1} {READ['Z'][k[i]]}.")
        elif c[0] == "s" and (i := idx(c, 3)) is not None:
            r.gate(i, X)
            if k[i] is not None:
                k[i] ^= 1
            print(f"  You spin the weathervane on statue {i+1}.")
        elif c[0] == "r":
            o = [r.look(i, "Z") for i in range(3)]
            if all(o):
                return True
            print("  The bell tolls, but at least one statue still faced you.")
            return False


def level2():
    note = ("Goal: copy each figure into the door code (0 = faces you / steps into the light,\n"
            "  1 = turns away / slips into shadow). A candle on the sill means use the Dusk lens.\n"
            "  z / x = choose Plain / Dusk lens   p N = photograph window N   d 0101 = try the door")
    r = Reg(4)
    bits = [RNG.randrange(2) for _ in range(4)]
    dusk = [RNG.randrange(2) for _ in range(4)]
    for i in range(4):
        if bits[i]:
            r.gate(i, X)
        if dusk[i]:
            r.gate(i, H)
    hist = [[] for _ in range(4)]
    lens = "Z"
    print(note)
    while True:
        print(f"  Lens: {NAME[lens]}")
        for i in range(4):
            candle = "🕯 " if dusk[i] else "   "
            seen = " / ".join(hist[i][-2:]) or "unseen"
            print(f"  Window {i+1} {candle}: {seen}")
        c = ask()
        if not c:
            continue
        if c[0] in ("z", "x"):
            lens = c[0].upper()
        elif c[0] == "p" and (i := idx(c, 4)) is not None:
            o = r.look(i, lens)
            hist[i].append(READ[lens][o])
            print(f"  Window {i+1}: the figure {READ[lens][o]}.")
        elif c[0] == "d" and len(c) > 1 and len(c[1]) == 4 and set(c[1]) <= {"0", "1"}:
            if [int(ch) for ch in c[1]] == bits:
                return True
            print("  Wrong code. The figures turn to watch you.")
            return False
        elif c[0] == "d":
            print("  Give four digits, like: d 0110")


def level3():
    note = ("Goal: make the lanterns agree three times in a row. Bind them before every photo.\n"
            "  b = bind at the shrine   s Z X = photograph both shores (lens for A, then B)")
    streak = 0
    r, bound = Reg(2), False
    print(note)
    while True:
        print(f"  Streak {streak}/3   Lanterns {'bound' if bound else 'not bound'}")
        c = ask()
        if not c:
            continue
        if c[0] == "b" and not bound:
            r.gate(0, H); r.link(0, 1); bound = True
            print("  The two flames lean together. They are now bound.")
        elif c[0] == "s" and len(c) == 3 and c[1] in ("z", "x") and c[2] in ("z", "x"):
            la, lb = c[1].upper(), c[2].upper()
            was = bound
            a, b = r.look(0, la), r.look(1, lb)
            r, bound = Reg(2), False
            print(f"  A {READ[la][a]}. B {READ[lb][b]}. "
                  f"{'They agree.' if a == b else 'They disagree.'}")
            if a == b and was:
                streak += 1
                if streak >= 3:
                    return True
            elif a == b:
                print("  They agree, but they weren't bound, so it doesn't count.")
            else:
                print("  The lanterns disagreed, so your streak resets.")
                return False
        elif c[0] == "s":
            print("  Try: s z z   or   s x x   or   s z x")


def level4():
    note = ("Goal: get the boat across on all three crossings (route up to 5 steps).\n"
            "  m = Mirror   f = Fog bell   l = Look back   v = Rusted vane (does nothing)\n"
            "  c = clear   go = make three crossings")
    names = {"m": "Mirror", "f": "Fog bell", "l": "Look back", "v": "Rusted vane"}
    route = []
    print(note)
    while True:
        print("  Route: " + (" > ".join(names[s] for s in route) or "(empty)"))
        c = ask()
        if not c:
            continue
        if c[0] in names and len(route) < 5:
            route.append(c[0])
        elif c[0] == "c":
            route = []
        elif c[0] == "go":
            res = []
            for _ in range(3):
                q = Reg(1)
                for s in route:
                    if s == "m":
                        q.gate(0, H)
                    elif s == "f":
                        q.gate(0, Z)
                    elif s == "l":
                        q.look(0, "Z")
                res.append(q.look(0, "Z") == 1)
            print("  " + "  ".join("arrived" if v else "stayed" for v in res))
            if all(res):
                return True
            print("  At least one boat never reached the far shore.")
            return False


LEVELS = [("The Square of Statues", level1), ("Windows That Remember", level2),
          ("The Twin Lanterns", level3), ("The Mirror Crossing", level4)]


def main():
    if "--test" in sys.argv:
        res = selftest()
        for n, v in res:
            print(("PASS " if v else "FAIL ") + n)
        sys.exit(0 if all(v for _, v in res) else 1)

    print("\nTHE VILLAGE THAT LOOKS BACK")
    print("Your car died at the edge of the fog. The village ahead is empty, but its")
    print("figures freeze whenever you raise your camera. Take the picture.")
    print("Hope reality agrees.\n")
    for n, (title, fn) in enumerate(LEVELS, 1):
        san = 3
        while True:
            print(f"\n=== {n}. {title}   {hearts(san)} ===")
            if fn():
                print("  The way opens.")
                break
            san -= 1
            if san <= 0:
                print("\nThe village keeps you. The street rearranges itself around you.")
                print("You wake up and try again.")
                san = 3
    print("\nYou step off the island.")
    print("A photograph makes something settle on one answer. Which lens you choose")
    print("decides what you can be sure of.")


if __name__ == "__main__":
    main()
