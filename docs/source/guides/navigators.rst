Navigators
==========

A common usecase for buttons is creating paginated button-menus. In miru, these are called
navigators, and such functionality is provided by the extension ``miru.ext.nav``.

.. note::
    ``miru.ext.nav`` is included with your installation, but is not imported implicitly,
    thus you have to explicitly import the module.

The base of any navigator is the :obj:`miru.ext.nav.navigator.NavigatorView`, a specialized view
designed for creating navigators. To get started, it's as easy as creating a new instance of it,
and using the ``send()`` method to send the navigator to a channel, or as a response to an interaction.

::

    import hikari
    import miru
    # Import the navigation module
    from miru.ext import nav

    bot = hikari.GatewayBot("...")
    miru.install(bot)


    @bot.listen()
    async def navigator(event: hikari.GuildMessageCreateEvent) -> None:

        # Do not process messages from bots or webhooks
        if not event.is_human:
            return

        me = bot.get_me()

        # If the bot is mentioned
        if me.id in event.message.user_mentions_ids:
            embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
            # The list of pages this navigator should paginate through
            pages = ["I'm the first page!", embed, "I'm the last page!"]
            # Define our navigator and pass in our list of pages
            navigator = nav.NavigatorView(pages=pages)
            # You may also pass an interaction object to this function
            await navigator.send(event.channel_id)


    bot.run()

Customizing Navigation Buttons
------------------------------

If you would like to customize the buttons used by the navigator, you can pass buttons via the ``buttons=`` keyword-only
argument. This should be a list of :obj:`miru.ext.nav.buttons.NavButton`.

There are also some built-in navigation buttons, these are:

- :obj:`miru.ext.nav.buttons.FirstButton` - Jump to first page
- :obj:`miru.ext.nav.buttons.PrevButton` - Jump to previous page
- :obj:`miru.ext.nav.buttons.NextButton` - Jump to next page
- :obj:`miru.ext.nav.buttons.LastButton` - Jump to last page
- :obj:`miru.ext.nav.buttons.StopButton` - Stop the navigation session
- :obj:`miru.ext.nav.buttons.IndicatorButton` - Show the current page and max pages

You may use any mix of the built-in and custom navigation buttons in your navigator views.

::

    import hikari
    import miru
    from miru.ext import nav


    class MyNavButton(nav.NavButton):
        def __init__(self):
            super().__init__(label="Page: 1", row=1)

        async def callback(self, ctx: miru.ViewContext) -> None:
            await ctx.respond("You clicked me!", flags=hikari.MessageFlag.EPHEMERAL)

        async def before_page_change(self) -> None:
            # This function is called before the new page is sent by
            # NavigatorView.send_page()
            self.label = f"Page: {self.view.current_page+1}"


    bot = hikari.GatewayBot("...")
    miru.install(bot)


    @bot.listen()
    async def navigator(event: hikari.GuildMessageCreateEvent) -> None:

        if not event.is_human:
            return

        me = bot.get_me()

        if me.id in event.message.user_mentions_ids:
            embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
            pages = ["I'm a customized navigator!", embed, "I'm the last page!"]
            # Define our custom buttons for this navigator, keep in mind the order
            # All navigator buttons MUST subclass nav.NavButton
            buttons = [nav.PrevButton(), nav.StopButton(), nav.NextButton(), MyNavButton()]
            # Pass our list of NavButton to the navigator
            navigator = nav.NavigatorView(pages=pages, buttons=buttons)

            await navigator.send(event.channel_id)


    bot.run()