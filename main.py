from dotenv import load_dotenv
import os
import asyncio
import discord
import uuid

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.all()
# intents.message_content = True
# intents.typing = False
client = discord.Client(intents=intents)

pomos = {}
config = [20, 10, 2]


async def callback(cnt, pomo, message):
    if pomo.recurring == 0:
        mess = "{}作業時間{:}分経ちました\n" \
            "すべての作業が終了しました\n" \
            "お疲れさまでした"
        await message.channel.send(mess.format(pomo.title,
                                               pomo.learning_time))
        return
    if cnt == 2:
        mess = "{}休憩時間{:}分経ちました\n" \
            "作業を始めてください\n" \
            "残り{:}回です"
        await message.channel.send(mess.format(pomo.title,
                                               pomo.rest_time,
                                               pomo.recurring))
        pomo.recurring -= 1
        args = [1, pomo, message]
        asyncio.ensure_future(wrap_with_delay(pomo.learning_time, callback, args))
    elif cnt == 1:
        mess = "{}作業時間{}分経ちました\n" \
            "休憩してください"
        await message.channel.send(mess.format(pomo.title,
                                               pomo.learning_time))
        args = [cnt+1, pomo, message]
        asyncio.ensure_future(wrap_with_delay(pomo.rest_time, callback, args))


class pomodoro():
    def __init__(self, id, title, learning_time, rest_time, recurring):
        self.id = id
        self.title = title
        self.learning_time = learning_time
        self.rest_time = rest_time
        self.recurring = recurring
        self.stop = False


async def wrap_with_delay(sec, func, args):
    await asyncio.sleep(sec * 60)
    pomo = args[1]
    if pomo.stop:
        pomos.pop(pomo.id)
        return
    await func(*args)


@client.event
async def on_ready():
    print("ログインしました")


@client.event
async def on_message(message):
    global config
    if message.author.bot:
        return
    tmp = message.content.split()

    if tmp[0] == "/set":
        if len(tmp) != 4:
            mess = "引数は3つです" + \
                "/set {作業時間} {休憩時間} {繰り返し回数}"
            await message.channel.send(mess)
        else:
            config = [int(tmp[1]), int(tmp[2]), int(tmp[3])]
            mess = "作業時間を{:}分、休憩時間を{:}分、" + \
                "繰り返し回数を{:}回に設定しました"
            await message.channel.send(mess.format(tmp[1], tmp[2], tmp[3]))

    elif tmp[0] == "/start":
        id = str(uuid.uuid4())
        title = f"===== {tmp[1]} =====\n" if len(tmp) == 2 else ""
        pomo = pomodoro(id, title, config[0], config[1], config[2] - 1)
        asyncio.ensure_future(wrap_with_delay(config[0], callback, [1, pomo, message]))
        pomos[id] = pomo
        mess = "{}タイマーをスタートします\n" \
            "id : {:}\n" \
            "作業時間     : {:}分\n" \
            "休憩時間     : {:}分\n" \
            "繰り返し回数 : {:}回\n" \
            "作業頑張ってください"
        await message.channel.send(mess.format(title,
                                               id,
                                               config[0],
                                               config[1],
                                               config[2]))

    elif tmp[0] == "/cancel":
        pomo = pomos[tmp[1]]
        pomo.stop = True
        await message.channel.send(f"{pomo.title}{tmp[1]}をキャンセルしました")

    elif tmp[0] == "/help":
        mess = "/set {作業時間} {休憩時間} {繰り返し回数}\n" \
            "\tポモドーロする時間を設定します\n\n" \
            "/start {タイトル}\n" \
            "\tポモドーロを開始します\n" \
            "\tタイトルは入力なしでも可\n\n" \
            "/cancel {id}\n" \
            "\t実行中のポモドーロをキャンセルします\n\n" \
            "/help\n" \
            "\tコマンドの詳細を表示します"
        await message.channel.send(mess)

    else:
        mess = "コマンドがありません\n" \
            "コマンドを確認してください\n" \
            "/helpでコマンドを確認できます"
        if tmp[0][0] != "/":
            return
        await message.channel.send(mess)

client.run(TOKEN)
