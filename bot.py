import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import discord
from zmanim.hebrew_calendar.jewish_calendar import JewishCalendar
from zmanim.util.geo_location import GeoLocation
from zmanim.zmanim_calendar import ZmanimCalendar

intents = discord.Intents.all()
bot = discord.Bot(intents=intents)

DISCORD_TOKEN = os.getenv('TOKEN')

LAT = float(os.getenv('LAT') or '0')
LON = float(os.getenv('LON') or '0')
ELEVATION_M = float(os.getenv('ELEVATION_M', '0') or '0')
TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')

USER_ID = os.getenv('USER_ID')

BEFORE_OFFSET_MIN = float(os.getenv("BEFORE_OFFSET_MIN") or "20")
AFTER_OFFSET_MIN = float(os.getenv("AFTER_OFFSET_MIN") or "25")

_ASSUR_OVERRIDE_UNTIL = None


def _ceil_to_quarter(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("dt must be timezone-aware")
    base = dt.replace(second=0, microsecond=0)
    quarter = (base.minute // 15) * 15
    if base.minute % 15 != 0 or dt.second or dt.microsecond:
        quarter += 15
    if quarter >= 60:
        base = base.replace(minute=0) + timedelta(hours=1)
    else:
        base = base.replace(minute=quarter)
    return base


def _assur_calc(now: datetime):
    before_off = timedelta(minutes=BEFORE_OFFSET_MIN)
    after_off = timedelta(minutes=AFTER_OFFSET_MIN)

    geo = GeoLocation("loc", LAT, LON, TIMEZONE, elevation=ELEVATION_M)
    zc = ZmanimCalendar(geo_location=geo)

    today = now.date()
    jc_today = JewishCalendar(today)

    zc.date = today
    cl_today = zc.candle_lighting() - before_off
    erev_now = jc_today.is_tomorrow_assur_bemelacha() and now >= cl_today

    tzais_today = zc.tzais() + after_off
    assur_now = jc_today.is_assur_bemelacha() and now < tzais_today

    if not (erev_now or assur_now):
        return False, None, False

    if erev_now and not jc_today.is_assur_bemelacha():
        first = today + timedelta(days=1)
    else:
        first = today
        while JewishCalendar(first - timedelta(days=1)).is_assur_bemelacha():
            first -= timedelta(days=1)

    last = first
    while JewishCalendar(last + timedelta(days=1)).is_assur_bemelacha():
        last += timedelta(days=1)

    zc.date = last
    end_local = zc.tzais() + after_off
    end_local = _ceil_to_quarter(end_local)

    is_last_day = (today == last)
    return True, end_local, is_last_day


def _issur_status_now():
    global _ASSUR_OVERRIDE_UNTIL

    now = datetime.now(ZoneInfo(TIMEZONE))

    if _ASSUR_OVERRIDE_UNTIL and now < _ASSUR_OVERRIDE_UNTIL:
        return False, None

    is_assur, end_local, _ = _assur_calc(now)
    if not is_assur or not end_local:
        return False, None
    return True, end_local


@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    if message.author.id == USER_ID:
        now = datetime.now(ZoneInfo(TIMEZONE))
        is_assur, end_local, is_last_day = _assur_calc(now)
        if is_assur and is_last_day and end_local:
            _set_assur_override(end_local)

    user = await bot.fetch_user(USER_ID)
    if not user:
        return

    if user in message.mentions:
        is_issur, end_local = _issur_status_now()
        if is_issur and end_local:
            end_utc = end_local.astimezone(timezone.utc)
            txt = f"{user.mention} is offline until {discord.utils.format_dt(end_utc, style='F')} and will respond to all messages then."
            await message.reply(txt)


def _set_assur_override(until_local: datetime):
    global _ASSUR_OVERRIDE_UNTIL
    _ASSUR_OVERRIDE_UNTIL = until_local


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
