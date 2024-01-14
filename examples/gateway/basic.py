import hikari
import miru

from miru import GW

# This is a basic example demonstrating how to create a simple component-based menu.
# This example uses decorators to create the components, if you want to use variables
# instead of static values for the component properties, check out the subclassed example.

bot = hikari.GatewayBot("...")
client = miru.Client(bot)

class BasicView(miru.View):

    # Define a new TextSelect menu with two options
    @miru.text_select(
        placeholder="Select me!",
        options=[
            miru.SelectOption(label="Option 1"),
            miru.SelectOption(label="Option 2"),
        ],
    )
    async def basic_select(self, select: miru.TextSelect, ctx: miru.ViewContext) -> None:
        await ctx.respond(f"You've chosen {select.values[0]}!")

    # Define a new Button with the Style of success (Green)
    @miru.button(label="Click me!", style=hikari.ButtonStyle.SUCCESS)
    async def basic_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        await ctx.respond("You clicked me!")

    # Define a new Button that when pressed will stop the view & invalidate all the buttons in this view
    @miru.button(label="Stop me!", style=hikari.ButtonStyle.DANGER)
    async def stop_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.stop()  # Called to stop the view





@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or webhooks
    if not event.is_human:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if me.id in event.message.user_mentions_ids:
        view = BasicView()  # Create an instance of our newly created BasicView
        # Attach the components defined in the view to our message
        await event.message.respond("This is a basic component menu built with miru!", components=view)

        client.start_view(view)  # Attach the view to the client and start it


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
