import hikari
import miru


class BasicView(miru.View):

    # Define a new Select menu with two options
    @miru.select(
        placeholder="Select me!", options=[miru.SelectOption(label="Option 1"), miru.SelectOption(label="Option 2")]
    )
    async def basic_select(self, select: miru.Select, interaction: miru.Interaction) -> None:
        await interaction.send_message(f"You've chosen {select.values[0]}!")

    # Define a new Button with the Style of success (Green)
    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, button: miru.Button, interaction: miru.Interaction) -> None:
        await interaction.send_message(f"You clicked me!")

    # Define a new Button that when pressed will stop the view & invalidate all the buttons in this view
    @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
    async def stop_button(self, button: miru.Button, interaction: miru.Interaction) -> None:
        self.stop()  # Called to stop the view


bot = hikari.GatewayBot("...")


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = BasicView(bot)  # Create an instance of our newly created BasicView
        # Build the components defined in the view and attach them to our message
        # View.build() returns a list of the built action-rows, ready to be sent in a message
        message = await event.message.respond(
            "This is a basic component menu built with miru!", components=view.build()
        )

        view.start(message)  # Start listening for interactions

        await view.wait()  # Wait until the view is stopped or times out

        print("View stopped or timed out!")


bot.run()
