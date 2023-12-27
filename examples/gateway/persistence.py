import hikari
import miru

# If you want your components to work and persist after an application restart,
# you have to make them persistent. There are two conditions to this:
# - The view's timeout must explicitly be set to None
# - All components MUST have a unique custom_id within the view

# Tip: It is recommended to subclass components to have the ability to pass
# variable custom_ids. See the subclassed example on how to do this.

# Tip 2: To check if your view can be persistent or not, use the View.is_persistent
# boolean property.
# If this is false, calling client.start_view with bind_to=None will fail.

bot = hikari.GatewayBot("...")
client = miru.GatewayClient(bot)

class Persistence(miru.View[miru.GW]):
    def __init__(self) -> None:
        super().__init__(timeout=None)  # Setting timeout to None

    @miru.button(label="Button 1", custom_id="my_unique_custom_id_1")
    async def button_one(self, button: miru.Button[miru.GW], ctx: miru.ViewContext[miru.GW]) -> None:
        await ctx.respond("You pressed button 1.")

    @miru.button(label="Button 2", custom_id="my_unique_custom_id_2")
    async def button_two(self, button: miru.Button[miru.GW], ctx: miru.ViewContext[miru.GW]) -> None:
        await ctx.respond("You pressed button 2.")





@bot.listen()
async def startup_views(event: hikari.StartedEvent) -> None:
    # You must reinstantiate the view in the same state it was before shutdown (e.g. same custom_ids)
    view = Persistence()
    # Restart the listener for the view, this will handle
    # all interactions for every view of type 'Persistence' globally.
    # You can also pass a message ID to bind the view to a specific message.
    # It will then only handle interactions for that message.
    client.start_view(view, bind_to=None)


@bot.listen()
async def buttons(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or webhooks
    if not event.is_human:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if me.id in event.message.user_mentions_ids:
        view = Persistence()
        await event.message.respond(
            "This is a persistent component menu, and works after bot restarts!",
            components=view,
        )
        # Persistent views do not need to be started, as starting one listener will handle all views of the same type.


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
