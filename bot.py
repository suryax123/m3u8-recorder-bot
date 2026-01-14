import asyncio
import datetime
import sys
import os
from typing import Dict
from telethon import events
from telethon.tl.custom import Button
from config import app, RECORDING_PATH
import utils

class RecordingState:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.step = "start"
        self.data = {}
        self.last_bot_message_id = None

class ActiveRecording:
    def __init__(self, chat_id, task, cancel_event):
        self.chat_id = chat_id
        self.task = task
        self.cancel_event = cancel_event
        self.start_time = datetime.datetime.now()

user_states: Dict[int, RecordingState] = {}
active_recordings: Dict[int, ActiveRecording] = {}
scheduled_jobs: Dict[int, asyncio.Task] = {}

def parse_time(time_str: str):
    try:
        return datetime.datetime.strptime(time_str, "%H:%M").time()
    except:
        return None

def calculate_schedule(start_time, end_time):
    now = datetime.datetime.now()
    start_dt = datetime.datetime.combine(now.date(), start_time)
    end_dt = datetime.datetime.combine(now.date(), end_time)

    if end_dt <= start_dt:
        end_dt += datetime.timedelta(days=1)

    if start_dt < now - datetime.timedelta(seconds=60):
        start_dt += datetime.timedelta(days=1)
        end_dt += datetime.timedelta(days=1)

    duration_minutes = (end_dt - start_dt).total_seconds() / 60
    return duration_minutes, start_dt, end_dt

async def run_recording(chat_id, url, start_dt, duration_minutes, end_dt):
    recorded_file = None
    date_str = start_dt.strftime("%d%m%Y")
    start_time_str = start_dt.strftime("%H%M")
    end_time_str = end_dt.strftime("%H%M")
    base_filename = f"{date_str}_{start_time_str}-{end_time_str}"

    try:
        await app.send_message(
            chat_id,
            f"Recording Started\n\n"
            f"File: {base_filename}.mp4\n"
            f"Duration: {duration_minutes:.0f} minutes\n\n"
            f"You will be notified when complete."
        )

        cancel_event = asyncio.Event()

        recording_task = asyncio.create_task(
            utils.record_stream_async(url, duration_minutes, base_filename, cancel_event)
        )

        active_recordings[chat_id] = ActiveRecording(chat_id, recording_task, cancel_event)

        recorded_file = await recording_task

        if chat_id in active_recordings:
            del active_recordings[chat_id]

        if not recorded_file:
            await app.send_message(chat_id, "Recording failed. Stream may be unavailable.")
            return

        file_size = utils.get_file_size_mb(recorded_file)

        upload_msg = await app.send_message(
            chat_id,
            f"Uploading {base_filename}.mp4 ({file_size:.1f} MB)..."
        )

        try:
            await app.send_file(
                chat_id,
                recorded_file,
                caption=f"Recording Complete\n\n"
                        f"File: {base_filename}.mp4\n"
                        f"Size: {file_size:.1f} MB\n"
                        f"Duration: {duration_minutes:.0f} min",
                supports_streaming=True
            )

            await app.delete_messages(chat_id, upload_msg.id)
            await app.send_message(chat_id, "Upload complete!")

        except Exception as e:
            await app.delete_messages(chat_id, upload_msg.id)
            await app.send_message(chat_id, f"Upload failed: {str(e)[:100]}")

    except utils.RecordingCancelled:
        await app.send_message(chat_id, "Recording cancelled.")

    except asyncio.CancelledError:
        await app.send_message(chat_id, "Job cancelled.")

    except Exception as e:
        await app.send_message(chat_id, f"Error: {str(e)[:200]}")

    finally:
        if recorded_file:
            utils.cleanup_file(recorded_file)

        if chat_id in active_recordings:
            del active_recordings[chat_id]

        if chat_id in scheduled_jobs:
            del scheduled_jobs[chat_id]

async def schedule_recording(chat_id, url, start_time, end_time):
    duration_minutes, start_dt, end_dt = calculate_schedule(start_time, end_time)
    delay_seconds = (start_dt - datetime.datetime.now()).total_seconds()

    if delay_seconds < 0:
        delay_seconds = 0

    async def scheduled_job():
        if delay_seconds > 0:
            await asyncio.sleep(delay_seconds)
        await run_recording(chat_id, url, start_dt, duration_minutes, end_dt)

    task = asyncio.create_task(scheduled_job())
    scheduled_jobs[chat_id] = task

    await app.send_message(
        chat_id,
        f"Recording Scheduled\n\n"
        f"Start: {start_dt.strftime('%d/%m/%Y %H:%M')}\n"
        f"End: {end_dt.strftime('%d/%m/%Y %H:%M')}\n"
        f"Duration: {duration_minutes:.0f} minutes\n\n"
        f"Use /cancel to cancel"
    )

@app.on(events.NewMessage(pattern='/start'))
@app.on(events.NewMessage(pattern='/menu'))
async def start_handler(event):
    user_id = event.chat_id
    user_states[user_id] = RecordingState(user_id)

    buttons = [
        [Button.inline("New Recording", data="new_recording")],
        [Button.inline("Cancel Job", data="cancel_job")],
        [Button.inline("Status", data="check_status")]
    ]

    msg = await event.reply("Stream Recorder Bot\n\nSchedule recordings from live streams", buttons=buttons)
    user_states[user_id].last_bot_message_id = msg.id

