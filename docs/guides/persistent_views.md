---
title: Persistent Views
description: Learn how to keep your components working after a bot restart.
hide:
  - toc
search:
  exclude: true
---

# Persistent Views

You may have noticed that after an application restart, your views will no longer work,
even if the timeout did not expire. The solution to this problem are **persistent views**.

Persistent views are views that persist and keep functioning, even after an application restart.

Two conditions need to be met in order for a view to be considered persistent:

- The view must have a timeout of `None`.

- All items attached to the view must have a `custom_id` provided to it.

There are two variants of them, bound and unbound. Let's explore the differences between the two.

## Unbound

Unbound persistent views are the simpler of the two, they provide simple stateless logic, and are
not bound to any one message. They are best suited for views and items that are expected to return
the same results regardless of the context.

The limitations for this way of handling persistent views are that you cannot edit the view during runtime,
as unbound views have no concept of what message they are attached to.

!!! note
    This example is for Gateway bots, but it can be applied to work with REST bots in a similar manner.

```py
class Persistence(miru.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)  # Setting timeout to None

    # Providing custom IDs to all items
    @miru.button(label="Button 1", custom_id="my_unique_custom_id_1")
    async def button_one(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("You pressed button 1.")

    @miru.button(label="Button 2", custom_id="my_unique_custom_id_2")
    async def button_two(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        await ctx.respond("You pressed button 2.")
```

You then need to start the view when your bot starts up:

=== "just hikari"

    === "Gateway"

        ```py
        @bot.listen()
        async def start_views(event: hikari.StartedEvent) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to any message
            client.start_view(view, bind_to=None)
        ```

    === "REST"

        ```py
        # Let's assume this is a startup callback of a RESTBot
        async def start_views(bot: hikari.RESTBot) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to any message
            client.start_view(view, bind_to=None)
        ```

=== "arc"

    === "Gateway"

        ```py
        @arc_client.set_startup_hook
        async def start_views(client: arc.GatewayClient) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to any message
            client.start_view(view, bind_to=None)
        ```

    === "REST"

        ```py
        @arc_client.set_startup_hook
        async def start_views(client: arc.RESTClient) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to any message
            client.start_view(view, bind_to=None)
        ```

=== "crescent"

    === "Gateway"

        ```py
        @crescent_client.include
        @crescent.event
        async def start_views(event: hikari.StartedEvent) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to any message
            client.start_view(view, bind_to=None)
        ```

    === "REST"

        `crescent` has nothing specific for handling a REST bot's startup,
        so just use the underlying `hikari.RESTBot`:

        ```py
        # Let's assume this is a startup callback of a RESTBot
        async def start_views(bot: hikari.RESTBot) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to any message
            client.start_view(view, bind_to=None)
        ```

=== "lightbulb"

    ```py
    @bot.listen()
    async def start_views(event: hikari.StartedEvent) -> None:
        # You must reinstantiate the view with the same custom_ids every time
        view = Persistence()
        # Restart the listener for the view after application startup
        # and explicitly tell it to not bind to any message
        client.start_view(view, bind_to=None)
    ```

=== "tanjun"

    ```py
    @component.with_listener()
    async def event_listener(event: hikari.StartedEvent) -> None:
        # You must reinstantiate the view with the same custom_ids every time
        view = Persistence()
        # Restart the listener for the view after application startup
        # and explicitly tell it to not bind to any message
        client.start_view(view, bind_to=None)
    ```

!!! note
    **Unbound** persistent views should **not** be started after sending, since a single view instance handles all interactions for all messages.

    If you do so, you may end up with duplicate responses.

Try restarting the bot after sending your view, your buttons should keep working!

!!! warning
    [`View.message`][miru.view.View.message] will be `None` for unbound persistent views.

## Bound

Bound views are different in the sense that they are bound to a specific message instead of globally handling
interactions for every view of the same type. To create a bound view, instead of an unbound one,
simply pass a message ID to `bind_to=` when starting the view. You can also leave it empty, in which case the view will bind to the first message it receives an interaction from. This also allows for the view to be edited during runtime.


=== "just hikari"

    === "Gateway"

        ```py
        @bot.listen()
        async def start_views(event: hikari.StartedEvent) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            message_id = ...
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to a message
            client.start_view(view, bind_to=message_id)
        ```

    === "REST"

        ```py
        # Let's assume this is a startup callback of a RESTBot
        async def start_views(bot: hikari.RESTBot) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            message_id = ...
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to a message
            client.start_view(view, bind_to=message_id)
        ```

=== "arc"

    === "Gateway"

        ```py
        @arc_client.set_startup_hook
        async def start_views(client: arc.GatewayClient) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            message_id = ...
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to a message
            client.start_view(view, bind_to=message_id)
        ```

    === "REST"

        ```py
        @arc_client.set_startup_hook
        async def start_views(client: arc.RESTClient) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            message_id = ...
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to a message
            client.start_view(view, bind_to=message_id)
        ```

=== "crescent"

    === "Gateway"

        ```py
        @crescent_client.include
        @crescent.event
        async def start_views(event: hikari.StartedEvent) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            message_id = ...
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to a message
            client.start_view(view, bind_to=message_id)
        ```

    === "REST"

        `crescent` has nothing specific for handling a REST bot's startup,
        so just use the underlying `hikari.RESTBot`:

        ```py
        # Let's assume this is a startup callback of a RESTBot
        async def start_views(bot: hikari.RESTBot) -> None:
            # You must reinstantiate the view with the same custom_ids every time
            view = Persistence()
            message_id = ...
            # Restart the listener for the view after application startup
            # and explicitly tell it to not bind to a message
            client.start_view(view, bind_to=message_id)
        ```

=== "lightbulb"

    ```py
    @bot.listen()
    async def start_views(event: hikari.StartedEvent) -> None:
        # You must reinstantiate the view with the same custom_ids every time
        view = Persistence()
        message_id = ...
        # Restart the listener for the view after application startup
        # and explicitly tell it to not bind to a message
        client.start_view(view, bind_to=message_id)
    ```

=== "tanjun"

    ```py
    @component.with_listener()
    async def event_listener(event: hikari.StartedEvent) -> None:
        # You must reinstantiate the view with the same custom_ids every time
        view = Persistence()
        message_id = ...
        # Restart the listener for the view after application startup
        # and explicitly tell it to not bind to a message
        client.start_view(view, bind_to=message_id)
    ```
