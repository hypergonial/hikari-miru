# hikari-miru
An optional component handler for [hikari](https://github.com/hikari-py/hikari), inspired by discord.py's views.

## Installation
```sh
pip install git+https://github.com/HyperGH/hikari-miru.git
```
## Usage
```py
import hikari
import hikari_miru as miru


class MyView(miru.View):

    @miru.button(label="Rock", emoji="🪨", style=hikari.ButtonStyle.PRIMARY)
    async def rock_button(self, button: miru.Button, interaction: hikari.ComponentInteraction):
        await interaction.create_initial_response(hikari.ResponseType.MESSAGE_CREATE, content=f"Paper!")

    @miru.button(label="Paper", emoji="📜", style=hikari.ButtonStyle.PRIMARY)
    async def paper_button(self, button: miru.Button, interaction: hikari.ComponentInteraction):
        await interaction.create_initial_response(hikari.ResponseType.MESSAGE_CREATE, content=f"Scissors!")

    @miru.button(label="Scissors", emoji="✂️", style=hikari.ButtonStyle.PRIMARY)
    async def scissors_button(self, button: miru.Button, interaction: hikari.ComponentInteraction):
        await interaction.create_initial_response(hikari.ResponseType.MESSAGE_CREATE, content=f"Rock!")

    @miru.button(emoji="⏹️", style=hikari.ButtonStyle.DANGER, row=2)
    async def stop_button(self, button: miru.Button, interaction: hikari.ComponentInteraction):
        await interaction.create_initial_response(hikari.ResponseType.DEFERRED_MESSAGE_UPDATE)
        self.stop() # Stop listening for interactions


bot = hikari.GatewayBot(token="...")


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    if event.is_bot or not event.content:
        return

    if event.content.startswith("hm.buttons"):
        view = MyView(bot, timeout=60)  # Create a new view
        message = await event.message.respond("Rock Paper Scissors!", components=view.build())
        view.start(message)  # Start listening for interactions
        await view.wait() # Wait until the view times out or gets stopped
        await event.message.respond("Thank you for playing!")

bot.run()
```
## Issues and support
For general usage help or questions, ping `Hyper#0001` in the [hikari discord](https://discord.gg/Jx4cNGG), if you have found a bug or have a feature request, feel free to [open an issue](https://github.com/HyperGH/hikari-miru/issues/new)!

## Contributing
If you wish to contribute, be sure to first enable the formatting pre-commit hook via `git config core.hooksPath .githooks`, then make your changes.
