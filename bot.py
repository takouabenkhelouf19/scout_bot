import os
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile
from PIL import Image

# 🟢 احصلي على التوكن من متغير البيئة (Render)
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise Exception("❌ BOT_TOKEN is missing! Add it in Render → Environment Variables.")

bot = Bot(token=TOKEN)
dp = Dispatcher()


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


# -------- /start -------- #
@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer("👋 أرسل صورتك باللباس الكشفي.")


# -------- استقبال الصور -------- #
@dp.message(F.photo)
async def handle_photo(message: Message):

    await message.answer("⏳ جاري معالجة الصورة...")

    try:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)

        # 🟢 حفظ الملفات في /tmp (مهم في Render)
        user_img_path = f"/tmp/user_{message.from_user.id}.jpg"
        output_path = f"/tmp/final_{message.from_user.id}.png"

        # تحميل الصورة
        await bot.download_file(file_info.file_path, destination=user_img_path)

        # إنشاء الصورة النهائية
        create_final_image("template.png", user_img_path, output_path)

        await message.answer_photo(FSInputFile(output_path))

    except Exception as e:
        await message.answer("❌ حدث خطأ أثناء معالجة الصورة.")
        print("ERROR:", e)

    finally:
        # 🟢 حذف الملفات المؤقتة
        try:
            if os.path.exists(user_img_path):
                os.remove(user_img_path)
            if os.path.exists(output_path):
                os.remove(output_path)
        except:
            pass


async def main():
    print("Bot is running on Render...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
