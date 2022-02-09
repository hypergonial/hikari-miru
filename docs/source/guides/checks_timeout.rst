View Checks & Timeout Handling
==============================

Checks
------

Checks are functions that are called when the callback of an item is about to be called.
They must evaluate to a truthy value to allow execution of the callback code.

Views provide a way to implement this via the :obj:`miru.views.View.view_check` coroutine method.
This object receives :obj:`miru.context.Context` as it's only argument, and if it does not evaluate
to a truthy value, the interaction will be ignored.

::

    import hikari
    import miru

    class ChecksView(miru.View):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            await ctx.respond("You clicked me!")
        
        # Define a custom view check
        async def view_check(self, ctx: miru.ViewContext) -> bool:
            # This view will only handle interactions that belong to this user
            # For every other user the interaction will simply fail
            return ctx.user.id == 123456789
            # You can also respond to the interaction here if you wish to provide a custom
            # error message, but do not forget to return a falsy value afterwards.

    ...

Timeout
-------

By default, views time out after 120 seconds of inactivity. This can be controlled via the ``timeout``
keyword argument passed to views. To execute code when the view times out, you can override the
:obj:`miru.views.View.on_timeout` coroutine method. This function receives no arguments.

::

    import hikari
    import miru

    class TimeoutView(miru.View):

        @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
        async def basic_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
            await ctx.respond("You clicked me!")
        
        async def on_timeout(self) -> None:
            print("This view timed out!")


    # Somewhere else in code:

    view = TimeoutView(timeout=10.0)

.. note::
    Please note that if you manually call :obj:`miru.views.View.stop`, :obj:`miru.views.View.on_timeout` will not be called.
