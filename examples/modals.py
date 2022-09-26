import hikari
import miru


class MyModal(miru.Modal):
    # Define our modal items
    # You can also use Modal.add_item() to add items to the modal after instantiation, just like with views.
    name = miru.TextInput(label="Name", placeholder="Enter your name!", required=True)
    bio = miru.TextInput(label="Biography", value="Pre-filled content!", style=hikari.TextInputStyle.PARAGRAPH)

    # The callback function is called after the user hits 'Submit'
    async def callback(self, ctx: miru.ModalContext) -> None:
        # ModalContext.values is a mapping of {TextInput: value}
        values = [value for value in ctx.values.values()]
        await ctx.respond(f"Received the following input: ```{' | '.join(values)}```")


class ModalView(miru.View):

    # Create a new button that will invoke our modal
    @miru.button(label="Click me!", style=hikari.ButtonStyle.PRIMARY)
    async def modal_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        modal = MyModal("Example Title")
        # You may also use Modal.send(interaction) if not working with a miru context object. (e.g. slash commands)
        # Keep in mind that modals can only be sent in response to interactions.
        await ctx.respond_with_modal(modal)
        # OR
        # await modal.send(ctx.interaction)


bot = hikari.GatewayBot("...")
miru.load(bot)


@bot.listen()
async def modals(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("miru"):
        view = ModalView()
        message = await event.message.respond("This button triggers a modal!", components=view)
        await view.start(message)


bot.run()

# MIT License
#
# Copyright (c) 2022-present HyperGH
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
