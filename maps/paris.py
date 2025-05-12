from collections import namedtuple


def exrypz(computer: str):
    if len(computer) >= 6 and "r" in computer and "s" in computer:
        res = {
            "building": "main",
            "p_sep": "s",
            "etage": computer.split("r")[0],
            "range": computer.split("r")[1].split("s")[0],
            "place": computer.split("s")[1],
        }
        return res
    return False


class RowPart:
    count: int
    is_pc: bool

    def __init__(self, count: int, is_pc: bool = True):
        self.count = count
        self.is_pc = is_pc


def create_row(cluster: str, row: str, row_parts: list[int | str]) -> list[str]:
    out = [row]
    r = 1
    for i, d in enumerate(row_parts):
        if isinstance(d, int):
            if d <= 0:
                out += ["" for _ in range(d)]
            else:
                out += [f"{cluster}{row}{r + p}" for p in range(d)]
        else:
            out.append(d)
    return out


# @formatter:off
# noqa: F401
# fmt: off
map = {
    "f6": [
        create_row("f6", "",    ["d", -7, -1, -7, "d"]),
        create_row("f6", "r1",  [     8,  -1, 8      ]),
        create_row("f6", "r2",  [     8,  -1, 8      ]),
        create_row("f6", "r3",  [     8,  -1, 8      ]),
        create_row("f6", "r4",  [     8,  -1, 8      ]),
        create_row("f6", "r5",  [     8,  -1, 8      ]),
        create_row("f6", "r6",  [     8,  -1, 8      ]),
        create_row("f6", "r7",  [     8,  -1, 8      ]),
        create_row("f6", "r8",  [     8,  -1, 8      ]),
        create_row("f6", "r9",  [     8,  -1, 8      ]),
        create_row("f6", "r10", [     8,  -1, 8      ]),
        create_row("f6", "r11", [     8,  -1, 8      ]),
        create_row("f6", "r12", [     8,  -1, 8      ]),
        create_row("f6", "r13", [     8,  -1, 8      ]),
        create_row("f6", "r14", [     8,  -1, 8      ]),
        create_row("f6", "",    ["d", -7, -1, -7, "d"]),
    ],
    "allowed": [
        "f1",
        "f1b",
        "f2",
        "f4",
        "f5",
        "f6",
    ],
    "buildings": {
        "main": [
            "F1",
            "F1B",
            "F2",
            "F4",
            "F5",
            "F6",
        ],
    },
    "kiosk_classes": {
        "<i class='fa-brands fa-apple'></i>": [],
        "<i class='fa-solid fa-display'></i>": [
            "F1",
            "F1B",
            "F2",
            "F4",
            "F5",
            "F6",
        ],
    },
    "piscine": [],
    "default": "f6",
    "exrypz": exrypz,
}

# @formatter:on
