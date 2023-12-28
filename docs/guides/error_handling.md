---
title: Error Handling
description: Learn how to handle errors in views.
hide:
  - toc
search:
  exclude: true
---

# Error Handling

Error handling within views is provided via the [`View.on_error`][miru.view.View.on_error] method.
When an error occurs in any item's callback or the timeout function, this function is called.

The first parameter is always the exception that occured, and if the the exception occured in an
item's callback, the item and the context are also passed. If you do not override this function,
it will, by default, print the exception and traceback to the console.

## Example:

=== "Gateway"

    ```py
    import hikari
    import miru

    class ErrorView(miru.View[miru.GW]):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, button: miru.Button[miru.GW], ctx: miru.ViewContext[miru.GW]) -> None:
            await ctx.respond("You clicked me!")

        # Create a button that raises an exception
        @miru.button(label="Error", style=hikari.ButtonStyle.DANGER)
        async def error_button(
            self, button: miru.Button[miru.GW], ctx: miru.ViewContext[miru.GW]
        ) -> None:
            raise RuntimeError("I'm an error!")

        # Define our custom error-handler
        # Keep in mind that if you override the error-handler,
        # tracebacks will no longer be printed in the console,
        # unless you call super's implementation.
        async def on_error(
            self,
            error: Exception,
            item: miru.ViewItem[miru.GW] | None = None,
            ctx: miru.ViewContext[miru.GW] | None = None
        ) -> None:
            # ctx is only passed if the error is raised in an item callback
            if ctx is not None:
                await ctx.respond(f"Oh no! This error occured: {error}")
    ```

=== "REST"

    ```py
    import hikari
    import miru

    class ErrorView(miru.View[miru.REST]):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, button: miru.Button[miru.REST], ctx: miru.ViewContext[miru.REST]) -> None:
            await ctx.respond("You clicked me!")

        # Create a button that raises an exception
        @miru.button(label="Error", style=hikari.ButtonStyle.DANGER)
        async def error_button(self, button: miru.Button[miru.REST], ctx: miru.ViewContext[miru.REST]) -> None:
            raise RuntimeError("I'm an error!")

        # Define our custom error-handler
        # Keep in mind that if you override the error-handler,
        # tracebacks will no longer be printed in the console,
        # unless you call super's implementation.
        async def on_error(
            self,
            error: Exception,
            item: miru.ViewItem[miru.REST] | None = None,
            ctx: miru.ViewContext[miru.REST] | None = None
        ) -> None:
            # ctx is only passed if the error is raised in an item callback
            if ctx is not None:
                await ctx.respond(f"Oh no! This error occured: {error}")
    ```
