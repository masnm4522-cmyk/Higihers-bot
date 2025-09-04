import os
import asyncio

# گرفتن توکن و آیدی از Environment Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_ID = os.getenv("BOT_ID")

if not BOT_TOKEN or not BOT_ID:
    raise ValueError("❌ لطفاً BOT_TOKEN و BOT_ID رو تنظیم کن.")

# 🎵 لیست دنس‌ها (۱ تا ۲۲۵ به صورت ساده)
DANCES = {i: f"Dance{i}" for i in range(1, 226)}

class HighriseBot:
    def __init__(self, token, bot_id):
        self.token = token
        self.bot_id = bot_id
        self.admins = []   # لیست ادمین‌ها
        self.jailed = []   # لیست افراد زندانی

    async def start(self):
        print(f"✅ بات با آیدی {self.bot_id} روشن شد.")
        await self.loop()

    async def loop(self):
        while True:
            await asyncio.sleep(10)
            print("⏳ ...بات همچنان آنلاینه")

    async def welcome_user(self, user_id):
        return (
            f"👋 خوش اومدی {user_id} 😎 دوست عزیز 🙂\n"
            f"❤️ یک قلب برات 💖\n"
            f"برای دنس، عددی بین 1 تا 225 بزن 🎵"
        )

    async def handle_command(self, user, command):
        # اگر یوزر توی زندانه (به جز free و help)
        if user in self.jailed and not command.startswith("!free") and command != "!help":
            return f"⛓️ {user} تو زندانی هستی، اجازه استفاده از دستورات رو نداری!"

        # فقط ادمین‌ها دسترسی به دستورات ویژه دارن
        if user not in self.admins and command != "!help":
            return f"⛔ {user} ادمین نیستی، نمی‌تونی استفاده کنی."

        if command == "!help":
            return (
                "📜 لیست دستورات:\n"
                "➡️ !dance <1-225>\n"
                "➡️ !danceloop <1-225>\n"
                "➡️ !wink all\n"
                "➡️ !clap all\n"
                "➡️ !heart all\n"
                "➡️ !summon @user | !summon all\n"
                "➡️ !tele @user\n"
                "➡️ !moveall room_id\n"
                "➡️ !bot\n"
                "➡️ !follow\n"
                "➡️ !loop <text> <count>\n"
                "➡️ !spam <text> <count>\n"
                "➡️ !copy @user\n"
                "➡️ !outfit @user\n"
                "➡️ !jail @user\n"
                "➡️ !free @user\n"
            )

        elif command.startswith("!dance"):
            parts = command.split()
            if len(parts) == 2 and parts[1].isdigit():
                dance_id = int(parts[1])
                if 1 <= dance_id <= 225:
                    return f"💃 {user} شروع کرد به دنس {DANCES[dance_id]}!"
                else:
                    return "⚠️ عدد دنس باید بین 1 تا 225 باشه."
            return "ℹ️ استفاده درست: !dance <شماره>"

        elif command.startswith("!danceloop"):
            parts = command.split()
            if len(parts) == 2 and parts[1].isdigit():
                dance_id = int(parts[1])
                if 1 <= dance_id <= 225:
                    return f"🔁 دنس {DANCES[dance_id]} در حال تکرار تا گفتن stop!"
                else:
                    return "⚠️ عدد دنس باید بین 1 تا 225 باشه."
            else:
                return "⚠️ استفاده درست: !danceloop <عدد>"

        elif command == "stop":
            return f"⏹️ {user} دنس یا اسپم رو متوقف کرد."

        elif command.startswith("!wink"):
            if "all" in command:
                return "😉 کل اتاق رو چشمک زد!"
            else:
                return f"😉 {user} چشمک زد!"

        elif command.startswith("!clap"):
            if "all" in command:
                return "👏 کل اتاق رو دست زد!"
            else:
                return f"👏 {user} دست زد!"

        elif command.startswith("!heart"):
            if "all" in command:
                return "❤️ برای همه توی اتاق قلب فرستاد!"
            else:
                return f"❤️ {user} قلب داد!"

        elif command.startswith("!summon"):
            parts = command.split()
            if len(parts) == 2:
                if parts[1] == "all":
                    return "📍 همه بازیکن‌ها احضار شدن به مکان تو!"
                elif parts[1].startswith("@"):
                    target = parts[1]
                    return f"📍 {target} احضار شد به مکان {user}!"
                else:
                    return "⚠️ استفاده درست: !summon @username یا !summon all"
            else:
                return "⚠️ استفاده درست: !summon @username یا !summon all"

        elif command.startswith("!tele"):
            parts = command.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target = parts[1]
                return f"🚀 {user} تلپورت شد به مکان {target}!"
            else:
                return "⚠️ استفاده درست: !tele @username"

        elif command.startswith("!moveall"):
            parts = command.split()
            if len(parts) == 2:
                room = parts[1]
                return f"🚪 همه بازیکن‌ها منتقل شدن به روم {room}!"
            else:
                return "⚠️ استفاده درست: !moveall room_id"

        elif command.startswith("!spam"):
            parts = command.split(maxsplit=2)
            if len(parts) == 3 and parts[2].isdigit():
                text = parts[1]
                count = int(parts[2])
                return (text + " ") * count
            else:
                return "⚠️ استفاده درست: !spam <متن> <تعداد>"

        elif command.startswith("!loop"):
            parts = command.split(maxsplit=2)
            if len(parts) == 3 and parts[2].isdigit():
                text = parts[1]
                count = int(parts[2])
                return (text + " ") * count
            else:
                return "⚠️ استفاده درست: !loop <متن> <تعداد>"

        elif command.startswith("!copy"):
            parts = command.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target = parts[1]
                return f"👕 {user} لباس {target} رو کپی کرد!"
            else:
                return "⚠️ استفاده درست: !copy @username"

        elif command.startswith("!outfit"):
            parts = command.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target = parts[1]
                return f"👗 بات لباس {target} رو پوشید!"
            else:
                return "⚠️ استفاده درست: !outfit @username"

        elif command == "!bot":
            return f"🤖 بات اومد پیش {user}!"

        elif command == "!follow":
            return f"🚶‍♂️ بات شروع کرد به دنبال کردن {user}!"

        # 📍 زندان و آزادی
        elif command.startswith("!jail"):
            parts = command.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target = parts[1]
                if target not in self.jailed:
                    self.jailed.append(target)
                    return f"⛓️ {target} به زندان فرستاده شد!"
                else:
                    return f"⚠️ {target} همین الانش هم توی زندانه."
            else:
                return "⚠️ استفاده درست: !jail @username"

        elif command.startswith("!free"):
            parts = command.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target = parts[1]
                if target in self.jailed:
                    self.jailed.remove(target)
                    return f"✅ {target} از زندان آزاد شد!"
                else:
                    return f"⚠️ {target} اصلاً زندانی نبود."
            else:
                return "⚠️ استفاده درست: !free @username"

        else:
            return f"❌ دستور {command} ناشناخته‌ست."


# اجرای بات
async def main():
    bot = HighriseBot(BOT_TOKEN, BOT_ID)

    # اضافه کردن یک ادمین تستی (آیدی خودتو اینجا بذار)
    bot.admins.append("@Sogoli__")

    print("🚀 ...در حال روشن شدن بات")
    await bot.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 بات خاموش شد.")
