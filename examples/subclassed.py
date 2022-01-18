import hikari
import miru


class YesButton(miru.Button):
    def __init__(self) -> None:
        # Initialize our button with some pre-defined properties
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label="Yes")

    # The callback is the function that gets called when the button is pressed
    # If you are subclassing, you must use the name "callback" when defining it.
    async def callback(self, interaction: miru.Interaction) -> None:
        # You can specify the ephemeral message flag to make your response ephemeral
        await interaction.send_message("I'm sorry but this is unacceptable.", flags=hikari.MessageFlag.EPHEMERAL)
        # You can access the view an item is attached to by accessing it's view property
        self.view.answer = True
        self.view.stop()


class NoButton(miru.Button):
    def __init__(self) -> None:
        super().__init__(style=hikari.ButtonStyle.DANGER, label="No")

    async def callback(self, interaction: miru.Interaction) -> None:
        await interaction.send_message("This is the only correct answer.", flags=hikari.MessageFlag.EPHEMERAL)
        self.view.answer = False
        self.view.stop()


bot = hikari.GatewayBot("...")


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = miru.View(bot)  # Create a new view
        view.add_item(YesButton())  # Add our custom buttons to it
        view.add_item(NoButton())
        message = await event.message.respond("Do you put pineapple on your pizza?", components=view.build())

        view.start(message)  # Start listening for interactions

        await view.wait()  # Wait until the view is stopped or times out

        if hasattr(view, "answer"):  # Check if there is an answer
            print(f"Received an answer! It is: {view.answer}")
        else:
            print("Did not receive an answer in time!")


bot.run()
