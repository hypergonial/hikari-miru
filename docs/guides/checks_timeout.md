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

```py
class ChecksView(miru.View):

    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("You clicked me!")

    # Define a custom view check
    async def view_check(self, ctx: miru.ViewContext) -> bool:
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

```py
class TimeoutView(miru.View):

    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("You clicked me!")

    async def on_timeout(self) -> None:
        print("This view timed out!")
        # Run custom logic here


# Somewhere else in code:

view = TimeoutView(timeout=10.0)
```

!!! note
    Note that if you manually call [`View.stop()`][miru.abc.item_handler.ItemHandler.stop], [`View.on_timeout()`][miru.abc.item_handler.ItemHandler.on_timeout] will not be called.
