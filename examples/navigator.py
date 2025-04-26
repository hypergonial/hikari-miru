import hikari

import miru
from miru.ext import nav


class MyNavButton(nav.NavButton):
    # This is how you can create your own navigator button
    # The extension also comes with the following nav buttons built-in:
    #
    # FirstButton - Goes to the first page
    # PrevButton - Goes to previous page
    # IndicatorButton - Indicates current page number
    # StopButton - Stops the navigator session and disables all buttons
    # NextButton - Goes to next page
    # LastButton - Goes to the last page

    async def callback(self, context: miru.ViewContext) -> None:
        await context.respond("You clicked me!", flags=hikari.MessageFlag.EPHEMERAL)

    async def before_page_change(self) -> None:
        # This function is called before the new page is sent by
        # NavigatorView.send_page()
        self.label = f"Page: {self.view.current_page + 1}"


bot = hikari.GatewayBot("...")
client = miru.Client(bot)


@bot.listen()
async def navigator(event: hikari.GuildMessageCreateEvent) -> None:
    # Do not process messages from bots or webhooks
    if not event.is_human:
        return

    me = bot.get_me()

    # If the bot is mentioned
    if event.message.user_mentions_ids and me and me.id in event.message.user_mentions_ids:
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")

        # You can also pass a Page object to the navigator to create customized page payloads.
        page = nav.Page(content="I'm the last page!", embed=hikari.Embed(title="I also have an embed!"))

        # 'pages' should be a list that contains 'str', 'hikari.Embed', and 'nav.Page' objects.
        pages = ["I'm the first page!", embed, page]

        # Define our navigator and pass in our list of pages
        navigator: nav.NavigatorView = nav.NavigatorView(pages=pages)

        # Note: You can also send the navigator to an interaction or miru context
        # See the documentation of MessageBuilder for more information
        builder = await navigator.build_response_async(client)
        await builder.send_to_channel(event.channel_id)
        client.start_view(navigator)

    # Otherwise we annoy everyone with our custom navigator instead
    else:
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
        pages = ["I'm a customized navigator!", embed, "I'm the last page!"]
        # Define our custom buttons for this navigator
        # All navigator items MUST subclass NavItem
        # All miru items have a 'Nav' counterpart
        buttons: list[nav.NavItem] = [
            nav.PrevButton(),
            nav.StopButton(),
            nav.NextButton(),
            MyNavButton(label="Page: 1", row=1),
        ]
        # Pass our list of NavButton to the navigator
        navigator = nav.NavigatorView(pages=pages, items=buttons)
        builder = await navigator.build_response_async(client)
        await builder.send_to_channel(event.channel_id)
        client.start_view(navigator)


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
