"""3-bit carry-lookahead adder built ONLY from the five Part B gates
(INV, NAND2, NOR2, AND2, OR2).  Used by Part C.

Inputs : a0 a1 a2 b0 b1 b2 cin          Outputs : s0 s1 s2 cout
P_i = A_i xor B_i      G_i = A_i and B_i
C1 = G0 + P0.Cin
C2 = G1 + P1.G0 + P1.P0.Cin
C3 = G2 + P2.G1 + P2.P1.G0 + P2.P1.P0.Cin      (Cout = C3)
S_i = P_i xor C_i
XOR is built from 4 NAND2 gates.
"""
INPUTS = ["a0", "a1", "a2", "b0", "b1", "b2", "cin"]
OUTPUTS = ["s0", "s1", "s2", "cout"]
VECTORS = list(range(2 ** len(INPUTS)))          # 128 input vectors


def build_gates():
    """Return list of (name, type, [input nets], output net) in topological order."""
    gates = []

    def add(t, ins, out):
        gates.append((f"g{len(gates)}", t, list(ins), out))
        return out

    def xor(a, b, out):
        n1 = add("NAND2", [a, b], f"{out}_n1")
        n2 = add("NAND2", [a, n1], f"{out}_n2")
        n3 = add("NAND2", [b, n1], f"{out}_n3")
        return add("NAND2", [n2, n3], out)

    for i in range(3):
        xor(f"a{i}", f"b{i}", f"p{i}")
        add("AND2", [f"a{i}", f"b{i}"], f"g{i}n")
    G = [f"g{i}n" for i in range(3)]
    P = [f"p{i}" for i in range(3)]
    # C1
    t1 = add("AND2", [P[0], "cin"], "t1")
    c1 = add("OR2", [G[0], t1], "c1")
    # C2
    t2a = add("AND2", [P[1], G[0]], "t2a")
    pp10 = add("AND2", [P[1], P[0]], "pp10")
    t2c = add("AND2", [pp10, "cin"], "t2c")
    u = add("OR2", [G[1], t2a], "u")
    c2 = add("OR2", [u, t2c], "c2")
    # C3 = Cout
    t3a = add("AND2", [P[2], G[1]], "t3a")
    pp21 = add("AND2", [P[2], P[1]], "pp21")
    t3b = add("AND2", [pp21, G[0]], "t3b")
    pp210 = add("AND2", [P[2], pp10], "pp210")
    t3c = add("AND2", [pp210, "cin"], "t3c")
    v1 = add("OR2", [G[2], t3a], "v1")
    v2 = add("OR2", [v1, t3b], "v2")
    add("OR2", [v2, t3c], "cout")
    # sums
    xor(P[0], "cin", "s0")
    xor(P[1], c1, "s1")
    xor(P[2], c2, "s2")
    return gates


GATES = build_gates()


def logic_eval(vec):
    """vec: int 0..127, bit order [a0 a1 a2 b0 b1 b2 cin] = bit0..bit6.
    Returns dict net -> 0/1 for every net."""
    v = {n: (vec >> k) & 1 for k, n in enumerate(INPUTS)}
    for _, t, ins, out in GATES:
        x = [v[i] for i in ins]
        if t == "INV":
            v[out] = 1 - x[0]
        elif t == "NAND2":
            v[out] = 1 - (x[0] & x[1])
        elif t == "NOR2":
            v[out] = 1 - (x[0] | x[1])
        elif t == "AND2":
            v[out] = x[0] & x[1]
        elif t == "OR2":
            v[out] = x[0] | x[1]
    return v


def expected_sum(vec):
    a = (vec & 1) | ((vec >> 1) & 1) << 1 | ((vec >> 2) & 1) << 2
    b = ((vec >> 3) & 1) | ((vec >> 4) & 1) << 1 | ((vec >> 5) & 1) << 2
    cin = (vec >> 6) & 1
    return a + b + cin


def pattern(ins_vals):
    return "".join(str(x) for x in ins_vals)
