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

## Installation


`miru` can be installed using pip via the following command:

```sh
pip install hikari-miru
```

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

Then you can instantiate your bot class, and create a miru [Client][miru.client.Client] from it.

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

Next up, we need to send our view. `miru` has support for all popular command handlers, and naturally can be used with only hikari as well.

=== "arc"

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

=== "crescent"

    ```py
    @crescent_client.include
    @crescent.command("name", "description")
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

    !!! note
        Lightbulb only supports Gateway bots.

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

=== "just hikari"

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

    !!! note
        This is Gateway-only, however you can implement slash commands using only
        hikari for REST, but that is outside the scope of this guide.

If you run this code, you should see some basic logging information, and your bot will be online!
Mentioning the bot in any channel should make the bot send the component menu defined above!

## Subclassing

A more advanced way to use `miru` is to create our own custom classes of buttons, select menus, and more.
This allows us to customize to a great degree their behaviour, pass variables dynamically, add or remove
items on the fly, and more!

Below you can see such an example:

```py
import hikari
import miru

class YesButton(miru.Button):
    def __init__(self) -> None:
        # Initialize our button with some pre-defined properties
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label="Yes")

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
        self.view.answer = True
        self.view.stop()


class NoButton(miru.Button):
    # Let's leave our arguments dynamic this time, instead of hard-coding them
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def callback(self, ctx: miru.ViewContext) -> None:
        await ctx.respond(
            "This is the only correct answer.",
            flags=hikari.MessageFlag.EPHEMERAL
        )
        self.view.answer = False
        self.view.stop()


class PineappleView(miru.View):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.answer = None

bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
client = miru.Client(bot)
```

Then we can adjust our sending logic from the previous example like so:

=== "arc"

    ```py
    @arc_client.include
    @arc.slash_command("name", "description")
    async def some_slash_command(ctx: arc.GatewayContext) -> None:
        view = PineappleView()  # Create a new view
        view.add_item(YesButton())  # Add our custom buttons to it
        # Pass arguments to NoButton
        view.add_item(NoButton(style=hikari.ButtonStyle.DANGER, label="No"))

        await ctx.respond("Do you put pineapple on your pizza?", components=view)

        client.start_view(view)

        await view.wait()  # Wait until the view is stopped or times out

        if view.answer is not None:
                print(f"Received an answer! It is: {view.answer}")
            else:
                print("Did not receive an answer in time!")
    ```

=== "crescent"

    ```py
    @crescent_client.include
    @crescent.command("name", "description")
    class SomeSlashCommand:
        async def callback(self, ctx: crescent.Context) -> None:
            view = PineappleView()  # Create a new view
            view.add_item(YesButton())  # Add our custom buttons to it
            # Pass arguments to NoButton
            view.add_item(NoButton(style=hikari.ButtonStyle.DANGER, label="No"))

            await ctx.respond("Do you put pineapple on your pizza?", components=view)

            client.start_view(view)

            await view.wait()  # Wait until the view is stopped or times out

            if view.answer is not None:
                    print(f"Received an answer! It is: {view.answer}")
                else:
                    print("Did not receive an answer in time!")
    ```

=== "lightbulb"

    ```py
    @lightbulb_bot.command()
    @lightbulb.command("name", "description", auto_defer=False)
    @lightbulb.implements(lightbulb.SlashCommand)
    async def some_slash_command(ctx: lightbulb.SlashContext) -> None:
        view = PineappleView()  # Create a new view
        view.add_item(YesButton())  # Add our custom buttons to it
        # Pass arguments to NoButton
        view.add_item(NoButton(style=hikari.ButtonStyle.DANGER, label="No"))

        await ctx.respond("Do you put pineapple on your pizza?", components=view)

        client.start_view(view)

        await view.wait()  # Wait until the view is stopped or times out

        if view.answer is not None:
                print(f"Received an answer! It is: {view.answer}")
            else:
                print("Did not receive an answer in time!")
    ```

=== "tanjun"

    ```py
    @tanjun.as_slash_command("name", "description")
    async def some_slash_command(ctx: tanjun.abc.SlashContext) -> None:
        view = PineappleView()  # Create a new view
        view.add_item(YesButton())  # Add our custom buttons to it
        # Pass arguments to NoButton
        view.add_item(NoButton(style=hikari.ButtonStyle.DANGER, label="No"))

        await ctx.respond("Do you put pineapple on your pizza?", components=view)

        client.start_view(view)

        await view.wait()  # Wait until the view is stopped or times out

        if view.answer is not None:
                print(f"Received an answer! It is: {view.answer}")
            else:
                print("Did not receive an answer in time!")
    ```

=== "just hikari"

    ```py
    @bot.listen()
    async def some_listener(event: hikari.MessageCreateEvent) -> None:

        if not event.is_human:
            return

        me = bot.get_me()

        if me.id in event.message.user_mentions_ids:
            view = PineappleView()  # Create a new view
            view.add_item(YesButton())  # Add our custom buttons to it
            # Pass arguments to NoButton
            view.add_item(NoButton(style=hikari.ButtonStyle.DANGER, label="No"))

            await event.message.respond(
                "Do you put pineapple on your pizza?",
                components=view
            )

            client.start_view(view)

            await view.wait()  # Wait until the view is stopped or times out

            if view.answer is not None:
                print(f"Received an answer! It is: {view.answer}")
            else:
                print("Did not receive an answer in time!")


    bot.run()
    ```

Running this code and mentioning the bot in a channel it can see should similarly yield a component menu.
The benefits of this approach are that you can define custom methods for your individual components,
and create "template" items for re-use later, reducing the need to paste the same code over and over again.
