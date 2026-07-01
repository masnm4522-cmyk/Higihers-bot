import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from serve2 import AdvancedBot as _BaseBot
from highrise import User, Position
from highrise.__main__ import BotDefinition
from asyncio import sleep, create_task, CancelledError
from datetime import datetime
import json
import logging
import random
import aiohttp

logger = logging.getLogger(__name__)

EXT_CONFIG_FILE = "ext_config.json"
EXT_DEFAULT_CONFIG = {
    "bot_home": None,
    "floors": {},
    "loop_messages": [
        "سلام عزیزم برای زدن دنس 1 تا 222 تایپ کن 😊",
        "برای راهنما !help بزنید 🔥"
    ],
    "loop_interval": 300,
    "loop_enabled": True,
    "bot_silent": False,
    "welcome_dm": True,
    "welcome_dm_message": "سلام {username} عزیز! 🌸 خوش اومدی. برای دیدن دستورات !help بزن.",
    "vip_temp_list": {},
    "warn_records": {},
    "banned_users": [],
    "welcome_dm_enabled": True,
    "welcome_dm_message": "سلام {username} عزیز! 🌸 خوش اومدی. برای دیدن دستورات !help بزن."
}


class ExtendedBot(_BaseBot):

    def __init__(self):
        super().__init__()
        self.ext_config = self._load_ext_config()
        self.bot_home_position = None
        self.bot_home_task = None
        self.loop_task = None
        self._loop_index = 0
        self._bot_silent = self.ext_config.get("bot_silent", False)
        self._lottery_active = False
        self._lottery_participants = []
        self._lottery_prize = ""
        self._quiz_active = False
        self._quiz_answer = ""
        self._quiz_asked_by = ""
        self._countdown_task = None
        self._tempvip_tasks = {}
        self._visitors_today = {}
        self._bot_dance_task = None
        self._bot_dance_emote = None
        self._ext_commands = {
            "!bot": self._cmd_bot,
            "!botfree": self._cmd_botfree,
            "!sethome": self._cmd_sethome,
            "!home": self._cmd_home,
            "!delhome": self._cmd_delhome,
            "!setfloor": self._cmd_setfloor,
            "!delfloor": self._cmd_delfloor,
            "!floors": self._cmd_floors,
            "!setloop": self._cmd_setloop,
            "!loopon": self._cmd_loopon,
            "!loopoff": self._cmd_loopoff,
            "!pos": self._cmd_pos,
            "!lottery": self._cmd_lottery,
            "!join": self._cmd_join,
            "!quiz": self._cmd_quiz,
            "!report": self._cmd_report,
            "!tempvip": self._cmd_tempvip,
            "!untempvip": self._cmd_untempvip,
            "!visitors": self._cmd_visitors,
            "!botoff": self._cmd_botoff,
            "!boton": self._cmd_boton,
            "!countdown": self._cmd_countdown,
            "!top": self._cmd_top,
            "!dm": self._cmd_dm,
            "!exthelp": self._cmd_exthelp,
            "!botdance": self._cmd_botdance,
            "!dancereset": self._cmd_dancereset,
            "!reset": self._cmd_reset,
            "!setroom": self._cmd_setroom,
            "!roominfo": self._cmd_roominfo,
            "!warn": self._cmd_warn,
            "!warns": self._cmd_warns,
            "!clearwarn": self._cmd_clearwarn,
            "!schedule": self._cmd_schedule,
            "!stats": self._cmd_stats,
            "!alldance": self._cmd_alldance,
            "!setwelcome": self._cmd_setwelcome,
            "!welcomeon": self._cmd_welcomeon,
            "!welcomeoff": self._cmd_welcomeoff,
            "!help": self._cmd_help_override,
            "!restart": self._cmd_restart,
            "!settoken": self._cmd_settoken,
        }

    # ─── کانفیگ اضافی ──────────────────────────────────────────────

    def _load_ext_config(self):
        try:
            if os.path.exists(EXT_CONFIG_FILE):
                with open(EXT_CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                merged = EXT_DEFAULT_CONFIG.copy()
                merged.update(data)
                return merged
        except Exception as e:
            logger.error(f"خطا در خواندن ext_config: {e}")
        return EXT_DEFAULT_CONFIG.copy()

    def _save_ext_config(self):
        try:
            with open(EXT_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.ext_config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"خطا در ذخیره ext_config: {e}")

    def _is_admin(self, user: User) -> bool:
        return user.username.lower() in self.config.get("admin_usernames", [])

    # ─── on_start ──────────────────────────────────────────────────

    async def on_start(self, session_metadata):
        await super().on_start(session_metadata)
        # لغو دنس پیش‌فرض والد و شروع دنس سفارشی
        if self.user_id and self.user_id in self.dance_tasks:
            self.dance_tasks[self.user_id].cancel()
        saved_dance = self.ext_config.get("bot_dance_emote", "dance-floss")
        self._bot_dance_emote = saved_dance
        self._bot_dance_task = create_task(self._bot_dance_loop())

        saved = self.ext_config.get("bot_home")
        if saved:
            self.bot_home_position = Position(x=saved["x"], y=saved["y"], z=saved["z"])
            self.bot_home_task = create_task(self._bot_home_loop())
            logger.info(f"قفل خونه بات از کانفیگ بارگذاری شد: {saved}")
        if self.ext_config.get("loop_enabled", True):
            self.loop_task = create_task(self._announcement_loop_ext())

    # ─── on_user_join ───────────────────────────────────────────────

    async def on_user_join(self, user: User, position: Position):
        await super().on_user_join(user, position)
        today = datetime.now().strftime("%Y-%m-%d")
        self._visitors_today.setdefault(today, set()).add(user.username)
        if self.ext_config.get("welcome_dm", True):
            try:
                dm_text = self.ext_config.get(
                    "welcome_dm_message",
                    "سلام {username} عزیز! خوش اومدی 🌸"
                ).replace("{username}", user.username)
                await self.highrise.send_message(
                    conversation_id="",
                    message=dm_text,
                    username=user.username
                )
            except Exception as e:
                logger.error(f"خطا در ارسال DM خوش‌آمد به {user.username}: {e}")

    # ─── on_chat ───────────────────────────────────────────────────

    async def on_chat(self, user: User, message: str):
        if self._bot_silent:
            pass

        msg = message.strip()
        msg_lower = msg.lower()

        cmd = msg_lower.split()[0] if msg_lower.startswith("!") else None
        if cmd and cmd in self._ext_commands:
            await self._ext_commands[cmd](user, msg)
            return

        if self._quiz_active and msg_lower == self._quiz_answer.lower():
            self._quiz_active = False
            pts = self.user_scores.get(user.username.lower(), 0) + 50
            self.user_scores[user.username.lower()] = pts
            await self.highrise.chat(
                f"🎉 @{user.username} جواب درست داد! +50 امتیاز\n"
                f"جواب: {self._quiz_answer}"
            )
            return

        if msg_lower in self.ext_config.get("floors", {}):
            floor = self.ext_config["floors"][msg_lower]
            dest = Position(x=floor["x"], y=floor["y"], z=floor["z"])
            try:
                await self.highrise.teleport(user_id=user.id, dest=dest)
            except Exception as e:
                await self.highrise.chat(f"❌ خطا در رفتن به طبقه: {e}")
            return

        await super().on_chat(user, message)

    # ══════════════════════════════════════════════════════════════
    # سیستم دنس بات 💃
    # ══════════════════════════════════════════════════════════════

    async def _bot_dance_loop(self):
        try:
            while True:
                if self._bot_dance_emote and self.user_id:
                    try:
                        duration = self.emote_durations.get(self._bot_dance_emote, 9.0)
                        await self.highrise.send_emote(self._bot_dance_emote, self.user_id)
                        await sleep(duration)
                    except Exception as e:
                        logger.error(f"خطا در دنس بات: {e}")
                        await sleep(5)
                else:
                    await sleep(5)
        except CancelledError:
            logger.info("لوپ دنس بات لغو شد.")

    def _resolve_emote(self, name_or_number: str):
        key = name_or_number.lower()
        # اگه توی دیکشنری emotes باشه (شماره یا اسم مستعار)
        if key in self.emotes:
            return self.emotes[key]
        # اگه مستقیم اسم emote باشه
        if key in self.emote_durations:
            return key
        # اگه با پیشوندهای معمول شروع بشه
        for prefix in ("dance-", "emote-", "idle-", "idle_", "emoji-", "sit-"):
            if key.startswith(prefix):
                return key
        return None

    # ─── لوپ قفل موقعیت بات ───────────────────────────────────────

    async def _bot_home_loop(self):
        try:
            while True:
                await sleep(5)
                if self.bot_home_position and self.user_id:
                    try:
                        await self.highrise.teleport(user_id=self.user_id, dest=self.bot_home_position)
                    except Exception as e:
                        logger.error(f"خطا در قفل موقعیت بات: {e}")
        except CancelledError:
            logger.info("لوپ قفل موقعیت بات لغو شد.")

    # ─── لوپ اعلان اضافی ──────────────────────────────────────────

    async def _announcement_loop_ext(self):
        try:
            while True:
                interval = self.ext_config.get("loop_interval", 300)
                await sleep(interval)
                if not self.ext_config.get("loop_enabled", True):
                    continue
                if self._bot_silent:
                    continue
                messages = self.ext_config.get("loop_messages", [])
                if messages:
                    msg = messages[self._loop_index % len(messages)]
                    self._loop_index += 1
                    await self.highrise.chat(msg)
        except CancelledError:
            logger.info("لوپ اعلان اضافی لغو شد.")
        except Exception as e:
            logger.error(f"خطا در لوپ اعلان: {e}")

    # ══════════════════════════════════════════════════════════════
    # سیستم قفل موقعیت بات
    # ══════════════════════════════════════════════════════════════

    async def _cmd_bot(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split()
        try:
            dest = None
            if len(parts) == 2 and parts[1].lower() == "here":
                pos = self.user_positions.get(user.username.lower())
                if not pos:
                    await self.highrise.chat("❌ موقعیت شما پیدا نشد، یه کم حرکت کن.")
                    return
                dest = pos
            elif len(parts) == 4:
                dest = Position(x=float(parts[1]), y=float(parts[2]), z=float(parts[3]))
            else:
                await self.highrise.chat("فرمت: !bot here | !bot x y z")
                return
            await self.highrise.teleport(user_id=self.user_id, dest=dest)
            self.bot_home_position = dest
            self.ext_config["bot_home"] = {"x": dest.x, "y": dest.y, "z": dest.z}
            self._save_ext_config()
            if not self.bot_home_task or self.bot_home_task.done():
                self.bot_home_task = create_task(self._bot_home_loop())
            await self.highrise.chat(
                f"📍 بات قفل شد! x={round(dest.x,1)} y={round(dest.y,1)} z={round(dest.z,1)} | آزاد: !botfree"
            )
        except ValueError:
            await self.highrise.chat("❌ مختصات باید عدد باشن!")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا: {e}")

    async def _cmd_botfree(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        self.bot_home_position = None
        self.ext_config["bot_home"] = None
        self._save_ext_config()
        if self.bot_home_task and not self.bot_home_task.done():
            self.bot_home_task.cancel()
            self.bot_home_task = None
        await self.highrise.chat("🔓 قفل موقعیت بات برداشته شد!")

    # ══════════════════════════════════════════════════════════════
    # سیستم خونه بات
    # ══════════════════════════════════════════════════════════════

    async def _cmd_sethome(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        pos = self.user_positions.get(user.username.lower())
        if not pos:
            await self.highrise.chat("❌ موقعیت شما پیدا نشد.")
            return
        self.ext_config["bot_home"] = {"x": pos.x, "y": pos.y, "z": pos.z}
        self.bot_home_position = pos
        self._save_ext_config()
        if not self.bot_home_task or self.bot_home_task.done():
            self.bot_home_task = create_task(self._bot_home_loop())
        await self.highrise.chat(
            f"🏠 خونه بات ذخیره شد! x={round(pos.x,1)} y={round(pos.y,1)} z={round(pos.z,1)}"
        )

    async def _cmd_home(self, user: User, message: str):
        saved = self.ext_config.get("bot_home")
        if not saved:
            await self.highrise.chat("❌ خونه‌ای ذخیره نشده. اول !sethome بزن.")
            return
        dest = Position(x=saved["x"], y=saved["y"], z=saved["z"])
        try:
            await self.highrise.teleport(user_id=self.user_id, dest=dest)
            await self.highrise.chat("🏠 بات به خونه برگشت!")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا: {e}")

    async def _cmd_delhome(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        self.ext_config["bot_home"] = None
        self.bot_home_position = None
        self._save_ext_config()
        if self.bot_home_task and not self.bot_home_task.done():
            self.bot_home_task.cancel()
            self.bot_home_task = None
        await self.highrise.chat("🗑 خونه بات پاک شد.")

    # ══════════════════════════════════════════════════════════════
    # سیستم طبقه
    # ══════════════════════════════════════════════════════════════

    async def _cmd_setfloor(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split()
        if len(parts) < 2:
            await self.highrise.chat("فرمت: !setfloor اسم | !setfloor اسم x y z")
            return
        name = parts[1].lower()
        if len(parts) == 5:
            try:
                x, y, z = float(parts[2]), float(parts[3]), float(parts[4])
            except ValueError:
                await self.highrise.chat("❌ مختصات باید عدد باشن!")
                return
        else:
            pos = self.user_positions.get(user.username.lower())
            if not pos:
                await self.highrise.chat("❌ موقعیت شما پیدا نشد، یه کم حرکت کن.")
                return
            x, y, z = pos.x, pos.y, pos.z
        self.ext_config.setdefault("floors", {})[name] = {"x": x, "y": y, "z": z}
        self._save_ext_config()
        await self.highrise.chat(
            f"✅ طبقه '{name}' ذخیره شد!\n"
            f"x={round(x,1)} y={round(y,1)} z={round(z,1)}\n"
            f"کاربرا '{name}' رو تایپ کنن تا برن اونجا."
        )

    async def _cmd_delfloor(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split()
        if len(parts) < 2:
            await self.highrise.chat("فرمت: !delfloor اسم")
            return
        name = parts[1].lower()
        floors = self.ext_config.get("floors", {})
        if name not in floors:
            await self.highrise.chat(f"❌ طبقه '{name}' وجود نداره.")
            return
        del floors[name]
        self._save_ext_config()
        await self.highrise.chat(f"🗑 طبقه '{name}' پاک شد.")

    async def _cmd_floors(self, user: User, message: str):
        floors = self.ext_config.get("floors", {})
        if not floors:
            await self.highrise.chat("هیچ طبقه‌ای ذخیره نشده.")
            return
        lines = ["📋 طبقه‌های موجود:"]
        for name, p in floors.items():
            lines.append(f"• {name}")
        await self.highrise.chat("\n".join(lines))

    # ══════════════════════════════════════════════════════════════
    # سیستم لوپ اعلان
    # ══════════════════════════════════════════════════════════════

    async def _cmd_setloop(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split(maxsplit=2)
        if len(parts) < 2:
            await self.highrise.chat(
                "📢 دستورات لوپ:\n"
                "!setloop دقیقه — تنظیم بازه\n"
                "!setloop add پیام — اضافه کردن پیام\n"
                "!setloop clear — پاک کردن همه\n"
                "!setloop status — وضعیت\n"
                "!loopon / !loopoff"
            )
            return
        sub = parts[1].lower()
        if sub == "status":
            msgs = self.ext_config.get("loop_messages", [])
            interval = self.ext_config.get("loop_interval", 300)
            enabled = self.ext_config.get("loop_enabled", True)
            await self.highrise.chat(
                f"📊 وضعیت لوپ:\n"
                f"{'فعال ✅' if enabled else 'غیرفعال ❌'}\n"
                f"بازه: {interval//60} دقیقه\n"
                f"تعداد پیام: {len(msgs)}"
            )
        elif sub == "clear":
            self.ext_config["loop_messages"] = []
            self._save_ext_config()
            await self.highrise.chat("🗑 همه پیام‌های لوپ پاک شدن.")
        elif sub == "add":
            if len(parts) < 3:
                await self.highrise.chat("پیام رو بنویس: !setloop add متن پیام")
                return
            self.ext_config.setdefault("loop_messages", []).append(parts[2])
            self._save_ext_config()
            await self.highrise.chat(f"✅ پیام اضافه شد. ({len(self.ext_config['loop_messages'])} پیام)")
        else:
            try:
                minutes = int(parts[1])
                if minutes < 1:
                    raise ValueError
                self.ext_config["loop_interval"] = minutes * 60
                self._save_ext_config()
                await self.highrise.chat(f"✅ بازه لوپ: {minutes} دقیقه")
            except ValueError:
                await self.highrise.chat("❌ عدد دقیقه باید مثبت باشه!")

    async def _cmd_loopon(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        self.ext_config["loop_enabled"] = True
        self._save_ext_config()
        if not self.loop_task or self.loop_task.done():
            self.loop_task = create_task(self._announcement_loop_ext())
        await self.highrise.chat("✅ لوپ اعلان روشن شد.")

    async def _cmd_loopoff(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        self.ext_config["loop_enabled"] = False
        self._save_ext_config()
        if self.loop_task and not self.loop_task.done():
            self.loop_task.cancel()
            self.loop_task = None
        await self.highrise.chat("🔇 لوپ اعلان خاموش شد.")

    # ══════════════════════════════════════════════════════════════
    # سیستم موقعیت
    # ══════════════════════════════════════════════════════════════

    async def _cmd_pos(self, user: User, message: str):
        pos = self.user_positions.get(user.username.lower())
        if not pos:
            await self.highrise.chat("❌ موقعیت شما پیدا نشد.")
            return
        await self.highrise.chat(
            f"📍 @{user.username}\n"
            f"x={round(pos.x,2)} y={round(pos.y,2)} z={round(pos.z,2)}\n"
            f"برای ساخت طبقه: !setfloor اسم"
        )

    # ══════════════════════════════════════════════════════════════
    # سیستم لاتاری 🎰
    # !lottery start جایزه — شروع
    # !lottery end — قرعه‌کشی و اعلام برنده
    # !lottery cancel — لغو
    # !join — شرکت در لاتاری
    # ══════════════════════════════════════════════════════════════

    async def _cmd_lottery(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split(maxsplit=2)
        sub = parts[1].lower() if len(parts) > 1 else ""

        if sub == "start":
            if self._lottery_active:
                await self.highrise.chat("❌ یه لاتاری در جریانه! اول !lottery end یا !lottery cancel بزن.")
                return
            prize = parts[2] if len(parts) > 2 else "جایزه ویژه"
            self._lottery_active = True
            self._lottery_participants = []
            self._lottery_prize = prize
            await self.highrise.chat(
                f"🎰 لاتاری شروع شد!\n"
                f"🎁 جایزه: {prize}\n"
                f"برای شرکت !join بزنید!"
            )

        elif sub == "end":
            if not self._lottery_active:
                await self.highrise.chat("❌ هیچ لاتاری فعالی نیست.")
                return
            self._lottery_active = False
            if not self._lottery_participants:
                await self.highrise.chat("😔 هیچکس شرکت نکرد!")
                return
            winner = random.choice(self._lottery_participants)
            self.user_scores[winner.lower()] = self.user_scores.get(winner.lower(), 0) + 100
            await self.highrise.chat(
                f"🎉 قرعه‌کشی انجام شد!\n"
                f"🏆 برنده: @{winner}\n"
                f"🎁 جایزه: {self._lottery_prize}\n"
                f"تعداد شرکت‌کننده: {len(self._lottery_participants)}"
            )
            self._lottery_participants = []

        elif sub == "cancel":
            if not self._lottery_active:
                await self.highrise.chat("❌ هیچ لاتاری فعالی نیست.")
                return
            self._lottery_active = False
            self._lottery_participants = []
            await self.highrise.chat("🚫 لاتاری لغو شد.")

        elif sub == "list":
            if not self._lottery_active:
                await self.highrise.chat("❌ هیچ لاتاری فعالی نیست.")
                return
            if not self._lottery_participants:
                await self.highrise.chat("هنوز کسی شرکت نکرده.")
                return
            await self.highrise.chat(
                f"👥 شرکت‌کنندگان ({len(self._lottery_participants)}):\n" +
                ", ".join(f"@{u}" for u in self._lottery_participants[:15])
            )
        else:
            await self.highrise.chat(
                "🎰 دستورات لاتاری:\n"
                "!lottery start جایزه\n"
                "!lottery end\n"
                "!lottery cancel\n"
                "!lottery list"
            )

    async def _cmd_join(self, user: User, message: str):
        if not self._lottery_active:
            await self.highrise.chat("❌ لاتاری فعالی نیست.")
            return
        if user.username in self._lottery_participants:
            await self.highrise.chat(f"❌ @{user.username} قبلاً شرکت کردی!")
            return
        self._lottery_participants.append(user.username)
        await self.highrise.chat(
            f"✅ @{user.username} وارد لاتاری شد! ({len(self._lottery_participants)} نفر)"
        )

    # ══════════════════════════════════════════════════════════════
    # سیستم Quiz ❓
    # !quiz سوال | جواب — ادمین سوال می‌ذاره
    # هر کسی جواب درست بزنه +50 امتیاز می‌گیره
    # ══════════════════════════════════════════════════════════════

    async def _cmd_quiz(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه سوال بذاره.")
            return
        parts = message.strip().split("|", 1)
        if len(parts) < 2:
            if self._quiz_active:
                await self.highrise.chat(
                    f"❓ سوال فعلی در جریانه!\n"
                    f"سوال رو با !quiz cancel لغو کن یا صبر کن کسی جواب بده."
                )
            else:
                await self.highrise.chat("فرمت: !quiz سوال | جواب\nمثال: !quiz پایتخت ایران چیه | تهران")
            return

        question_part = parts[0].replace("!quiz", "").strip()
        answer = parts[1].strip()

        if not question_part or not answer:
            await self.highrise.chat("فرمت: !quiz سوال | جواب")
            return

        if message.strip().split()[1].lower() == "cancel":
            self._quiz_active = False
            self._quiz_answer = ""
            await self.highrise.chat("🚫 سوال لغو شد.")
            return

        self._quiz_active = True
        self._quiz_answer = answer
        self._quiz_asked_by = user.username
        await self.highrise.chat(
            f"❓ سوال از @{user.username}:\n"
            f"{question_part}\n"
            f"اولین نفری که جواب درست بزنه +50 امتیاز می‌گیره! 🏆"
        )

    # ══════════════════════════════════════════════════════════════
    # سیستم گزارش 🚨
    # !report @username دلیل
    # ══════════════════════════════════════════════════════════════

    async def _cmd_report(self, user: User, message: str):
        parts = message.strip().split(maxsplit=2)
        if len(parts) < 3:
            await self.highrise.chat("فرمت: !report @username دلیل")
            return
        target = parts[1].lstrip("@")
        reason = parts[2]
        now = datetime.now().strftime("%H:%M")
        await self.highrise.chat(
            f"🚨 گزارش دریافت شد!\n"
            f"از: @{user.username}\n"
            f"کاربر: @{target}\n"
            f"دلیل: {reason}\n"
            f"⏰ {now} — ادمین بررسی می‌کنه."
        )
        try:
            admins = self.config.get("admin_usernames", [])
            if admins:
                dm_text = (
                    f"🚨 گزارش جدید!\n"
                    f"از @{user.username} درباره @{target}:\n"
                    f"دلیل: {reason}"
                )
                await self.highrise.send_message(
                    conversation_id="",
                    message=dm_text,
                    username=admins[0]
                )
        except Exception as e:
            logger.error(f"خطا در ارسال DM گزارش: {e}")

    # ══════════════════════════════════════════════════════════════
    # سیستم VIP موقت ⭐
    # !tempvip @username دقیقه
    # ══════════════════════════════════════════════════════════════

    async def _cmd_tempvip(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split()
        if len(parts) < 3:
            await self.highrise.chat("فرمت: !tempvip @username دقیقه")
            return
        target = parts[1].lstrip("@").lower()
        try:
            minutes = int(parts[2])
            if minutes < 1:
                raise ValueError
        except ValueError:
            await self.highrise.chat("❌ دقیقه باید عدد مثبت باشه!")
            return

        vips = self.config.setdefault("vip_usernames", [])
        if target not in vips:
            vips.append(target)
            self.save_config()

        await self.highrise.chat(
            f"⭐ @{target} برای {minutes} دقیقه VIP شد!"
        )

        async def _remove_vip():
            try:
                await sleep(minutes * 60)
                if target in self.config.get("vip_usernames", []):
                    self.config["vip_usernames"].remove(target)
                    self.save_config()
                await self.highrise.chat(f"⌛ VIP موقت @{target} به پایان رسید.")
                self._tempvip_tasks.pop(target, None)
            except CancelledError:
                pass

        if target in self._tempvip_tasks and not self._tempvip_tasks[target].done():
            self._tempvip_tasks[target].cancel()
        self._tempvip_tasks[target] = create_task(_remove_vip())

    async def _cmd_untempvip(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split()
        if len(parts) < 2:
            await self.highrise.chat("فرمت: !untempvip @username")
            return
        target = parts[1].lstrip("@").lower()
        if target in self._tempvip_tasks and not self._tempvip_tasks[target].done():
            self._tempvip_tasks[target].cancel()
            self._tempvip_tasks.pop(target, None)
        vips = self.config.get("vip_usernames", [])
        if target in vips:
            vips.remove(target)
            self.save_config()
        await self.highrise.chat(f"❌ VIP @{target} برداشته شد.")

    # ══════════════════════════════════════════════════════════════
    # سیستم بازدیدکنندگان 👥
    # ══════════════════════════════════════════════════════════════

    async def _cmd_visitors(self, user: User, message: str):
        today = datetime.now().strftime("%Y-%m-%d")
        visitors = self._visitors_today.get(today, set())
        if not visitors:
            await self.highrise.chat("امروز هنوز کسی نیومده.")
            return
        await self.highrise.chat(
            f"👥 بازدیدکنندگان امروز ({len(visitors)} نفر):\n" +
            ", ".join(f"@{u}" for u in list(visitors)[:20])
        )

    # ══════════════════════════════════════════════════════════════
    # سیستم خاموش/روشن بات 🔇
    # ══════════════════════════════════════════════════════════════

    async def _cmd_botoff(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        self._bot_silent = True
        self.ext_config["bot_silent"] = True
        self._save_ext_config()
        await self.highrise.chat("🔇 بات وارد مد سکوت شد.")

    async def _cmd_boton(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        self._bot_silent = False
        self.ext_config["bot_silent"] = False
        self._save_ext_config()
        await self.highrise.chat("🔊 بات از مد سکوت خارج شد!")

    # ══════════════════════════════════════════════════════════════
    # سیستم Countdown ⏳
    # !countdown عدد پیام — مثال: !countdown 10 مسابقه شروع میشه
    # ══════════════════════════════════════════════════════════════

    async def _cmd_countdown(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split(maxsplit=2)
        if len(parts) < 2:
            await self.highrise.chat("فرمت: !countdown عدد پیام\nمثال: !countdown 10 مسابقه شروع میشه")
            return
        if parts[1].lower() == "stop":
            if self._countdown_task and not self._countdown_task.done():
                self._countdown_task.cancel()
                await self.highrise.chat("🚫 تایمر متوقف شد.")
            else:
                await self.highrise.chat("❌ تایمری فعال نیست.")
            return
        try:
            seconds = int(parts[1])
            if seconds < 1 or seconds > 300:
                raise ValueError
        except ValueError:
            await self.highrise.chat("❌ عدد باید بین 1 تا 300 باشه!")
            return
        final_msg = parts[2] if len(parts) > 2 else "⏰ وقت تموم شد!"

        if self._countdown_task and not self._countdown_task.done():
            self._countdown_task.cancel()

        async def _run_countdown():
            try:
                await self.highrise.chat(f"⏳ تایمر شروع شد: {seconds} ثانیه")
                checkpoints = [s for s in [seconds, 30, 20, 10, 5, 3, 2, 1] if s < seconds]
                remaining = seconds
                for cp in sorted(checkpoints, reverse=True):
                    wait = remaining - cp
                    if wait > 0:
                        await sleep(wait)
                        remaining = cp
                        await self.highrise.chat(f"⏳ {cp} ثانیه مونده...")
                await sleep(remaining)
                await self.highrise.chat(f"🎯 {final_msg}")
            except CancelledError:
                pass
            except Exception as e:
                logger.error(f"خطا در countdown: {e}")

        self._countdown_task = create_task(_run_countdown())

    # ══════════════════════════════════════════════════════════════
    # سیستم Top امتیاز 🏆
    # ══════════════════════════════════════════════════════════════

    async def _cmd_top(self, user: User, message: str):
        scores = self.user_scores
        if not scores:
            await self.highrise.chat("هنوز کسی امتیازی نگرفته!")
            return
        top = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:10]
        medals = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
        lines = ["🏆 برترین کاربرا:"]
        for i, (uname, score) in enumerate(top):
            lines.append(f"{medals[i]} {uname}: {score} امتیاز")
        await self.highrise.chat("\n".join(lines))

    # ══════════════════════════════════════════════════════════════
    # DM به کاربر خاص 📩
    # !dm @username پیام
    # ══════════════════════════════════════════════════════════════

    async def _cmd_dm(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split(maxsplit=2)
        if len(parts) < 3:
            await self.highrise.chat("فرمت: !dm @username پیام")
            return
        target = parts[1].lstrip("@")
        msg_text = parts[2]
        try:
            await self.highrise.send_message(
                conversation_id="",
                message=msg_text,
                username=target
            )
            await self.highrise.chat(f"📩 پیام به @{target} ارسال شد.")
        except Exception as e:
            await self.highrise.chat(f"❌ خطا در ارسال پیام: {e}")

    # ══════════════════════════════════════════════════════════════
    # راهنمای سیستم‌های اضافی
    # ══════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════
    # دستور !botdance
    # !botdance شماره/اسم  — تغییر دنس بات
    # !botdance stop        — متوقف کردن دنس بات
    # !botdance current     — دنس فعلی
    # ══════════════════════════════════════════════════════════════

    async def _cmd_botdance(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        parts = message.strip().split(maxsplit=1)
        if len(parts) < 2:
            current = self._bot_dance_emote or "ندارد"
            await self.highrise.chat(
                f"💃 دستورات دنس بات:\n"
                f"!botdance شماره — مثال: !botdance 222\n"
                f"!botdance اسم — مثال: !botdance dance-floss\n"
                f"!botdance stop — متوقف کردن\n"
                f"!botdance current — دنس فعلی\n"
                f"دنس الان: {current}"
            )
            return

        arg = parts[1].strip()

        if arg.lower() == "stop":
            self._bot_dance_emote = None
            self.ext_config["bot_dance_emote"] = None
            self._save_ext_config()
            if self._bot_dance_task and not self._bot_dance_task.done():
                self._bot_dance_task.cancel()
                self._bot_dance_task = None
            await self.highrise.chat("⏹ دنس بات متوقف شد.")
            return

        if arg.lower() == "current":
            current = self._bot_dance_emote or "ندارد"
            await self.highrise.chat(f"💃 دنس فعلی بات: {current}")
            return

        emote = self._resolve_emote(arg)
        if not emote:
            await self.highrise.chat(
                f"❌ دنس '{arg}' پیدا نشد!\n"
                f"می‌تونی شماره (1-222) یا اسم دنس بزنی.\n"
                f"مثال: !botdance 222 یا !botdance dance-floss"
            )
            return

        self._bot_dance_emote = emote
        self.ext_config["bot_dance_emote"] = emote
        self._save_ext_config()

        if self._bot_dance_task and not self._bot_dance_task.done():
            self._bot_dance_task.cancel()
        self._bot_dance_task = create_task(self._bot_dance_loop())
        await self.highrise.chat(f"💃 دنس بات تغییر کرد به: {emote}")

    # ══════════════════════════════════════════════════════════════
    # سیستم تغییر روم 🚪 — فقط مالک (x11k)
    # ══════════════════════════════════════════════════════════════

    OWNER = "x11k"

    async def _cmd_setroom(self, user: User, message: str):
        if user.username.lower() != self.OWNER:
            await self.highrise.chat("❌ فقط مالک می‌تونه روم رو عوض کنه.")
            return
        parts = message.strip().split()
        if len(parts) < 2:
            current = self.ext_config.get("room_id", "پیش‌فرض")
            await self.highrise.chat(
                f"فرمت: !setroom [room_id]\n"
                f"روم فعلی: {current}\n"
                f"بعد از تغییر، بات ریستارت می‌کنه."
            )
            return
        new_room = parts[1].strip()
        old_room = self.ext_config.get("room_id", "نامشخص")
        self.ext_config["room_id"] = new_room
        self._save_ext_config()
        await self.highrise.chat(
            f"✅ آیدی روم ذخیره شد!\n"
            f"قبلی: {old_room}\n"
            f"جدید: {new_room}\n"
            f"🔄 بات داره میره روم جدید..."
        )
        await sleep(1.5)
        raise SystemExit("switch_room")

    async def _cmd_roominfo(self, user: User, message: str):
        if user.username.lower() != self.OWNER:
            await self.highrise.chat("❌ فقط مالک می‌تونه این رو ببینه.")
            return
        room_id = self.ext_config.get("room_id") or os.getenv("ROOM_ID", "از env")
        await self.highrise.chat(
            f"🏠 اطلاعات روم:\n"
            f"Room ID: {room_id}\n"
            f"برای تغییر: !setroom [room_id]"
        )

    async def _cmd_dancereset(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه از این دستور استفاده کنه.")
            return
        default = "dance-floss"
        self._bot_dance_emote = default
        self.ext_config["bot_dance_emote"] = default
        self._save_ext_config()
        if self._bot_dance_task and not self._bot_dance_task.done():
            self._bot_dance_task.cancel()
        self._bot_dance_task = create_task(self._bot_dance_loop())
        await self.highrise.chat(f"🔄 دنس بات ریست شد! برگشت به: {default}")

    async def _cmd_reset(self, user: User, message: str):
        username = user.username.lower()
        if username in self.dance_tasks and not self.dance_tasks[username].done():
            self.dance_tasks[username].cancel()
            self.dance_tasks.pop(username, None)
        self.user_dances.pop(username, None)
        self.party_dances.pop(username, None)
        await self.highrise.chat(f"🔄 @{user.username} دنست ریست شد!")

    # ══════════════════════════════════════════════════════════════
    # ⚠️ سیستم اخطار
    # ══════════════════════════════════════════════════════════════

    async def _cmd_warn(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه اخطار بده.")
            return
        parts = message.strip().split(None, 2)
        if len(parts) < 2:
            await self.highrise.chat("فرمت: !warn @username [دلیل]")
            return
        target = parts[1].lstrip("@").lower()
        reason = parts[2] if len(parts) > 2 else "بدون دلیل"
        warns = self.ext_config.setdefault("warn_records", {})
        warns[target] = warns.get(target, 0) + 1
        count = warns[target]
        self._save_ext_config()
        if count >= 3:
            banned = self.ext_config.setdefault("banned_users", [])
            if target not in banned:
                banned.append(target)
                self._save_ext_config()
            await self.highrise.chat(
                f"🚫 @{target} بعد از {count} اخطار بن شد!\n"
                f"دلیل آخر: {reason}"
            )
        else:
            await self.highrise.chat(
                f"⚠️ اخطار {count}/3 به @{target}\n"
                f"دلیل: {reason}"
            )

    async def _cmd_warns(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه کارنامه ببینه.")
            return
        parts = message.strip().split()
        if len(parts) < 2:
            await self.highrise.chat("فرمت: !warns @username")
            return
        target = parts[1].lstrip("@").lower()
        warns = self.ext_config.get("warn_records", {})
        count = warns.get(target, 0)
        banned = self.ext_config.get("banned_users", [])
        status = "🚫 بن شده" if target in banned else "✅ فعال"
        await self.highrise.chat(
            f"📋 کارنامه @{target}\n"
            f"اخطار: {count}/3\n"
            f"وضعیت: {status}"
        )

    async def _cmd_clearwarn(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه اخطار پاک کنه.")
            return
        parts = message.strip().split()
        if len(parts) < 2:
            await self.highrise.chat("فرمت: !clearwarn @username")
            return
        target = parts[1].lstrip("@").lower()
        self.ext_config.setdefault("warn_records", {}).pop(target, None)
        banned = self.ext_config.setdefault("banned_users", [])
        if target in banned:
            banned.remove(target)
        self._save_ext_config()
        await self.highrise.chat(f"✅ اخطارهای @{target} پاک شد.")

    # ══════════════════════════════════════════════════════════════
    # ⏰ سیستم پیام زمانبندی
    # ══════════════════════════════════════════════════════════════

    async def _cmd_schedule(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه پیام زمانبندی بذاره.")
            return
        parts = message.strip().split(None, 2)
        if len(parts) < 3:
            await self.highrise.chat("فرمت: !schedule [دقیقه] [پیام]")
            return
        try:
            minutes = float(parts[1])
        except ValueError:
            await self.highrise.chat("❌ عدد دقیقه درست نیست.")
            return
        scheduled_msg = parts[2]
        await self.highrise.chat(
            f"⏰ پیام بعد از {minutes:.0f} دقیقه ارسال میشه."
        )
        async def _send_later():
            await sleep(minutes * 60)
            await self.highrise.chat(f"📢 {scheduled_msg}")
        create_task(_send_later())

    # ══════════════════════════════════════════════════════════════
    # 📊 سیستم آمار
    # ══════════════════════════════════════════════════════════════

    async def _cmd_stats(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه آمار ببینه.")
            return
        today = datetime.now().strftime("%Y-%m-%d")
        visitors_today = len(self._visitors_today.get(today, set()))
        total_visitors = sum(len(v) for v in self._visitors_today.values())
        banned_count = len(self.ext_config.get("banned_users", []))
        warned_count = len(self.ext_config.get("warn_records", {}))
        admin_list = self.config.get("admin_usernames", [])
        vip_list = self.config.get("vip_usernames", [])
        floors_count = len(self.ext_config.get("floors", {}))
        await self.highrise.chat(
            f"📊 آمار اتاق:\n"
            f"👥 بازدیدکننده امروز: {visitors_today}\n"
            f"🗓 کل بازدید: {total_visitors}\n"
            f"🚫 بن‌شده: {banned_count}\n"
            f"⚠️ اخطارخورده: {warned_count}\n"
            f"👑 ادمین: {len(admin_list)}\n"
            f"⭐ VIP: {len(vip_list)}\n"
            f"🏠 طبقه: {floors_count}"
        )

    # ══════════════════════════════════════════════════════════════
    # 👥 سیستم همه‌کسی‌دنس
    # ══════════════════════════════════════════════════════════════

    async def _cmd_alldance(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه همه رو به دنس وادار کنه.")
            return
        parts = message.strip().split()
        emote_key = parts[1] if len(parts) > 1 else "dance-floss"
        emote = self._resolve_emote(emote_key)
        if not emote:
            await self.highrise.chat(f"❌ دنس '{emote_key}' پیدا نشد.")
            return
        try:
            room_users = await self.highrise.get_room_users()
            users = room_users.content if hasattr(room_users, "content") else []
        except Exception as e:
            await self.highrise.chat(f"❌ خطا در گرفتن لیست کاربران: {e}")
            return
        count = 0
        for u, _ in users:
            if u.id == self.user_id:
                continue
            try:
                await self.highrise.send_emote(emote, u.id)
                count += 1
                await sleep(0.3)
            except Exception:
                pass
        await self.highrise.chat(f"🕺 {count} نفر دنس '{emote_key}' زدن!")

    # ══════════════════════════════════════════════════════════════
    # 🔔 سیستم خوش‌آمد سفارشی
    # ══════════════════════════════════════════════════════════════

    async def _cmd_setwelcome(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه خوش‌آمد رو تنظیم کنه.")
            return
        parts = message.strip().split(None, 1)
        if len(parts) < 2:
            current = self.ext_config.get("welcome_dm_message", "")
            await self.highrise.chat(
                f"پیام فعلی:\n{current}\n\n"
                f"فرمت: !setwelcome [پیام]\n"
                f"از {{username}} برای نام کاربر استفاده کن."
            )
            return
        new_msg = parts[1]
        self.ext_config["welcome_dm_message"] = new_msg
        self.ext_config["welcome_dm"] = True
        self._save_ext_config()
        await self.highrise.chat(
            f"✅ پیام خوش‌آمد ذخیره شد:\n{new_msg}"
        )

    async def _cmd_welcomeon(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه.")
            return
        self.ext_config["welcome_dm"] = True
        self._save_ext_config()
        await self.highrise.chat("✅ دم خوش‌آمد روشن شد.")

    async def _cmd_welcomeoff(self, user: User, message: str):
        if not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه.")
            return
        self.ext_config["welcome_dm"] = False
        self._save_ext_config()
        await self.highrise.chat("🔕 دم خوش‌آمد خاموش شد.")

    async def _cmd_settoken(self, user: User, message: str):
        if user.username.lower() != self.OWNER:
            await self.highrise.chat("❌ فقط مالک می‌تونه توکن رو عوض کنه.")
            return
        parts = message.strip().split()
        if len(parts) < 2:
            await self.highrise.chat(
                "فرمت: !settoken [api_token]\n"
                "توکن جدید رو از Developer Portal بگیر."
            )
            return
        new_token = parts[1].strip()
        self.ext_config["api_token"] = new_token
        self._save_ext_config()
        await self.highrise.chat(
            "✅ توکن ذخیره شد!\n"
            "حالا !restart بزن تا با توکن جدید وصل بشه."
        )

    async def _cmd_restart(self, user: User, message: str):
        if user.username.lower() != self.OWNER and not self._is_admin(user):
            await self.highrise.chat("❌ فقط ادمین می‌تونه بات رو ریستارت کنه.")
            return
        await self.highrise.chat("🔄 بات داره ریستارت می‌شه...")
        await sleep(1.5)
        raise SystemExit("restart")

    async def _cmd_help_override(self, user: User, message: str):
        await super().on_chat(user, message)
        await self.highrise.chat(
            "〰〰〰〰〰〰〰〰〰\n"
            "📖 دستورات اضافی:\n"
            "  !exthelp 1 ← دنس، موقعیت، طبقه\n"
            "  !exthelp 2 ← لاتاری، کوییز، VIP\n"
            "  !exthelp 3 ← اخطار، آمار، خوش‌آمد\n"
            "〰〰〰〰〰〰〰〰〰"
        )

    async def _cmd_exthelp(self, user: User, message: str):
        parts = message.strip().split()
        page = parts[1] if len(parts) > 1 else "1"

        if page == "2":
            await self.highrise.chat(
                "〰〰〰〰〰〰〰〰〰\n"
                "📖 راهنما — صفحه ۲\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "🎰 لاتاری:\n"
                "  !lottery start [جایزه]\n"
                "  !lottery end | cancel | list\n"
                "  !join ← شرکت در لاتاری\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "❓ Quiz:\n"
                "  !quiz [سوال] | [جواب]\n"
                "  جواب درست = +50 امتیاز 🏆\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "⭐ VIP موقت:\n"
                "  !tempvip @user [دقیقه]\n"
                "  !untempvip @user\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "⏳ !countdown [ثانیه] [پیام]\n"
                "🏆 !top | 👥 !visitors\n"
                "🚨 !report @user [دلیل]\n"
                "📩 !dm @user [پیام]\n"
                "🔇 !botoff | 🔊 !boton\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "📄 ۱: !exthelp 1 | ۳: !exthelp 3"
            )
        elif page == "3":
            await self.highrise.chat(
                "〰〰〰〰〰〰〰〰〰\n"
                "📖 راهنما — صفحه ۳\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "⚠️ سیستم اخطار:\n"
                "  !warn @user [دلیل]\n"
                "  !warns @user ← کارنامه\n"
                "  !clearwarn @user ← پاک کردن\n"
                "  بن خودکار بعد از 3 اخطار 🚫\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "⏰ پیام زمانبندی:\n"
                "  !schedule [دقیقه] [پیام]\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "📊 !stats ← آمار اتاق\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "👥 همه‌کسی‌دنس:\n"
                "  !alldance [شماره یا اسم دنس]\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "🔔 خوش‌آمد DM:\n"
                "  !setwelcome [پیام] ← {username}\n"
                "  !welcomeon | !welcomeoff\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "🏠 !setroom [id] | !roominfo\n"
                "📄 ۱: !exthelp 1 | ۲: !exthelp 2"
            )
        else:
            await self.highrise.chat(
                "〰〰〰〰〰〰〰〰〰\n"
                "📖 راهنما — صفحه ۱\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "💃 دنس بات:\n"
                "  !botdance [شماره/اسم]\n"
                "  !botdance stop | current\n"
                "  !dancereset ← برگشت به floss\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "📍 موقعیت بات:\n"
                "  !bot here | !bot [x] [y] [z]\n"
                "  !botfree | !sethome | !home\n"
                "  !delhome | !pos\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "🏢 طبقه‌ها:\n"
                "  !setfloor [اسم] | !delfloor\n"
                "  !floors | [اسم طبقه] ← رفتن\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "📢 لوپ اعلان:\n"
                "  !setloop [دقیقه]\n"
                "  !setloop add [پیام]\n"
                "  !setloop clear | status\n"
                "  !loopon | !loopoff\n"
                "〰〰〰〰〰〰〰〰〰\n"
                "📄 ۲: !exthelp 2 | ۳: !exthelp 3"
            )


def _get_room_id():
    try:
        if os.path.exists(EXT_CONFIG_FILE):
            with open(EXT_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("room_id"):
                return data["room_id"]
    except Exception:
        pass
    return os.getenv("ROOM_ID", "6a2ef319974dafc881423ffd")


def _get_api_token():
    try:
        if os.path.exists(EXT_CONFIG_FILE):
            with open(EXT_CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("api_token"):
                return data["api_token"]
    except Exception:
        pass
    return os.getenv("API_TOKEN", "218946befa48bac63674a437c19fae56379702fc88e56ed91d37fb408cd24314")


async def main():
    api_token = _get_api_token()

    max_attempts = 5
    attempt = 0
    while attempt < max_attempts:
        room_id = _get_room_id()
        bot = ExtendedBot()
        bot_def = BotDefinition(room_id=room_id, api_token=api_token, bot=bot)
        logger.info(f"اتصال به روم: {room_id}")
        try:
            from highrise.__main__ import main as highrise_main
            await highrise_main([bot_def])
        except SystemExit as e:
            reason = str(e)
            logger.info(f"SystemExit دریافت شد: {reason}")
            attempt = 0
            await sleep(2)
            continue
        except BaseException as e:
            if "ClientConnectionReset" in type(e).__name__:
                logger.error(f"اتصال قطع شد: {e}")
                try:
                    await bot_def.bot.cleanup_tasks()
                except Exception:
                    pass
                attempt += 1
                logger.info(f"تلاش مجدد ({attempt}/{max_attempts}) بعد از 10 ثانیه...")
                await sleep(10)
            else:
                logger.error(f"خطای ناشناخته: {type(e).__name__}: {e}")
                attempt += 1
                await sleep(10)
        else:
            attempt = 0
    logger.error("حداکثر تلاش‌های اتصال به پایان رسید.")


if __name__ == "__main__":
    import asyncio
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("bot_ext.log"), logging.StreamHandler()]
    )
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"خطا در اجرای اولیه: {e}", exc_info=True)
