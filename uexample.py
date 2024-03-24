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
pool_index = u.AttrSpec(colors_256["green"], 'default', 256)
new_random =u.AttrSpec('bold', 'default', 256)

def main():

    pools = u.Text(
        [
            (pool_index, "0: "),
            ("normal", "0x00   \n"),
            (pool_index, "1: "),
            ("normal", "0x0102  <- 0,1\n"),
        ] * 16
    )
    seed_file = u.Text("0x" + "DEADCODE" * 16)
    output_history = u.Text(["FOCACCIA"*4, (new_random, "FEE1DEAD"*4 )])
    events = u.Text("Events") # list

    pile = u.Pile(
        u.LineBox(w, title=t)
        for w, t in [
            (seed_file, "seed file"),
            (output_history, "output history"),
            (events, "events"),
        ]
    )
    pile = u.Filler(pile, height=('relative', 100))

    columns = u.Columns(
           [
           u.LineBox(pools, title="pools"),
           pile
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
        elif data =='p':
            from time import sleep
            with StoppedScreen(loop.screen):
                print('hello friend')
                sleep(0.5)
                print('bye friend')
                sleep(0.5)
        return False

    loop = u.MainLoop(filler, unhandled_input = unhandled_input)

    loop.run()


if __name__ == "__main__":

    main()

