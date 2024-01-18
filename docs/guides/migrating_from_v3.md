---
title: Migrating from v3
description: Learn what changed in v4 and how to migrate your bot from v3!
hide:
  - toc
search:
  exclude: true
---

# Migrating from v3

With the release of miru version 4.0 comes a number of large feature releases, notably RESTBot support and the addition of dependency injection to manage state. However the changes to the underlying architecture of the library necessitated some breaking changes.

This guide tries to help you migrate an existing application using miru v3 to v4, and explore some of the changes you need to make.

!!! warning
    `miru` v4 bumps the minimum required Python version to **3.10** or higher. If this is unsuitable for your usecase, you should continue using v3.

    For the v3 documentation, see [this](https://hikari-miru.readthedocs.io/en/v3/index.html) link.

## Client

`miru.install()` has been removed in v4, in an effort to stop relying on global state.

Instead, you need to create [`Client`][miru.client.Client], and pass your bot to it:

=== "v4"

    ```py
    bot = hikari.GatewayBot(...) # or hikari.RESTBot
    client = miru.Client(bot)
    ```

=== "v3"

    ```py
    bot = hikari.GatewayBot(...)
    client = miru.install(bot)
    ```

## Decorated callbacks

The ordering of arguments passed to decorated callbacks such as `@miru.button` has changed. They now take `Context` as their first argument and the respective item as the second. This is to improve consistency with other parts of the library.

=== "v4"

    ```py
    @miru.button(...)
    async def some_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        ...
    ```

=== "v3"

    ```py
    @miru.button(...)
    async def some_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        ...
    ```

## Starting views

`view.start()` has been removed in favor of the newly added [`Client.start_view()`][miru.client.Client.start_view].

Since in v4 everything is tied to the [`Client`][miru.client.Client], views need to be assigned to one when being started. Note that the requirement to pass a message to the start call has been lifted.

=== "v4"

    ```py
    view = miru.View(...)
    await something.respond(..., components=view)
    client.start_view(view) # This is the client you created earlier
    ```

=== "v3"

    ```py
    view = miru.View(...)
    msg = await something.respond(..., components=view)
    await view.start(msg)
    ```

## Sending modals

`Modal.send()` has been removed.

Due to the changes required to support REST bots, it is no longer possible to put modals themselves in control of sending, due to the many ways they can now be sent as a response.

Therefore, this responsibility is now in the hands of the user. This *does* add some extra complexity, however it also allows for much greater control over how these objects are sent, and thus better compatibility with other libraries.

=== "v4"

    ```py
    modal = miru.Modal(...)
    # This returns a custom InteractionModalBuilder
    # It can be returned in REST callbacks
    builder = modal.build_response()
    # Or you can use some of the custom methods it has
    await builder.create_modal_response(interaction)

    client.start_modal(modal)
    ```

=== "v3"

    ```py
    modal = miru.Modal(...)
    await modal.send(interaction)
    ```

For more information on how to use these builders with each of the major **command handler** frameworks, please see the updated [modal](./modals.md) guide.

## Sending navigators & menus

`NavigatorView.send()`, `Menu.send()` have been removed.

Similarly to modals, menus & navigators are also now turned into builders. However, since the payloads are built asynchronously, you need to use [`Menu.build_response_async()`][miru.ext.menu.menu.Menu.build_response_async] and [`NavigatorView.build_response_async()`][miru.ext.nav.NavigatorView.build_response_async] respectively. If you're handling an interaction, you may also need to defer beforehand depending on how long it takes to build the payload.

=== "v4"

    === "NavigatorView"

        ```py
        navigator = nav.NavigatorView(...)
        # This returns a custom InteractionMessageBuilder
        # It can be returned in REST callbacks
        builder = await navigator.build_response_async()

        # Or you can use some of the custom methods it has
        await builder.create_initial_response(interaction)
        # Or
        await builder.send_to_channel(channel_id)

        client.start_view(navigator)
        ```

    === "Menu"

        ```py
        my_menu = menu.Menu(...)
        # This returns a custom InteractionMessageBuilder
        # It can be returned in REST callbacks
        builder = await my_menu.build_response_async()

        # Or you can use some of the custom methods it has
        await builder.create_initial_response(interaction)
        # Or
        await builder.send_to_channel(channel_id)

        client.start_view(my_menu)
        ```

=== "v3"

    === "NavigatorView"

        ```py
        navigator = nav.NavigatorView(...)
        await navigator.send(channel_id | interaction)
        ```

    === "Menu"

        ```py
        my_menu = menu.Menu(...)
        await my_menu.send(channel_id | interaction)
        ```

For more information on how to use these builders with each of the major **command handler** frameworks, please see the updated [menu](./menus.md) and [navigator](./navigators.md) guides.

## Link buttons

Link buttons have been seperated out of `miru.Button` and received their own class: `miru.LinkButton`.

For your existing link buttons, it should be as simple as updating the class:

=== "v4"

    ```py
    view.add_item(miru.LinkButton(url="https://google.com"))
    ```

=== "v3"

    ```py
    view.add_item(miru.Button(url="https://google.com"))
    ```
