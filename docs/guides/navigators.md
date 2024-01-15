---
title: Navigators
description: Learn how to use navigators, and paginate content using buttons.
hide:
  - toc
search:
  exclude: true
---

# Navigators


A common usecase for buttons is creating paginated button-menus. In miru, these are called
navigators, and such functionality is provided by the extension `miru.ext.nav`.

!!! note
    `miru.ext.nav` is included with your installation, but is not imported implicitly,
    thus you have to explicitly import the module.

The base of any navigator is the [`NavigatorView`][miru.ext.nav.navigator.NavigatorView], a specialized view
designed for creating navigators. To get started, it's as easy as creating a new instance of it,
turning it into a builder, and sending it to a channel or interaction.

The examples below are for a **Gateway** bot, but a **REST** bot would behave similarly in command handlers that support it:

=== "arc"

    ```py
    import arc
    import hikari
    import miru
    # Import the navigation module
    from miru.ext import nav

    bot = hikari.GatewayBot("TOKEN")

    client = miru.Client(bot)
    arc_client = arc.GatewayClient(bot)

    @arc_client.include
    @arc.slash_command("name", "description")
    async def my_command(ctx: arc.GatewayContext) -> None:
        embed = hikari.Embed(
            title="I'm the second page!",
            description="Also an embed!"
        )
        # A Page object can be used to further customize the page payload
        page = nav.Page(
            content="I'm the last page!",
            embed=hikari.Embed(title="I also have an embed!")
        )

        # The list of pages this navigator should paginate through
        # This should be a list that contains
        # 'str', 'hikari.Embed', or 'nav.Page' objects.
        pages = ["I'm the first page!", embed, page]

        # Define our navigator and pass in our list of pages
        navigator = nav.NavigatorView(pages=pages)

        builder = nav.build_response(client)
        await ctx.respond_with_builder(builder)
        client.start_view(nav)


    bot.run()
    ```

=== "crescent"

    Crescent is not yet supported.

=== "lightbulb"

    ```py
    import hikari
    import lightbulb
    import miru
    # Import the navigation module
    from miru.ext import nav

    bot = lightbulb.BotApp("TOKEN")

    client = miru.Client(bot)

    @bot.command
    @lightbulb.command("name", "description", auto_defer=False)
    @lightbulb.implements(lightbulb.SlashCommand)
    async def my_command(ctx: lightbulb.SlashContext) -> None:
        embed = hikari.Embed(
            title="I'm the second page!",
            description="Also an embed!"
        )
        # A Page object can be used to further customize the page payload
        page = nav.Page(
            content="I'm the last page!",
            embed=hikari.Embed(title="I also have an embed!")
        )

        # The list of pages this navigator should paginate through
        # This should be a list that contains
        # 'str', 'hikari.Embed', or 'nav.Page' objects.
        pages = ["I'm the first page!", embed, page]

        # Define our navigator and pass in our list of pages
        navigator = nav.NavigatorView(pages=pages)

        builder = nav.build_response(client)
        await builder.create_initial_response(ctx.interaction)
        # Or in a prefix command:
        # await builder.send_to_channel(ctx.channel_id)

        client.start_view(nav)


    bot.run()
    ```

=== "tanjun"

    ```py
    import hikari
    import miru
    import tanjun

    from miru.ext import nav

    bot = hikari.GatewayBot("TOKEN")

    tanjun_client = tanjun.Client.from_gateway_bot(bot)
    client = miru.Client(bot)

    @tanjun.as_slash_command("name", "description")
    async def some_slash_command(ctx: tanjun.abc.SlashContext) -> None:
        embed = hikari.Embed(
            title="I'm the second page!",
            description="Also an embed!"
        )
        # A Page object can be used to further customize the page payload
        page = nav.Page(
            content="I'm the last page!",
            embed=hikari.Embed(title="I also have an embed!")
        )

        # The list of pages this navigator should paginate through
        # This should be a list that contains
        # 'str', 'hikari.Embed', or 'nav.Page' objects.
        pages = ["I'm the first page!", embed, page]

        # Define our navigator and pass in our list of pages
        navigator = nav.NavigatorView(pages=pages)

        builder = nav.build_response(client)
        # the builder has specific adapters for tanjun
        await ctx.respond(**builder.to_tanjun_kwargs())
        client.start_view(nav)


    bot.run()
    ```

=== "just hikari"

    ```py
    import hikari
    import miru
    # Import the navigation module
    from miru.ext import nav

    bot = hikari.GatewayBot("...")

    client = miru.Client(bot)

    @bot.listen()
    async def navigator(event: hikari.MessageCreateEvent) -> None:

        # Do not process messages from bots or webhooks
        if not event.is_human:
            return

        me = bot.get_me()

        # If the bot is mentioned
        if me.id in event.message.user_mentions_ids:
            embed = hikari.Embed(
                title="I'm the second page!",
                description="Also an embed!"
            )

            # A Page object can be used to further customize the page payload
            page = nav.Page(
                content="I'm the last page!",
                embed=hikari.Embed(title="I also have an embed!")
            )

            # The list of pages this navigator should paginate through
            # This should be a list that contains
            # 'str', 'hikari.Embed', or 'nav.Page' objects.
            pages = ["I'm the first page!", embed, page]

            # Define our navigator and pass in our list of pages
            navigator = nav.NavigatorView(pages=pages)

            builder = nav.build_response(client)
            await builder.send_to_channel(event.channel_id)
            client.start_view(nav)


    bot.run()
    ```

## Customizing Navigation Buttons

If you would like to customize the buttons used by the navigator, you can pass buttons via the `buttons=` keyword-only
argument. This should be a list of [`NavButton`][miru.ext.nav.items.NavButton].

There are also some built-in navigation buttons, these are:

- [`FirstButton`][miru.ext.nav.items.FirstButton] - Jump to first page
- [`PrevButton`][miru.ext.nav.items.PrevButton] - Jump to previous page
- [`NextButton`][miru.ext.nav.items.NextButton] - Jump to next page
- [`LastButton`][miru.ext.nav.items.LastButton] - Jump to last page
- [`StopButton`][miru.ext.nav.items.StopButton] - Stop the navigation session
- [`IndicatorButton`][miru.ext.nav.items.IndicatorButton] - Show the current page and max pages

You may use any mix of the built-in and custom navigation buttons in your navigator views.

Let's define a custom navigation button:

```py
class MyIndicatorButton(nav.NavButton):
    def __init__(self):
        super().__init__(label="Page: 1", row=1)

    async def callback(self, ctx: miru.ViewContext) -> None:
        await ctx.respond("You clicked me!", flags=hikari.MessageFlag.EPHEMERAL)

    async def before_page_change(self) -> None:
        # This function is called before the new page is sent by the navigator
        self.label = f"Page: {self.view.current_page+1}"
```

Then we can add it to our Navigator before sending:

```py
embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
pages = ["I'm a customized navigator!", embed, "I'm the last page!"]

# Define our custom buttons for this navigator, keep in mind the order
# All navigator buttons MUST subclass nav.NavButton
buttons = [
    nav.PrevButton(),
    nav.StopButton(),
    nav.NextButton(),
    MyNavButton()
]

# Pass our list of NavButton to the navigator
navigator = nav.NavigatorView(pages=pages, buttons=buttons)

# ... Send the navigator
```
