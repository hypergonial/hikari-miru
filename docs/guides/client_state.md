---
title: Client as State
description: Learn how to store and access the miru client using popular command handlers.
hide:
  - toc
search:
  exclude: true
---

# Client as State

The miru [`Client`][miru.client.Client] is the centerpiece of the library, it starts & manages all views and modals, routes interactions to them, etc... However, when working with a larger codebase, it can get quite complicated to pass the client around to all the places that need it.

This guide tries to cover some ways you can manage your miru client as state using popular command handlers, so it is always available when you need it.

=== "arc"

    === "Gateway"

        The `miru` client is automatically set as a type dependency when creating your client using [`Client.from_arc()`][miru.client.Client.from_arc].

        ```py
        bot = hikari.GatewayBot(...)
        arc_client = arc.GatewayClient(bot)
        # The miru client is automatically set as a type dependency
        client = miru.Client.from_arc(arc_client)
        ```

        Somewhere else in your code:

        ```py
        @arc.slash_command("name", "description")
        # Inject the miru client as normal
        async def some_command(ctx: arc.GatewayContext, client: miru.Client = arc.inject()) -> None:
            view = miru.View(...)
            await ctx.respond(..., components=view)
            client.start_view(view)
        ```

    === "REST"

        The `miru` client is automatically set as a type dependency when creating your client using [`Client.from_arc()`][miru.client.Client.from_arc].

        ```py
        bot = hikari.RESTBot(...)
        arc_client = arc.RESTClient(bot)
        # The miru client is automatically set as a type dependency
        client = miru.Client.from_arc(arc_client)
        ```

        Somewhere else in your code:

        ```py
        @arc.slash_command("name", "description")
        # Inject the miru client as normal
        async def some_command(ctx: arc.RESTContext, client: miru.Client = arc.inject()) -> None:
            view = miru.View(...)
            await ctx.respond(..., components=view)
            client.start_view(view)
        ```

    To learn more about **dependency injection** in `arc`, see [here](https://arc.hypergonial.com/guides/dependency_injection/).

=== "crescent"

    === "Gateway"

        The recommended way to manage state in crescent is using a **model**:

        ```py
        @dataclasses.dataclass
        class MyModel:
            miru: miru.Client

        bot = hikari.GatewayBot(...)
        client = miru.Client(bot)
        crescent_client = crescent.Client(bot, MyModel(client))
        ```

        Somewhere else in your code:

        ```py
        @crescent.command(name="name", description="description")
        class SomeCommand:
            async def callback(self, ctx: crescent.Context) -> None:
                view = miru.View(...)
                await ctx.respond(..., components=view)
                # Access the miru client from the model
                ctx.client.model.miru.start_view(view)
        ```

    === "REST"

        The recommended way to manage state in crescent is using a **model**:

        ```py
        @dataclasses.dataclass
        class MyModel:
            miru: miru.Client

        bot = hikari.RESTBot(...)
        client = miru.Client(bot)
        crescent_client = crescent.Client(bot, MyModel(client))
        ```

        Somewhere else in your code:

        ```py
        @crescent.command(name="name", description="description")
        class SomeCommand:
            async def callback(self, ctx: crescent.Context) -> None:
                view = miru.View(...)
                await ctx.respond(..., components=view)
                # Access the miru client from the model
                ctx.client.model.miru.start_view(view)
        ```

    To learn more about **models** in crescent, see [here](https://hikari-crescent.github.io/hikari-crescent/guides/plugins/#model).

=== "lightbulb"

    The recommended way to manage state in lightbulb is via a `DataStore` object.

    ```py
    bot = lightbulb.BotApp(...)
    # Save the client to the bot's DataStore
    bot.d.miru = miru.Client(bot)
    ```

    Somewhere else in your code:

    ```py
    @lightbulb.command("name", "description", auto_defer=False)
    @lightbulb.implements(lightbulb.SlashCommand)
    async def some_command(ctx: lightbulb.SlashContext) -> None:
        view = miru.View(...)
        await ctx.respond(..., components=view)

        # Access the miru client from the DataStore
        ctx.app.d.miru.start_view(view)
    ```

    To learn more about `DataStore`, see [here](https://hikari-lightbulb.readthedocs.io/en/latest/api_references/utils.html#lightbulb.utils.data_store.DataStore).

=== "tanjun"

    === "Gateway"

        The `miru` client is automatically set as a type dependency when creating your client using [`Client.from_tanjun()`][miru.client.Client.from_tanjun].

        ```py
        bot = hikari.GatewayBot(...)
        tanjun_client = tanjun.Client.from_gateway_bot(bot)
        # The miru client is automatically set as a type dependency
        client = miru.Client.from_tanjun(tanjun_client)
        ```

        Somewhere else in your code:

        ```py
        @tanjun.as_slash_command("name", "description")
        # Inject the miru client as normal
        async def some_command(ctx: tanjun.abc.SlashContext, client: miru.Client = alluka.inject()) -> None:
            view = miru.View(...)
            await ctx.respond(..., components=view)
            client.start_view(view)
        ```

    === "REST"

        The `miru` client is automatically set as a type dependency when creating your client using [`Client.from_tanjun()`][miru.client.Client.from_tanjun].

        ```py
        bot = hikari.RESTBot(...)
        tanjun_client = tanjun.Client.from_rest_bot(bot)
        # The miru client is automatically set as a type dependency
        client = miru.Client.from_tanjun(tanjun_client)
        ```

        Somewhere else in your code:

        ```py
        @tanjun.as_slash_command("name", "description")
        # Inject the miru client as normal
        async def some_command(ctx: tanjun.abc.SlashContext, client: miru.Client = alluka.inject()) -> None:
            view = miru.View(...)
            await ctx.respond(..., components=view)
            client.start_view(view)
        ```

    To learn more about **dependency injection** in Tanjun, see [here](https://tanjun.cursed.solutions/usage/#dependency-injection).

!!! tip
    If you're **not using a command handler**, a good way to manage state (such as the miru client) can be through **dependency injection**. You can use a library like [alluka](https://alluka.cursed.solutions/) for this.
