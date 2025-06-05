---
title: Menus
description: Learn how to create nested menus using miru and navigate between different screens.
hide:
  - toc
search:
  exclude: true
---

# Menus

One great use for Discord UI components is to create nested menus. `miru.ext.menu` aims to make this easier
to handle and provides useful abstractions.

!!! note
    `miru.ext.menu` is included with your installation, but is not imported implicitly,
    thus you have to explicitly import the module.

## Screens

The foundation of a menu in `ext.menu` is a [`Screen`][miru.ext.menu.screen.Screen]. It behaves similarly to a [`View`][miru.view.View],
in that you can add items such as buttons and select menus to it, however it is not a direct subclass of `View`. Instead, a collection of
screens forms a [`Menu`][miru.ext.menu.menu.Menu], which manages the screens and the navigation between them.

Let's create a couple screens, so that later on we can create a menu out of them, and navigate between them:



```py
import hikari
import miru
# Import the menu extension
from miru.ext import menu


class MainScreen(menu.Screen):
    # This method must be overridden in your screen classes
    # This is where you would fetch data from
    # a database, etc. to display on your screen
    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(
            embed=hikari.Embed(
                title="Welcome to the Miru Menu example!",
                description="This is an example of the Miru Menu extension.",
                color=0x00FF00,
            ),
        )

    # Note: You should always use @menu decorators
    # inside Screen subclasses, NOT @miru
    @menu.button(label="Moderation")
    async def moderation(self, ctx: miru.ViewContext, button: menu.ScreenButton) -> None:
        # Add a new screen to the menu stack,
        # the message is updated automatically
        await self.menu.push(ModerationScreen(self.menu))

    @menu.button(label="Logging")
    async def fun(self, ctx: miru.ViewContext, button: menu.ScreenButton) -> None:
        await self.menu.push(LoggingScreen(self.menu))


class ModerationScreen(menu.Screen):
    async def build_content(self) -> menu.ScreenContent:
        return menu.ScreenContent(
            embed=hikari.Embed(
                title="Moderation",
                description="This is the moderation screen!",
                color=0x00FF00,
            ),
        )

    @menu.button(label="Back")
    async def back(self, ctx: miru.ViewContext, button: menu.ScreenButton) -> None:
        # Remove the current screen from the menu stack,
        # effectively going back to the previous screen
        await self.menu.pop()

    @menu.button(label="Ban", style=hikari.ButtonStyle.DANGER)
    async def ban(self, ctx: miru.ViewContext, button: menu.ScreenButton) -> None:
        await ctx.respond("Hammer time!")

    @menu.button(label="Kick", style=hikari.ButtonStyle.SECONDARY)
    async def kick(self, ctx: miru.ViewContext, button: menu.ScreenButton) -> None:
        await ctx.respond("Kick!")


class LoggingScreen(menu.Screen):
    def __init__(self, menu: menu.Menu) -> None:
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
    async def back(self, ctx: miru.ViewContext, button: menu.ScreenButton) -> None:
        await self.menu.pop()

    @menu.button(label="Enable", style=hikari.ButtonStyle.DANGER)
    async def enable(self, ctx: miru.ViewContext, button: menu.ScreenButton) -> None:
        self.is_enabled = not self.is_enabled

        if self.is_enabled:
            button.style = hikari.ButtonStyle.SUCCESS
            button.label = "Disable"
        else:
            button.style = hikari.ButtonStyle.DANGER
            button.label = "Enable"
        # Update the message the menu is attached to
        # with the new state of components.
        await self.menu.update_message()
```

Here, we defined 3 screens. The `MainScreen`, our entrypoint, allows us to navigate to the other two
screens, `ModerationScreen` and `LoggingScreen`, and the latter two screens allow us to go back,
returning to `MainScreen`. You may also create more complex, nested navigation, this is just a simple example.

