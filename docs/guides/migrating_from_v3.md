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

## Client

`miru.install()` has been removed in v4, in an effort to stop relying on global state. Instead, you need to create [`Client`][miru.client.Client], and pass your bot to it:

=== v3

    ```py
    bot = hikari.GatewayBot(...)
    client = miru.install(bot)
    ```

=== v4

    ```py
    bot = hikari.GatewayBot(...) # or hikari.RESTBot
    client = miru.Client(bot)
    ```

## Decorated callbacks

The ordering of arguments passed to decorated callbacks such as `@miru.button` has changed. They now take `Context` as their first argument and the respective item as the second. This is to improve consistency with other parts of the library.

=== v3

    ```py
    @miru.button(...)
    async def some_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        ...
    ```

=== v4

    ```py
    @miru.button(...)
    async def some_button(self, ctx: miru.ViewContext, button: miru.Button) -> None:
        ...
    ```

## Starting views

`view.start()` has been removed in favor of the newly added [`Client.start_view()`][miru.client.Client.start_view].

Since in v4 everything is tied to the [`Client`][miru.client.Client], views need to be assigned to one when being started. Note that the requirement to pass a message to the start call has been lifted.

=== v3

    ```py
    view = miru.View(...)
    msg = await something.respond(..., components=view)
    await view.start(msg)
    ```

=== v4

    ```py
    view = miru.View(...)
    await something.respond(..., components=view)
    client.start_view(view) # This is the client you created earlier
    ```

## Sending modals, navigators

`Modal.send()`, `NavigatorView.send()` have been removed.

Due to the changes required to support REST bots, it is no longer possible to put modals & navigator views in control of sending, due to the many ways these objects can be sent as a response. Therefore, this responsibility is now in the hands of the user. This *does* add some extra complexity, however it also allows for much greater control over how these objects are sent, and thus better compatibility with other libraries.

=== v3

    ```py
    modal = miru.Modal(...)
    await modal.send(interaction)
    ```

=== v4

    ```py
    modal = miru.Modal(...)
    # This returns a custom InteractionModalBuilder
    # It can be returned in REST callbacks
    builder = modal.build_response()
    # Or you can use some of the custom methods it has
    await builder.create_modal_response(interaction)

    client.start_modal(modal)
    ```

For more information on how to use these builders with each of the major command handler frameworks, please see the updated [modal](./modals.md) and [navigator](./navigators.md) guides.

## Sending menus

`Menu.send()` has been removed.

Similarly to modals & navigators, menus are also now turned into builders. However, since menu payloads are built asynchronously, you need to use [`Menu.build_response_async()`][miru.ext.menu.menu.Menu.build_response_async] instead. If you're handling an interaction, you may also need to defer beforehand if building your initial screen takes a long time.

=== v3

    ```py
    modal = menu.Menu(...)
    await menu.send(channel_id | interaction)
    ```

=== v4

    ```py
    menu = menu.Menu(...)
    # This returns a custom InteractionMessageBuilder
    # It can be returned in REST callbacks
    builder = await menu.build_response_async()

    # Or you can use some of the custom methods it has
    await builder.create_initial_response(interaction)
    # Or
    await builder.send_to_channel(channel_id)

    client.start_view(menu)
    ```

For more information on how to use these builders with each of the major command handler frameworks, please see the updated [menu](./menus.md) guide.
