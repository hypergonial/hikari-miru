Modals
======

With the release of miru v2.0.0, **modals** are now available to use. They function in a very similar way to
views, with a few notable exceptions, namely:

- Modal listeners start automatically after sending.

- Modal items do not have individual callbacks, instead the entire modal has one singular callback.

- Modals only accept :obj:`miru.abc.item.ModalItem`, and pass :obj:`miru.context.ModalContext` when the callback is triggered.


.. note::
    Please note that modals can only be sent as a response to an **interaction**.

Let's create our first modal:

::

    class MyModal(miru.Modal):
        name = miru.TextInput(label="Name", placeholder="Type your name!", required=True)
        bio = miru.TextInput(label="Biography", value="Pre-filled content!", style=hikari.TextInputStyle.PARAGRAPH)

        # The callback function is called after the user hits 'Submit'
        async def callback(self, ctx: miru.ModalContext) -> None:
            # You can also access the values using ctx.values, Modal.values, or use ctx.get_value_by_id()
            await ctx.respond(f"Your name: `{self.name.value}`\nYour bio: ```{self.bio.value}```")

There is also an alternative way to add items to a modal, through the :obj:`miru.Modal.add_item` method, similarly to views.

.. warning::
    Please be careful when naming your modal item variables. They cannot shadow existing modal properties such as **title** or **custom_id**.

Now we will get an **interaction** through the use of a button so we can send the user our modal:

::

    class ModalView(miru.View):

    # Create a new button that will invoke our modal
    @miru.button(label="Click me!", style=hikari.ButtonStyle.PRIMARY)
    async def modal_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        modal = MyModal(title="Example Title")

        # You may also use Modal.send(interaction) if not working with a miru context object.
        # (e.g. slash commands)
        await ctx.respond_with_modal(modal)

    bot = hikari.GatewayBot("YOUR_TOKEN_HERE")
    miru.install(bot)

    @bot.listen()
    async def modals(event: hikari.GuildMessageCreateEvent) -> None:

        # Do not process messages from bots or webhooks
        if not event.is_human:
            return
        
        me = bot.get_me()

        if me.id in event.message.user_mentions_ids:
            view = ModalView()
            message = await event.message.respond(
                "This button triggers a modal!", components=view
            )
            await view.start(message)


    bot.run()

Combining the above code with the modal we created earlier, you should now have a basic working example where the user can click the button, 
get prompted with a modal, and then submit their input. For more information on modals, please see the :obj:`miru.Modal` API reference.