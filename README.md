# hikari-miru

<div align="center">

[![PyPI](https://img.shields.io/pypi/v/hikari-miru)](https://pypi.org/project/hikari-miru)
[![CI](https://github.com/hypergonial/hikari-miru/actions/workflows/ci.yml/badge.svg)](https://github.com/hypergonial/hikari-miru/actions/workflows/ci.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
![Pyright](https://badgen.net/badge/Pyright/strict/2A6DB2)

</div>

A component handler for [hikari](https://github.com/hikari-py/hikari), aimed at making the creation & management of Discord UI components easy.

> [!TIP]
> Like what you see? Check out [arc](https://arc.hypergonial.com), a command handler with a focus on type-safety and correctness.

## Installation

To install miru, run the following command:

```sh
pip install -U hikari-miru
```

To check if miru has successfully installed or not, run the following:

```sh
python3 -m miru
# On Windows you may need to run:
py -m miru
```

## Usage

```py
import hikari
import miru

# REST bots are also supported
bot = hikari.GatewayBot(token="...")

# Wrap the bot in a miru client
client = miru.Client(bot)

class MyView(miru.View):

    @miru.button(label="Rock", emoji="\N{ROCK}", style=hikari.ButtonStyle.PRIMARY)
    async def rock_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("Paper!")

    @miru.button(label="Paper", emoji="\N{SCROLL}", style=hikari.ButtonStyle.PRIMARY)
    async def paper_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("Scissors!")

    @miru.button(label="Scissors", emoji="\N{BLACK SCISSORS}", style=hikari.ButtonStyle.PRIMARY)
    async def scissors_button(self, ctx: miru.ViewContext,  button: miru.Button) -> None:
        await ctx.respond("Rock!")

    @miru.button(emoji="\N{BLACK SQUARE FOR STOP}", style=hikari.ButtonStyle.DANGER, row=1)
    async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.stop() # Stop listening for interactions


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Ignore bots or webhooks pinging us
    if not event.is_human:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if me.id in event.message.user_mentions_ids:
        view = MyView()  # Create a new view
        # Send the view as message components
        await event.message.respond("Rock Paper Scissors!", components=view)
        client.start_view(view) # Attach to the client & start it

bot.run()
```

To get started with `miru`, see the [documentation](https://miru.hypergonial.com), or the [examples](https://github.com/hypergonial/hikari-miru/tree/main/examples).

## Extensions

miru has two extensions built-in:

- [`ext.nav`](https://miru.hypergonial.com/guides/navigators/) - To make it easier to build navigators (sometimes called paginators).
- [`ext.menu`](https://miru.hypergonial.com/guides/menus/) - To make it easier to create nested menus.

Check the corresponding documentation and the [examples](https://github.com/hypergonial/hikari-miru/tree/main/examples) on how to use them.

## Issues and support

For general usage help or questions, see the `#miru` channel in the [hikari discord](https://discord.gg/hikari), if you have found a bug or have a feature request, feel free to [open an issue](https://github.com/hypergonial/hikari-miru/issues/new)!

## Contributing

See [Contributing](./CONTRIBUTING.md)

## Links

- [**Documentation**](https://miru.hypergonial.com)
- [**Examples**](https://github.com/hypergonial/hikari-miru/tree/main/examples)
- [**License**](https://github.com/hypergonial/hikari-miru/blob/main/LICENSE)
