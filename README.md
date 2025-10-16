# Assur AFK Bot

Automatic AFK replies when a specific user is pinged during **assur melacha** times. Uses precise zmanim with location, elevation, timezone, and safety offsets. Ends “offline until” at the next quarter-hour after *tzais* on the last assur day and formats the time with native Discord timestamps.

---

## Features

* Watches all messages and replies when the configured user is mentioned
* Detects:

  * **Erev**: from candle lighting minus offset until nightfall
  * **Yom Tov/Shabbos**: full assur window until *tzais* plus offset
* Rounds the end time **up** to the next 15-minute mark
* Converts end time to UTC and replies with `<t:...:F>` formatting
* Local, elevation-aware zmanim via `zmanim` library
* Optional “last-day” override to avoid duplicate replies near the end

---

## How it determines assur melacha

1. Build `GeoLocation(LAT, LON, ELEVATION_M, TIMEZONE)`
2. For **today**:

   * `candle_lighting() - BEFORE_OFFSET_MIN` → Erev start guard
   * `tzais() + AFTER_OFFSET_MIN` → End guard
3. Status is true if:

   * Erev now and tomorrow is assur **or**
   * Today is assur and now < adjusted *tzais*
4. Compute the **first** and **last** consecutive assur dates
5. End-of-window = `tzais(last) + AFTER_OFFSET_MIN`, then **ceil to next 15 min**
6. Reply only when the configured user is mentioned and window is active

---

## Bot in Action

<img width="4320" height="2340" alt="image" src="https://github.com/user-attachments/assets/85e55528-5329-45f3-9d83-0c1ed873c4a6" />


(Internally uses `discord.utils.format_dt(end_utc, style='F')`.)

---

## Requirements

* Python 3.10+
* `discord.py` 2.x
* `zmanim` (Python zmanim library)
* Timezone data (IANA tz, e.g. `America/New_York`)

Install:

```bash
python -m pip install -U discord.py zmanim
```

---

## Configuration

All settings are via environment variables.

| Variable            | Type   | Default            | Description                                             |
| ------------------- | ------ | ------------------ | ------------------------------------------------------- |
| `TOKEN`             | string | —                  | Discord bot token                                       |
| `USER_ID`           | int    | —                  | Discord user ID to protect (numeric, not a tag)         |
| `LAT`               | float  | `0`                | Latitude                                                |
| `LON`               | float  | `0`                | Longitude                                               |
| `ELEVATION_M`       | float  | `0`                | Elevation in meters                                     |
| `TIMEZONE`          | string | `America/New_York` | IANA timezone                                           |
| `BEFORE_OFFSET_MIN` | float  | `20`               | Minutes **before** candle lighting to begin Erev window |
| `AFTER_OFFSET_MIN`  | float  | `25`               | Minutes **after** *tzais* to end window                 |

`.env` example:

```env
TOKEN=
LAT=0
LON=0
ELEVATION_M=0
TIMEZONE=America/New_York
USER_ID=
BEFORE_OFFSET_MIN=20
AFTER_OFFSET_MIN=25
```

---

## Run

```bash
python bot.py
```

Bot prints a single readiness line when connected.

---

## Discord setup

* **Scopes**: `bot`, `applications.commands`
* **Permissions**: `Send Messages`, `Read Message History`, `View Channels`
* **Privileged intent**: enable **Message Content Intent** in the Developer Portal to receive message content and mentions reliably

---
