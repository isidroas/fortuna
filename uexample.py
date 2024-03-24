import urwid as u


palette = [
    ("body", "black", "light gray", "standout"),
    ("reverse", "light gray", "black"),
    ("header", "white", "dark red", "bold"),
    ("important", "dark blue", "light gray", ("standout", "underline")),
    ("editfc", "white", "dark blue", "bold"),
    ("editbx", "light gray", "dark blue"),
    ("editcp", "black", "light gray", "standout"),
    ("bright", "dark gray", "light gray", ("bold", "standout")),
    ("buttn", "black", "dark cyan"),
    ("buttnf", "white", "dark blue", "bold"),
]

colors_256 = {
    "black": "h0",
    "red": "h1",
    "green": "h2",
    "brown": "h3",
    "blue": "h4",
    "magenta": "h5",
    "cyan": "h6",
    "light gray": "h7",
    "dark gray": "h8",
    "bright red": "h9",
    "bright green": "h10",
    "bright brown": "h11",
    "bright blue": "h12",
    "bright magenta": "h13",
    "bright cyan": "h14",
    "white": "h15",
}

# green = u.AttrSpec(colors_256["white"], colors_256["green"], 256)
green = u.AttrSpec(colors_256["green"], 'default', 256)

def main():

    # TODO: put titles
    pools = u.Text(
        [
            (green, "0: "),
            ("normal", "0x00   \n"),
            (green, "1: "),
            ("normal", "0x0102  <- 0,1\n"),
        ]
    )
    seed_file = u.Text("0x" + "DEADCODE" * 16)
    output_history = u.Text("random output")
    events = u.Text("Events")

    columns = u.Columns(
        u.LineBox(w, title=t)
        for w, t in [
            (pools, "pools"),
            (seed_file, "seed file"),
            (output_history, "output history"),
            (events, "events"),
        ]
    )

    filler = u.Filler(columns, "top")

    PALETTE = [("normal", "black", "white"), ("selected", "black", "light cyan")]

    def unhandled_input(data: str | tuple[str, int, int, int]) -> bool | None:
        # print(data)
        if data == "q":
            raise u.ExitMainLoop()
        elif data == "t":
            seed_file.set_text("updated text")
            return True
        return False

    loop = u.MainLoop(filler, unhandled_input=unhandled_input)

    loop.run()


if __name__ == "__main__":

    main()
