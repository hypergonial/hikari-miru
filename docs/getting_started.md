---
title: Getting started
description: Getting started with miru
hide:
  - navigation
  - toc
search:
  exclude: true
---

# Getting Started

This guide assumes that you already have a basic bot with [`hikari`](https://github.com/hikari-py/hikari) (and perharps a command handler of your choice) set up and running. It **does not** cover how to create a bot from scratch.

??? tip "Help! I don't have a bot yet!"
    If you're completely new to making Discord bots, and haven't started coding yet, you can check out [`arc`](https://arc.hypergonial.com/) and its [getting started](https://arc.hypergonial.com/getting_started/) guide. It covers the basics of how to create a Discord bot using it and `hikari` from scratch, and provides a good starting point for adding components to your bot.

## Installation

`miru` can be installed using pip via the following command:

```sh
pip install hikari-miru
```

!!! note
    Please note that `miru` requires a Python version of **at least 3.10**.

To make sure `miru` installed correctly, run the following command:

=== "Windows"

    ```sh
    py -m miru
    ```
=== "macOS, Linux"

    ```sh
    python3 -m miru
    ```

It should print basic information about the library to the console.

## First steps

This is what a basic component menu looks like with miru:

```py
import hikari
import miru

# Define a new custom View that contains 3 items
class BasicView(miru.View):

    # Define a new TextSelect menu with two options
    @miru.text_select(
        placeholder="Select me!",
        options=[
            miru.SelectOption(label="Option 1"),
            miru.SelectOption(label="Option 2"),
        ],
    )
    async def basic_select(self, ctx: miru.ViewContext, select: miru.TextSelect) -> None:
        await ctx.respond(f"You've chosen {select.values[0]}!")

    # Define a new Button with the Style of success (Green)
    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("You clicked me!")

    # Define a new Button that when pressed will stop the view
    # & invalidate all the buttons in this view
    @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
    async def stop_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        self.stop()  # Called to stop the view
```

!!! note "A note on usage with command handlers"
    `miru` has support for the following command handlers:

    - [`arc`](https://arc.hypergonial.com/)
    - [`crescent`](https://github.com/hikari-crescent/hikari-crescent)
    - [`lightbulb`](https://hikari-lightbulb.readthedocs.io/en/latest/)
    - [`tanjun`](https://tanjun.cursed.solutions/)

    It can also be used **without a command handler**, if preferred. Other command handlers may work, but there was no consideration made to support them.

??? question "What is a command handler?"
    Command handlers typically extend `hikari` with additional functionality to make it easier to define and manage commands. They also usually ship with a plethora of utility functions to make bot creation easier. Their use is **not necessary**, but is *recommended* for newcomers. If you need help picking a command handler for your bot, see [this repository](https://github.com/parafoxia/hikari-intro) for a comparison.

To proceed, you can instantiate your bot class, and create a miru [Client][miru.client.Client] from it:

=== "just hikari"

    === "Gateway"

        ```py
        bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
        client = miru.Client(bot)
        ```

    === "REST"

        ```py
        bot = hikari.RESTBot("YOUR_TOKEN_HERE")
        client = miru.Client(bot)
        ```

=== "arc"

    `miru` has specific support for `arc` clients, and can share registered type dependencies set by it for injection:

    === "Gateway"

        ```py
        bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
        arc_client = arc.GatewayClient(bot)
        client = miru.Client.from_arc(arc_client)
        ```

    === "REST"

        ```py
        bot = hikari.RESTBot("YOUR_TOKEN_HERE")
        arc_client = arc.RESTClient(bot)
        client = miru.Client.from_arc(arc_client)
        ```

=== "crescent"

    === "Gateway"

        ```py
        bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
        crescent_client = crescent.Client(bot)
        client = miru.Client(bot)
        ```

    === "REST"

        ```py
        bot = hikari.RESTBot("YOUR_TOKEN_HERE")
        crescent_client = crescent.Client(bot)
        client = miru.Client(bot)
        ```

=== "lightbulb"

    ```py
    bot = lightbulb.BotApp("YOUR_TOKEN_HERE")
    client = miru.Client(bot)
    ```

    !!! note
        `lightbulb` only supports Gateway bots.

=== "tanjun"

    `miru` has specific support for **Tanjun** clients, and can share registered type dependencies set by it for injection:

    === "Gateway"

        ```py
        bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
        tanjun_client = tanjun.Client.from_gateway_bot(...)
        client = miru.Client.from_tanjun(tanjun_client)
        ```

    === "REST"

        ```py
        bot = hikari.RESTBot("YOUR_TOKEN_HERE")
        tanjun_client = tanjun.Client.from_rest_bot(...)
        client = miru.Client.from_tanjun(tanjun_client)
        ```


??? question "What is the difference between a Gateway and a REST bot?"

    There are two main ways for a bot to connect to Discord & receive interactions, via either a **GatewayBot** or a **RESTBot**.

    A bot connected to the [**Gateway**](https://discord.com/developers/docs/topics/gateway "Discord's fancy way of saying WebSocket") needs to maintain a constant connection to Discord's servers through a [WebSocket](https://en.wikipedia.org/wiki/WebSocket "A way of establishing realtime two-way communication between client & server"),
    and in turn receives **events** that inform it about things happening on Discord in real time (messages being sent, channels being created etc...).
    **Interactions** are also delivered to a bot of this type through the Gateway as events. In addition, Gateway bots typically have a [*cache*][miru.client.Client.cache] and can manage complex state.
    This model is ideal for bots that need to do things other than just responding to interactions, such as reading and responding to messages sent by users, or acting on other server events (e.g. a moderation bot).

    A **RESTBot** however, isn't constantly connected to Discord, instead, you're expected to host a small HTTP server, and Discord will send **interactions** to your server
    by making HTTP `POST` requests to it. RESTBots **only receive interactions** from Discord, they **do not receive events** or other types of data. They are ideal for bots that manage little to no state,
    and rely only on users invoking the bot via slash commands. Setting up a RESTBot however is slightly more complicated compared to a GatewayBot, as it requires a publically accessible [domain](https://en.wikipedia.org/wiki/Domain_name "A domain name, like 'www.example.com'") with [TLS](https://en.wikipedia.org/wiki/Transport_Layer_Security "Transport Layer Security (site with https://)") for Discord to be able to send interactions to your webserver.

    For more information about **interactions**, see the brief explainer found in [`arc`'s documentation](https://arc.hypergonial.com/guides/interactions/).

Next up, we need to send our view, containing our components, in response to something:

=== "just hikari"

    === "Gateway"

        ```py
        @bot.listen()
        async def buttons(event: hikari.MessageCreateEvent) -> None:

            # Ignore bots or webhooks pinging us
            if not event.is_human:
                return

            me = bot.get_me()

            # If the bot is mentioned
            if me.id in event.message.user_mentions_ids:
                # Create a new instance of our view
                view = BasicView()
                await event.message.respond("Hello miru!", components=view)
                # Assign the view to the client and start it
                client.start_view(view)

        bot.run()
        ```

    === "REST"

        ```py
        # This function will handle the interactions received
        async def handle_command(interaction: hikari.CommandInteraction):
            # Create a new instance of our view
            view = BasicView()

            builder = interaction.build_response().set_content("Hello miru!")

            for action_row in view.build():
                builder.add_component(action_row)

            yield builder

            # Assign the view to the client and start it
            client.start_view(view)


        # Register the commands on startup.
        #
        # Note that this is not a nice way to manage this, as it is quite spammy
        # to do it every time the bot is started. You can either use a command handler
        # or only run this code in a script using `RESTApp` or add checks to not update
        # the commands if there were no changes
        async def create_commands(bot: hikari.RESTBot) -> None:
            application = await bot.rest.fetch_application()

            await bot.rest.set_application_commands(
                application=application.id,
                commands=[
                    bot.rest.slash_command_builder("test", "My first test command!"),
                ],
            )

        bot.add_startup_callback(create_commands)
        bot.set_listener(hikari.CommandInteraction, handle_command)

        bot.run()
        ```

        !!! tip
            In the case of `RESTBot`, it is *recommended* to use a command handler, so that you don't have to deal with manually
            registering commands and building responses yourself.

=== "arc"

    === "Gateway"

        ```py
        @arc_client.include
        @arc.slash_command("name", "description")
        async def some_slash_command(ctx: arc.GatewayContext) -> None:
            # Create a new instance of our view
            view = BasicView()
            await ctx.respond("Hello miru!", components=view)

            # Assign the view to the client and start it
            client.start_view(view)
        ```

    === "REST"

        ```py
        @arc_client.include
        @arc.slash_command("name", "description")
        async def some_slash_command(ctx: arc.RESTContext) -> None:
            # Create a new instance of our view
            view = BasicView()
            await ctx.respond("Hello miru!", components=view)

            # Assign the view to the client and start it
            client.start_view(view)
        ```

=== "crescent"

    ```py
    @crescent_client.include
    @crescent.command(name="name", description="description")
    class SomeSlashCommand:
        async def callback(self, ctx: crescent.Context) -> None:
            # Create a new instance of our view
            view = BasicView()
            await ctx.respond("Hello miru!", components=view)

            # Assign the view to the client and start it
            client.start_view(view)
    ```

=== "lightbulb"

    ```py
    @lightbulb_bot.command()
    @lightbulb.command("name", "description", auto_defer=False)
    @lightbulb.implements(lightbulb.SlashCommand)
    async def some_slash_command(ctx: lightbulb.SlashContext) -> None:
        # Create a new instance of our view
        view = BasicView()
        await ctx.respond("Hello miru!", components=view)

        # Assign the view to the client and start it
        client.start_view(view)
    ```

=== "tanjun"

    ```py
    @tanjun.as_slash_command("name", "description")
    async def some_slash_command(ctx: tanjun.abc.SlashContext) -> None:
        # Create a new instance of our view
        view = BasicView()
        await ctx.respond("Hello miru!", components=view)

        # Assign the view to the client and start it
        client.start_view(view)
    ```


If you run this code, you should see some basic logging information, and your bot will be online!
Mentioning the bot in any channel should make the bot send the component menu defined above!

## Subclassing

A more advanced way to use `miru` is to create our own custom classes, or templates, if you will, of buttons, select menus, and more.
This allows us to customize to a great degree their behaviour, pass variables dynamically, add or remove items on the fly, and more!

??? question "Help! What are classes, and how do they work?"
    If you're not sure how classes & subclassing work in Python, check out this [guide from Real Python](https://realpython.com/python3-object-oriented-programming/) on the subject.

Below you can see such an example:

```py
class YesButton(miru.Button):
    def __init__(self) -> None:
        # Initialize our button with some pre-defined properties
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label="Yes")
        self.value = True

    # The callback is the function that gets called when the button is pressed
    # If you are subclassing, you must use the name "callback" when defining it.
    async def callback(self, ctx: miru.ViewContext) -> None:
        # You can specify the ephemeral message flag
        # to make your response ephemeral
        await ctx.respond(
            "I'm sorry but this is unacceptable.",
            flags=hikari.MessageFlag.EPHEMERAL
        )
        # You can access the view an item is attached to
        # by accessing it's view property
        self.view.answer = self.value
        self.view.stop()


class NoButton(miru.Button):
    # Let's leave our arguments dynamic this time, instead of hard-coding them
    def __init__(self, style: hikari.ButtonStyle, label: str = "No") -> None:
        super().__init__(style=style, label=label)
        self.value = False

    async def callback(self, ctx: miru.ViewContext) -> None:
        await ctx.respond(
            "This is the only correct answer.",
            flags=hikari.MessageFlag.EPHEMERAL
        )
        self.view.answer = self.value
        self.view.stop()


class PineappleView(miru.View):

    # Include our custom buttons.
    yes = YesButton()
    no = NoButton(style=hikari.ButtonStyle.DANGER)
    # Let's also add a link button.
    # Link buttons cannot have a callback,
    # they simply direct the user to the given website
    learn_more = miru.LinkButton(
        url="https://en.wikipedia.org/wiki/Hawaiian_pizza", label="Learn More"
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.answer: bool | None = None
```

Then we can adjust our sending logic from the previous example like so:

=== "just hikari"

    === "Gateway"

        ```py hl_lines="10-13 22-27"
        @bot.listen()
        async def some_listener(event: hikari.MessageCreateEvent) -> None:

            if not event.is_human:
                return

            me = bot.get_me()

            if me.id in event.message.user_mentions_ids:
                view = PineappleView()  # Create the view

                await event.message.respond(
                    "Do you put pineapple on your pizza?",
                    components=view
                )

                client.start_view(view)

                # You can also wait until the view is stopped or times out
                await view.wait()

                if view.answer is not None:
                    print(f"Received an answer! It is: {view.answer}")
                else:
                    print("Did not receive an answer in time!")


        bot.run()
        ```

    === "REST"

        ```py hl_lines="2-5 17-22"
        async def handle_command(interaction: hikari.CommandInteraction):
            view = PineappleView()  # Create the view


            builder = interaction.build_response().set_content("Do you put pineapple on your pizza?")

            for action_row in view.build():
                builder.add_component(action_row)

            yield builder

            # Assign the view to the client and start it
            client.start_view(view)

            # You can also wait until the view is stopped or times out
            await view.wait()

            if view.answer is not None:
                print(f"Received an answer! It is: {view.answer}")
            else:
                print("Did not receive an answer in time!")


        async def create_commands(bot: hikari.RESTBot) -> None:
            application = await bot.rest.fetch_application()

            await bot.rest.set_application_commands(
                application=application.id,
                commands=[
                    bot.rest.slash_command_builder("test", "My first test command!"),
                ],
            )

        bot.add_startup_callback(create_commands)
        bot.set_listener(hikari.CommandInteraction, handle_command)

        bot.run()
        ```

=== "arc"

    === "Gateway"

        ```py hl_lines="4-7 13-18"
        @arc_client.include
        @arc.slash_command("name", "description")
        async def some_slash_command(ctx: arc.GatewayContext) -> None:
            view = PineappleView()  # Create the view

            await ctx.respond("Do you put pineapple on your pizza?", components=view)

            client.start_view(view)

            # You can also wait until the view is stopped or times out
            await view.wait()

            if view.answer is not None:
                    print(f"Received an answer! It is: {view.answer}")
                else:
                    print("Did not receive an answer in time!")
        ```

    === "REST"

        ```py hl_lines="4-7 13-18"
        @arc_client.include
        @arc.slash_command("name", "description")
        async def some_slash_command(ctx: arc.RESTContext) -> None:
            view = PineappleView()  # Create the view

            await ctx.respond("Do you put pineapple on your pizza?", components=view)

            client.start_view(view)

            # You can also wait until the view is stopped or times out
            await view.wait()

            if view.answer is not None:
                    print(f"Received an answer! It is: {view.answer}")
                else:
                    print("Did not receive an answer in time!")
        ```

=== "crescent"

    ```py hl_lines="5-8 14-19"
    @crescent_client.include
    @crescent.command(name="name", description="description")
    class SomeSlashCommand:
        async def callback(self, ctx: crescent.Context) -> None:
            view = PineappleView()  # Create the view

            await ctx.respond("Do you put pineapple on your pizza?", components=view)

            client.start_view(view)

            # You can also wait until the view is stopped or times out
            await view.wait()

            if view.answer is not None:
                    print(f"Received an answer! It is: {view.answer}")
                else:
                    print("Did not receive an answer in time!")
    ```

=== "lightbulb"

    ```py hl_lines="5-8 14-19"
    @lightbulb_bot.command()
    @lightbulb.command("name", "description", auto_defer=False)
    @lightbulb.implements(lightbulb.SlashCommand)
    async def some_slash_command(ctx: lightbulb.SlashContext) -> None:
        view = PineappleView()  # Create the view

        await ctx.respond("Do you put pineapple on your pizza?", components=view)

        client.start_view(view)

        # You can also wait until the view is stopped or times out
        await view.wait()

        if view.answer is not None:
                print(f"Received an answer! It is: {view.answer}")
            else:
                print("Did not receive an answer in time!")
    ```

=== "tanjun"

    ```py hl_lines="3-6 12-17"
    @tanjun.as_slash_command("name", "description")
    async def some_slash_command(ctx: tanjun.abc.SlashContext) -> None:
        view = PineappleView()  # Create the view

        await ctx.respond("Do you put pineapple on your pizza?", components=view)

        client.start_view(view)

        # You can also wait until the view is stopped or times out
        await view.wait()

        if view.answer is not None:
                print(f"Received an answer! It is: {view.answer}")
            else:
                print("Did not receive an answer in time!")
    ```

Running this code and mentioning the bot in a channel it can see should similarly yield a component menu.
The benefits of this approach are that you can define custom methods for your individual components,
and create "template" items for re-use later, reducing the need to paste the same code over and over again.

!!! info "Dynamically managing view items"
    You may also want to build views dynamically based on conditions, this can be done using the [`View.add_item()`][miru.view.View.add_item] method:

    ```py
    # add_item() calls can be chained!
    view = (
        PineappleView()
        .add_item(YesButton())
        .add_item(NoButton(style=hikari.ButtonStyle.DANGER, label="No"))
    )


    if some_condition:
        view.add_item(
            miru.LinkButton(url="https://en.wikipedia.org/wiki/Hawaiian_pizza", label="Learn More")
        )
    ```

    Items can also be removed using [`View.remove_item()`][miru.view.View.remove_item], or cleared using [`View.clear_items()`][miru.view.View.clear_items].

    Additionally, you can access all current items of a view using the [`View.children`][miru.view.View.children] property.
