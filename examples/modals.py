import hikari

import miru


class MyModal(miru.Modal, title="Example Title"):
    # Define our modal items
    # You can also use Modal.add_item() to add items to the modal after instantiation, just like with views.
    name = miru.TextInput(label="Name", placeholder="Enter your name!", required=True)
    bio = miru.TextInput(label="Biography", value="Pre-filled content!", style=hikari.TextInputStyle.PARAGRAPH)

    # The callback function is called after the user hits 'Submit'
    async def callback(self, context: miru.ModalContext) -> None:
        # You can also access the values using ctx.values, Modal.values, or use ctx.get_value_by_id()
        await context.respond(f"Your name: `{self.name.value}`\nYour bio: ```{self.bio.value}```")


class ModalView(miru.View):
    # Create a new button that will invoke our modal
    @miru.button(label="Click me!", style=hikari.ButtonStyle.PRIMARY)
    async def modal_button(self, context: miru.ViewContext, button: miru.Button) -> None:
        modal = MyModal()
        # You may also use the builder provided by Modal to send the modal to an arbitrary interaction.
        # Keep in mind that modals can only be sent in response to interactions.
        await context.respond_with_modal(modal)

        # OR
        # builder = modal.build_response(client)
        # await builder.create_modal_response(interaction)
        # client.start_modal(modal)


bot = hikari.GatewayBot("...")
client = miru.Client(bot)


@bot.listen()
async def modals(event: hikari.GuildMessageCreateEvent) -> None:
    # Do not process messages from bots or webhooks
    if not event.is_human:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if event.message.user_mentions_ids and me and me.id in event.message.user_mentions_ids:
        view = ModalView()
        await event.message.respond("This button triggers a modal!", components=view)
        client.start_view(view)


bot.run()

# MIT License
#
# Copyright (c) 2022-present hypergonial
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
