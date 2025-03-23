import telebot
import yt_dlp
import os
import time
import threading

# Replace with your actual bot token
token = "7886146867:AAGmzGkiNhD9u-XmB4D-YHTkMLJXzI2d9iA"

bot = telebot.TeleBot(token)

# Create downloads folder if it doesn't exist
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Format download speed
def format_speed(speed):
    if speed is None:
        return "0 B/s"
    for unit in ['B/s', 'KB/s', 'MB/s', 'GB/s']:
        if speed < 1024:
            return f"{speed:.2f} {unit}"
        speed /= 1024
    return f"{speed:.2f} TB/s"

# Format remaining time
def format_time(seconds):
    if seconds is None or seconds == float('inf'):
        return "Calculating..."
    minutes, sec = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}h {minutes}m {sec}s"
    elif minutes > 0:
        return f"{minutes}m {sec}s"
    else:
        return f"{sec}s"

# Download handler function
def download_video(message, url):
    chat_id = message.chat.id

    try:
        sent_msg = bot.send_message(chat_id, "Preparing to download video... 📥")

        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'best',
            'cookies': 'cookies.txt',  # Making sure cookies file is used correctly
            'progress_hooks': [lambda d: progress_hook(d, chat_id, sent_msg.message_id)]
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_file = ydl.prepare_filename(info_dict)

        with open(video_file, 'rb') as video:
            bot.send_document(chat_id, video)

        bot.edit_message_text(chat_id=chat_id, message_id=sent_msg.message_id, text="✅ Download complete!")

        # Clean up the downloaded file
        os.remove(video_file)

    except Exception as e:
        bot.send_message(chat_id, f"❌ Failed to download video.\nError: {e}")

# Progress bar updater
def progress_hook(d, chat_id, message_id):
    if d['status'] == 'downloading':
        total_bytes = d.get('total_bytes', 1)
        downloaded_bytes = d.get('downloaded_bytes', 0)
        speed = d.get('speed', 0)
        eta = d.get('eta', None)
        percentage = int(downloaded_bytes * 100 / total_bytes)

        # Create progress bar
        bar_length = 20
        filled_length = int(bar_length * percentage // 100)
        bar = '█' * filled_length + '-' * (bar_length - filled_length)

        message_text = (
            f"Downloading... [{bar}] {percentage}% 📥\n"
            f"Speed: {format_speed(speed)}\n"
            f"Time Remaining: {format_time(eta)}"
        )

        try:
            bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=message_text)
        except:
            pass  # Ignore editing errors

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Welcome to Dark Downloader! 📥\nSend me any video link from YouTube, PW, or Gateway Classes to download.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    url = message.text.strip()
    thread = threading.Thread(target=download_video, args=(message, url))
    thread.start()  # Run downloads in separate threads to handle multiple downloads

bot.infinity_polling()
