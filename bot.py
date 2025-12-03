import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart
from PIL import Image
from flask import Flask, request
import os

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

app = Flask(__name__)

# ---------------- IMAGE PROCESSING ---------------- #
def create_final_image(template_path, user_photo_path, output_path):
    template = Image.open(template_path).convert("RGBA")
    user_photo = Image.open(user_photo_path).convert("RGBA")

    template_w, template_h = template.size
    user_ratio = user_photo.width / user_photo.height
    frame_ratio = template_w / template_h

    if user_ratio > frame_ratio:
        new_width = int(user_photo.height * frame_ratio)
        left = (user_photo.width - new_width) // 2
        user_photo = user_photo.crop((left, 0, left + new_width, user_photo.height))
    else:
        new_height = int(user_photo.width / frame_ratio)
        top = (user_photo.height - new_height) // 2
        user_photo = user_photo.crop((0, top, user_photo.width, top + new_height))

    user_photo = user_photo.resize((template_w, template_h))

    final_img = Image.new("RGBA", (template_w, template_h))
    final_img.paste(user_photo, (0, 0))
    final_img.paste(template, (0, 0), template)

    final_img.save(output_path)

# ---------------- TELEGRAM HANDLERS ---------------- #
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("👋 أرسل صورتك باللباس الكشفي.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    await message.answer("⏳ جاري معالجة الصورة...")

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)

    user_img_path = f"user_{message.from_user.id}.jpg"
    await bot.download_file(file_info.file_path, destination=user_img_path)

    output_path = f"final_{message.from_user.id}.png"
    create_final_image("template.png", user_img_path, output_path)

    await message.answer_photo(FSInputFile(output_path))

# ---------------- WEBHOOK SERVER ---------------- #
@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json()
    asyncio.run(dp.feed_update(bot, update))
    return "OK", 200

async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

if __name__ == "__main__":
    asyncio.run(on_startup())
    app.run(host="0.0.0.0", port=8000)
