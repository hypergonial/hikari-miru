---
title: View Checks & Timeout Handling
description: Learn how you can set view checks and handle timing out in miru.
hide:
  - toc
search:
  exclude: true
---

# View Checks & Timeout Handling

## Checks

Checks are functions that are called when the callback of an item is about to be called.
They must evaluate to a truthy value to allow execution of the callback code.

Views provide a way to implement this via the [`View.view_check()`][miru.view.View.view_check] method.
This object receives [`ViewContext`][miru.context.view.ViewContext] as it's only argument, and if it
does not evaluate to a truthy value, the interaction will be ignored.

=== "Gateway"

    ```py
    class ChecksView(miru.View[miru.GW]):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(
            self, button: miru.Button[miru.GW], ctx: miru.ViewContext[miru.GW]
        ) -> None:
            await ctx.respond("You clicked me!")

        # Define a custom view check
        async def view_check(self, ctx: miru.ViewContext[miru.GW]) -> bool:
            # This view will only handle interactions that belong to this user
            # For every other user, we show them an error
            if ctx.user.id != 123456789:
                await ctx.respond("You cannot press this!")
                return False

            return True
    ```

=== "REST"

    ```py
    class ChecksView(miru.View[miru.REST]):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(
            self, button: miru.Button[miru.REST], ctx: miru.ViewContext[miru.REST]
        ) -> None:
            await ctx.respond("You clicked me!")

        # Define a custom view check
        async def view_check(self, ctx: miru.ViewContext[miru.REST]) -> bool:
            # This view will only handle interactions that belong to this user
            # For every other user, we show them an error
            if ctx.user.id != 123456789:
                await ctx.respond("You cannot press this!")
                return False

            return True
    ```

## Timeout

By default, views time out after 120 seconds of inactivity. This can be controlled via the `timeout=`
keyword argument passed to views. To execute code when the view times out, you can override the
[`View.on_timeout()`][miru.abc.item_handler.ItemHandler.on_timeout] method. This function receives no arguments.

=== "Gateway"

    ```py
    class TimeoutView(miru.View[miru.GW]):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(
            self, button: miru.Button[miru.GW], ctx: miru.ViewContext[miru.GW]
        ) -> None:
            await ctx.respond("You clicked me!")

        async def on_timeout(self) -> None:
            print("This view timed out!")
            # Run custom logic here


    # Somewhere else in code:

    view = TimeoutView(timeout=10.0)
    ```

=== "REST"

    ```py
    class TimeoutView(miru.View[miru.REST]):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(
            self, button: miru.Button[miru.REST], ctx: miru.ViewContext[miru.REST]
        ) -> None:
            await ctx.respond("You clicked me!")

        async def on_timeout(self) -> None:
            print("This view timed out!")
            # Run custom logic here


    # Somewhere else in code:

    view = TimeoutView(timeout=10.0)
    ```

!!! note
    Note that if you manually call [`View.stop()`][miru.abc.item_handler.ItemHandler.stop], [`View.on_timeout()`][miru.abc.item_handler.ItemHandler.on_timeout] will not be called.