!!! note
    You should always use `ScreenItem` inside `Screen`, such as `ScreenButton` instead of `Button`.

    The `@menu` decorators create `ScreenItem`s, but you can also create them via subclassing and then calling
    `Screen.add_item()`, similarly to how it is showcased in the [Subclassing](../getting_started.md#subclassing) section of this guide.

## Menu

The `Menu` ties all the screens together and navigates between them. If you `push` or `pop` a screen from the `Menu`,
it will automatically update it's message and build the corresponding screen's content for you.

To set up a menu for the screens we designed above, see this snippet below:

=== "just hikari"

    === "Gateway"

        ```py
        @bot.listen()
        async def buttons(event: hikari.MessageCreateEvent) -> None:
            # Do not process messages from bots or webhooks
            if not event.is_human:
                return

            me = bot.get_me()

            # If the bot is mentioned
            if me.id in event.message.user_mentions_ids:
                my_menu = menu.Menu()  # Create a new Menu

                # Pass in the initial screen
                builder = await my_menu.build_response_async(client, MainScreen(my_menu))

                await builder.send_to_channel(event.channel_id)

                client.start_view(my_menu)
        ```

    === "REST"

        ```py
        # Let's assume this is a RESTBot's CommandInteraction callback
        async def handle_command(interaction: hikari.CommandInteraction):
            my_menu = menu.Menu()  # Create a new Menu

            # Pass in the initial screen
            builder = await my_menu.build_response_async(client, MainScreen(my_menu))

            # The builder is a valid REST response builder
            yield builder

            # Assign the view to the client and start it
            client.start_view(my_menu)s
        ```

=== "arc"

    === "Gateway"

        ```py
        @arc_client.include
        @arc.slash_command("name", "description")
        async def some_slash_command(ctx: arc.GatewayContext) -> None:
            my_menu = menu.Menu()  # Create a new Menu
            # Pass in the initial screen
            builder = await my_menu.build_response_async(client, MainScreen(my_menu))
            await ctx.respond_with_builder(builder)
            client.start_view(my_menu)
        ```

    === "REST"

        ```py
        @arc_client.include
        @arc.slash_command("name", "description")
        async def some_slash_command(ctx: arc.RESTContext) -> None:
            my_menu = menu.Menu()  # Create a new Menu
            # Pass in the initial screen
            builder = await my_menu.build_response_async(client, MainScreen(my_menu))
            await ctx.respond_with_builder(builder)
            client.start_view(my_menu)
        ```

=== "crescent"

    ```py
    @crescent_client.include
    @crescent.command(name="name", description="description")
    class SomeSlashCommand:
        async def callback(self, ctx: crescent.Context) -> None:
            # Create a new instance of our view
            view = BasicView()
            builder = await my_menu.build_response_async(client, MainScreen(my_menu))
            await ctx.respond_with_builder(builder)
            client.start_view(my_menu)
    ```

=== "lightbulb"

    ```py
    @lightbulb_bot.command()
    @lightbulb.command("name", "description", auto_defer=False)
    @lightbulb.implements(lightbulb.SlashCommand)
    async def some_slash_command(ctx: lightbulb.SlashContext) -> None:
        my_menu = menu.Menu()  # Create a new Menu
        # You may need to defer if building your first page takes more than 3 seconds
        builder = await my_menu.build_response_async(client, MainScreen(my_menu))
        await builder.create_initial_response(ctx.interaction)
        # Or if using a prefix command:
        # await builder.send_to_channel(ctx.channel_id)

        client.start_view(my_menu)
    ```

=== "tanjun"

    ```py
    @tanjun.as_slash_command("name", "description")
    async def some_slash_command(ctx: tanjun.abc.SlashContext) -> None:
        my_menu = menu.Menu()  # Create a new Menu
        # Pass in the initial screen
        builder = await my_menu.build_response_async(client, MainScreen(my_menu))
        await ctx.respond_with_builder(builder)
        client.start_view(my_menu)
    ```

!!! tip
    If you want to send a menu in response to a `miru` item being interacted with, you may use [`Context.respond_with_builder()`][miru.abc.context.Context.respond_with_builder].

!!! note
    Menus do not support persistence.
