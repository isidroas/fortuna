import urwid as u


# using high colors file:///home/isidro/op/urwid/build/documentation/manual/displayattributes.html#bright-background-colors instead of bright I don't remember why
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
pool_index = u.AttrSpec(colors_256["green"], "default", 256)
new_random = u.AttrSpec("bold", "default", 256)
old_random = u.AttrSpec(colors_256['light gray'], "default", 256)

def create_top(pools: u.Text, seed_file: u.Text, output_history: u.Text, events: u.SimpleListWalker, help: u.Text):
    pile = u.Pile(
        [
            u.Columns(
                [
                    u.LineBox(u.Filler(seed_file, 'top'), title="seed file"),
                    u.LineBox(u.Filler(output_history, 'bottom'), title="output history"),
                ]
            ),
            u.Columns(
                [
                    u.LineBox(events, title="events"),
                    u.LineBox(u.Filler(help, 'bottom'), title="help"),

                ]
            ),
        ]
    )

    top = u.Columns([u.LineBox(u.Filler(pools), title="pools"), pile])
    return top

def add_output_history(output_history: u.Text, data: bytes):
    # TODO: u.Text no se puede modificar, ni u.Edit. Usar también ListBox?
    output_history[-1] = (old_random, output_history[-1][1])
    output_history.append((new_random, data.hex().upper()))

def main():

    pools = u.Text(
        [
            (pool_index, "0: "),
            ("normal", "0x00   \n"),
            (pool_index, "1: "),
            ("normal", "0x0102  <- 0,1\n"),
        ]
        * 16
    )
    seed_file = u.Text("0x" + "DEADCODE" * 16)
    output_history = u.Text([(old_random, "FOCACCIA" * 4), (new_random, "FEE1DEAD" * 4)])

    # events = u.SimpleListWalker([])
    events = u.ListBox(u.SimpleListWalker(u.Text(t) for t in [
        "Pressed 'k'",
        "Pressed 'j'",
        "timestamp: 16:59:30.671210",
        "timestamp: 16:59:30.952142",
        "not writing seed file",
        "found empty tmp/seed_file file",
    ]))

    help = u.Text(
        [
            "c: Add entropy from keystrokes char\n",
            "t: Add entropy from keystrokes timestamp\n",
            "f: Update seed file\n",
            "r: generate random\n",
            "b: edit number of blocks\n",
        ]
    )


    def unhandled_input(data: str | tuple[str, int, int, int]) -> bool | None:
        # print(data)
        if data == "q":
            raise u.ExitMainLoop()
        elif data == "t":
            seed_file.set_text("updated text")
            return True
        elif data == "e":
            # source: pudb.debugger.add_cmdline_content
            events.body.append(u.Text('alarmmm!'))
            # esto es necesario porque si no se queda el focus arriba
            events.set_focus_valign("bottom")
            events.set_focus(len(events) - 1, coming_from="above")
        elif data == "r":
            add_output_history(output_history, b'\xde\xca\xfb\xad')

        return False

    loop = u.MainLoop(create_top(pools, seed_file, output_history, events, help) , unhandled_input=unhandled_input)
    loop.run()


if __name__ == "__main__":

    main()
