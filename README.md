# hikari-miru
An optional component handler for [hikari](https://github.com/hikari-py/hikari), inspired by discord.py's views.

## Installation
```sh
pip install git+https://github.com/HyperGH/hikari-miru.git
```
## Usage
```py
import hikari
import miru


class MyView(miru.View):

    @miru.button(label="Rock", emoji=chr(129704), style=hikari.ButtonStyle.PRIMARY)
    async def rock_button(self, button: miru.Button, interaction: miru.Interaction):
        await interaction.send_message(content="Paper!")

    @miru.button(label="Paper", emoji=chr(128220), style=hikari.ButtonStyle.PRIMARY)
    async def paper_button(self, button: miru.Button, interaction: miru.Interaction):
        await interaction.send_message(content="Scissors!")

    @miru.button(label="Scissors", emoji=chr(9986), style=hikari.ButtonStyle.PRIMARY)
    async def scissors_button(self, button: miru.Button, interaction: miru.Interaction):
        await interaction.send_message(content="Rock!")

    @miru.button(emoji=chr(9209), style=hikari.ButtonStyle.DANGER, row=2)
    async def stop_button(self, button: miru.Button, interaction: miru.Interaction):
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
For general usage help or questions, see the `#hikari-miru` channel in the [hikari discord](https://discord.gg/Jx4cNGG), if you have found a bug or have a feature request, feel free to [open an issue](https://github.com/HyperGH/hikari-miru/issues/new)!

## Contributing
If you wish to contribute, be sure to first enable the formatting pre-commit hook via `git config core.hooksPath .githooks`, then make your changes.
