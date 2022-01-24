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

    async def callback(self, interaction: miru.Interaction) -> None:
        await interaction.send_message("You clicked me!", flags=hikari.MessageFlag.EPHEMERAL)

    async def before_page_change(self) -> None:
        # This function is called before the new page is sent by
        # NavigatorView.send_page()
        self.label = f"Page: {self.view.current_page+1}"

bot = hikari.GatewayBot("...")

@bot.listen()
async def navigator(event: hikari.GuildMessageCreateEvent) -> None:

    # Do not process messages from bots or empty messages
    if event.is_bot or not event.content:
        return

    if event.content.startswith("mirunav"):
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
        pages = ["I'm the first page!", embed, "I'm the last page!"]
        # Define our navigator and pass in our list of pages
        navigator = nav.NavigatorView(event.app, pages=pages)
        # You may also pass an interaction object to this function
        await navigator.send(channel_id=event.channel_id)
    
    elif event.content.startswith("mirucustom"):
        embed = hikari.Embed(title="I'm the second page!", description="Also an embed!")
        pages = ["I'm a customized navigator!", embed, "I'm the last page!"]
        # Define our custom buttons for this navigator
        # All navigator buttons MUST subclass NavButton
        buttons = [nav.PrevButton(), nav.StopButton(), nav.NextButton(), MyNavButton(label="Page: 1", row=1)]
        # Pass our list of NavButton to the navigator
        navigator = nav.NavigatorView(event.app, pages=pages, buttons=buttons)

        await navigator.send(channel_id=event.channel_id)


bot.run()