import ast
from datetime import datetime

from bs4 import BeautifulSoup
from disnake import ApplicationCommandInteraction
from loguru import logger
import disnake
from disnake.ext.commands import Cog, Param, slash_command
from requests import Session

from bot.misc.constants import online_url, headers, emojiCuteSad
from bot.misc.penguin import Penguin
from bot.misc.utils import getPenguinFromInter, getPenguinOrNoneFromUserId, transferCoinsAndReturnStatus


class UserCommands(Cog):
    def __init__(self, bot):
        self.bot = bot

        logger.info(f"Loaded {len(self.get_application_commands())} public users app commands")

    @slash_command(name="ilyash", description=":D")
    async def ilyash(self, inter: ApplicationCommandInteraction):
        await inter.send(f"Теперь вы пешка иляша!")

    @slash_command(name="card", description="Показывает полезную информацию о твоём аккаунте")
    async def card(self, inter: ApplicationCommandInteraction,
                   user: disnake.User = Param(default=None, description='Пользователь, чью карточку нужно показать')):
        if user:
            p = await getPenguinOrNoneFromUserId(user.id)
            if p is None:
                return await inter.send(f"Мы не нашли пингвина у указанного вами+ пользователя.", ephemeral=True)
        else:
            p: Penguin = await getPenguinFromInter(inter)

        if p.get_custom_attribute("mood") and p.get_custom_attribute("mood") != " ":
            mood = f'*{p.get_custom_attribute("mood")}*'.replace("\n", " ")
        else:
            mood = None

        embed = disnake.Embed(title=p.safe_name(),
                              description=mood,
                              color=disnake.Color(0x035BD1))
        embed.set_thumbnail(url=f"https://play.cpps.app/avatar/{p.id}/cp?size=600")
        embed.add_field(name="ID", value=p.id)
        embed.add_field(name="Проведено в игре", value=f'{p.minutes_played} минут')
        embed.add_field(name="Монеты", value=p.coins)
        embed.add_field(name="Марки", value=len(p.stamps) + p.count_epf_awards())
        embed.add_field(name="Возраст пингвина", value=f"{(datetime.now() - p.registration_date).days} дней")
        embed.add_field(name="Сотрудник", value="Да" if p.moderator else "Нет")
        await inter.send(embed=embed)

    @slash_command(name="pay", description="Перевести свои монеты другому игроку")
    async def pay(self, inter: ApplicationCommandInteraction,
                  receiver: disnake.Member = Param(description='Получатель'),
                  amount: int = Param(description='Количество монет'),
                  message: str = Param(default=None, description='Сообщение получателю')):
        p: Penguin = await getPenguinFromInter(inter)
        r: Penguin = await getPenguinOrNoneFromUserId(receiver.id)
        if r is None:
            return await inter.send(f"Мы не нашли пингвина у указанного вами пользователя.", ephemeral=True)

        statusDict = await transferCoinsAndReturnStatus(p, r, amount, message)
        if statusDict["code"] == 400:
            await inter.send(statusDict["message"], ephemeral=True)

        await inter.send(statusDict["message"])

    @slash_command(name="online", description="Показывает количество игроков которые сейчас онлайн")
    async def online(self, inter: ApplicationCommandInteraction):
        with Session() as s:
            s.headers.update(headers)
            response = s.get(online_url)
            soup = BeautifulSoup(response.text, "html.parser")

        online = int(ast.literal_eval(soup.text)[0]['3104'])
        if online == 0:
            textMessage = f"В нашей игре сейчас никого нет {emojiCuteSad}"
        else:
            textMessage = f"В нашей игре сейчас `{online}` человек/а онлайн"
        await inter.send(textMessage)


def setup(bot):
    bot.add_cog(UserCommands(bot))
