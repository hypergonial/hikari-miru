import hikari
import miru
from miru.ext import menu
from miru import GW

# The `menu` extension is designed to make creating complex nested menus easy via Discord components.
#
# - The `Menu` class stores a stack of `Screen` instances, which are used to display components.
# - The `Screen` is essentially just a container for a `ScreenContent` and a list of `ScreenItem`s.
# - The `ScreenContent` is used to store the message payload (content, embeds etc.) of the screen.


class MainScreen(menu.Screen[GW]):
    # This method must be overridden in your screen classes
    # This is where you would fetch data from a database, etc. to display on your screen
    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(
            embed=hikari.Embed(
                title="Welcome to the Miru Menu example!",
                description="This is an example of the Miru Menu extension.",
                color=0x00FF00,
            ),
        )

    # Note: You should always use @menu decorators inside Screen subclasses, NOT @miru
    @menu.button(label="Moderation")
    async def moderation(self, button: menu.ScreenButton[GW], ctx: miru.ViewContext[GW]) -> None:
        # Add a new screen to the menu stack, the message is updated automatically
        await self.menu.push(ModerationScreen(self.menu))

    @menu.button(label="Logging")
    async def logging(self, button: menu.ScreenButton[GW], ctx: miru.ViewContext[GW]) -> None:
        await self.menu.push(LoggingScreen(self.menu))

class ModerationScreen(menu.Screen[GW]):
    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(
            embed=hikari.Embed(
                title="Moderation",
                description="This is the moderation screen!",
                color=0x00FF00,
            ),
        )

    @menu.button(label="Back")
    async def back(self, button: menu.ScreenButton[GW], ctx: miru.ViewContext[GW]) -> None:
        # Remove the current screen from the menu stack,
        # effectively going back to the previous screen
        await self.menu.pop()

    @menu.button(label="Ban", style=hikari.ButtonStyle.DANGER)
    async def ban(self, button: menu.ScreenButton[GW], ctx: miru.ViewContext[GW]) -> None:
        await ctx.respond("Hammer time!")

    @menu.button(label="Kick", style=hikari.ButtonStyle.SECONDARY)
    async def kick(self, button: menu.ScreenButton[GW], ctx: miru.ViewContext[GW]) -> None:
        await ctx.respond("Kick!")

class LoggingScreen(menu.Screen[GW]):
    def __init__(self, menu: menu.Menu[GW]) -> None:
        super().__init__(menu)
        # Your screens can store state in the class instance
        # But keep in mind that the instance will be
        # destroyed once the screen is popped off the stack
        self.is_enabled = False

    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(
            embed=hikari.Embed(
                title="Logging",
                description="This is the logging screen!",
                color=0x00FF00,
            ),
        )


    @menu.button(label="Back")
    async def back(self, button: menu.ScreenButton[GW], ctx: miru.ViewContext[GW]) -> None:
        await self.menu.pop()

    @menu.button(label="Enable", style=hikari.ButtonStyle.DANGER)
    async def enable(self, button: menu.ScreenButton[GW], ctx: miru.ViewContext[GW]) -> None:
        self.is_enabled = not self.is_enabled
        button.style = hikari.ButtonStyle.SUCCESS if self.is_enabled else hikari.ButtonStyle.DANGER
        button.label = "Disable" if self.is_enabled else "Enable"
        # Update the message the menu is attached to with the new state of components.
        await self.menu.update_message()

bot = hikari.GatewayBot("...")
client = miru.GatewayClient(bot)


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or webhooks
    if not event.is_human:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if me.id in event.message.user_mentions_ids:
        my_menu = menu.Menu[GW]()  # Create a new Menu
        builder = await my_menu.build_response_async(client, MainScreen(my_menu))
        await builder.send_to_channel(event.channel_id)
        client.start_view(my_menu)
        # Note: You can also send the menu to an interaction or miru context
        # See the documentation of Menu.send() for more information


bot.run()