@app.on(events.CallbackQuery(data='new_recording'))
async def new_recording_handler(event):
    user_id = event.chat_id

    if user_id in active_recordings or user_id in scheduled_jobs:
        await event.answer("You already have an active recording", alert=True)
        return

    state = user_states.get(user_id)
    if not state:
        state = RecordingState(user_id)
        user_states[user_id] = state

    await event.edit("Step 1/3: Send stream URL\n\nSupported: m3u8, YouTube, most formats")
    state.step = "waiting_url"
    await event.answer()

@app.on(events.CallbackQuery(data='cancel_job'))
async def cancel_job_handler(event):
    chat_id = event.chat_id

    if chat_id in active_recordings:
        recording = active_recordings[chat_id]
        recording.cancel_event.set()
        await event.edit("Cancelling recording...")
        await event.answer()
        return

    if chat_id in scheduled_jobs:
        scheduled_jobs[chat_id].cancel()
        del scheduled_jobs[chat_id]
        if chat_id in user_states:
            del user_states[chat_id]
        await event.edit("Job cancelled")
        await event.answer()
        return

    await event.edit("No active job")
    await event.answer()

@app.on(events.CallbackQuery(data='check_status'))
async def status_handler(event):
    chat_id = event.chat_id

    if chat_id in active_recordings:
        recording = active_recordings[chat_id]
        elapsed = (datetime.datetime.now() - recording.start_time).total_seconds()
        await event.answer(f"Recording in progress\nElapsed: {elapsed/60:.0f} min", alert=True)
    elif chat_id in scheduled_jobs:
        await event.answer("Job scheduled, waiting to start", alert=True)
    else:
        await event.answer("No active recordings", alert=True)

@app.on(events.CallbackQuery(data='cancel_conversation'))
async def cancel_conversation_handler(event):
    user_id = event.chat_id
    if user_id in user_states:
        del user_states[user_id]
    await event.edit("Cancelled")
    await event.answer()

@app.on(events.NewMessage(pattern='/cancel'))
async def cancel_command(event):
    chat_id = event.chat_id

    if chat_id in active_recordings:
        recording = active_recordings[chat_id]
        recording.cancel_event.set()
        await event.reply("Cancelling...")
    elif chat_id in scheduled_jobs:
        scheduled_jobs[chat_id].cancel()
        del scheduled_jobs[chat_id]
        await event.reply("Job cancelled")
    else:
        await event.reply("No active job")

@app.on(events.NewMessage)
async def message_handler(event):
    user_id = event.chat_id
    text = event.text.strip()

    if text.startswith('/') or event.is_reply or event.sender.bot:
        return

    state = user_states.get(user_id)
    if not state:
        return

    try:
        await app.delete_messages(user_id, event.id)
    except:
        pass

    if state.step == "waiting_url":
        if not text.startswith('http'):
            await app.send_message(user_id, "Invalid URL")
            return

        state.data['url'] = text
        state.step = "waiting_start_time"
        await app.edit_message(user_id, state.last_bot_message_id, "Step 2/3: Send start time (HH:MM)\n\nExample: 14:30")

    elif state.step == "waiting_start_time":
        start_time = parse_time(text)
        if not start_time:
            await app.send_message(user_id, "Invalid time. Use HH:MM")
            return

        state.data['start_time'] = start_time
        state.step = "waiting_end_time"
        await app.edit_message(user_id, state.last_bot_message_id, "Step 3/3: Send end time (HH:MM)\n\nExample: 15:30")

    elif state.step == "waiting_end_time":
        end_time = parse_time(text)
        if not end_time:
            await app.send_message(user_id, "Invalid time. Use HH:MM")
            return

        duration_minutes, start_dt, end_dt = calculate_schedule(state.data['start_time'], end_time)

        if duration_minutes <= 0:
            await app.send_message(user_id, "End time must be after start time")
            return

        if duration_minutes > 720:
            await app.send_message(user_id, "Max duration: 12 hours")
            return

        state.data['end_time'] = end_time
        state.step = "ready_to_start"

        buttons = [
            [Button.inline("Confirm", data="start_job")],
            [Button.inline("Cancel", data="cancel_conversation")]
        ]

        await app.edit_message(
            user_id,
            state.last_bot_message_id,
            f"Review:\n\n"
            f"Start: {start_dt.strftime('%d/%m %H:%M')}\n"
            f"End: {end_dt.strftime('%d/%m %H:%M')}\n"
            f"Duration: {duration_minutes:.0f} min",
            buttons=buttons
        )

@app.on(events.CallbackQuery(data='start_job'))
async def start_job_handler(event):
    user_id = event.chat_id
    state = user_states.get(user_id)

    if not state or state.step != "ready_to_start":
        await event.edit("Error: Restart with /menu")
        await event.answer()
        return

    await event.edit("Scheduling...")
    await event.answer()

    await schedule_recording(user_id, state.data['url'], state.data['start_time'], state.data['end_time'])

    if user_id in user_states:
        del user_states[user_id]

if __name__ == '__main__':
    try:
        print("Bot starting...")
        print(f"Recording path: {RECORDING_PATH}")
        app.run_until_disconnected()
    except KeyboardInterrupt:
        print("\nBot stopped")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
