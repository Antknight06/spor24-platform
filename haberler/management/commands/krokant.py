from django.core.management.base import BaseCommand
from django.conf import settings
from haberler.models import BekleyenYetkiliHaberi, Haber, Kategori
from django.utils.text import slugify
from django.contrib.auth.models import User
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import os
import google.generativeai as genai
from asgiref.sync import sync_to_async

# KONFIGURASYON (Bunları .env dosyasından çekmek daha güvenli olur)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID', 'YOUR_CHAT_ID_HERE')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')

# Gemini Ayarla
if GEMINI_API_KEY != 'YOUR_GEMINI_API_KEY_HERE':
    genai.configure(api_key=GEMINI_API_KEY)

class Command(BaseCommand):
    help = 'Krokant: Telegram üzerinden haberleri özgünleştirir ve yayınlar.'

    def handle(self, *args, **options):
        self.stdout.write("🧠 KROKANT: Analiz Merkezi Başlatılıyor...")
        
        if TELEGRAM_BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            self.stdout.write(self.style.ERROR("❌ TELEGRAM_BOT_TOKEN ayarlanmamış! Lütfen script içini veya .env dosyasını düzenleyin."))
            return

        # Bot Uygulamasını Başlat
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

        # Komutlar
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("check", self.check_news))
        application.add_handler(CallbackQueryHandler(self.button))

        # Periyodik Kontrol (Her 60 saniyede bir)
        job_queue = application.job_queue
        job_queue.run_repeating(self.auto_check_news, interval=60, first=10)

        self.stdout.write(self.style.SUCCESS("✅ Krokant Telegram'a bağlandı. Bekleniyor..."))
        application.run_polling()

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('Merhaba! Ben Krokant. Bekleyen haberleri analiz etmek için hazırım. /check komutu ile manuel kontrol yapabilirsiniz.')

    async def auto_check_news(self, context: ContextTypes.DEFAULT_TYPE):
        await self.process_pending_news(context)

    async def check_news(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        await update.message.reply_text('🔍 Bekleyen haberler taranıyor...')
        await self.process_pending_news(context, chat_id=update.effective_chat.id)

    async def process_pending_news(self, context, chat_id=None):
        target_chat_id = chat_id or ADMIN_CHAT_ID
        if target_chat_id == 'YOUR_CHAT_ID_HERE':
            return

        # Bekleyen haberleri getir (Henüz işlenmemiş)
        news_list = await sync_to_async(list)(BekleyenYetkiliHaberi.objects.filter(onaylandi=False, reddedildi=False)[:5])
        
        if not news_list and chat_id:
            await context.bot.send_message(chat_id=chat_id, text="✅ Bekleyen yeni haber yok.")
            return

        for news in news_list:
            keyboard = [
                [
                    InlineKeyboardButton("✨ Özgünleştir & Yayınla", callback_data=f"rewrite_{news.id}"),
                    InlineKeyboardButton("❌ Reddet", callback_data=f"reject_{news.id}"),
                ],
                [InlineKeyboardButton("🔗 Kaynağı Gör", url='http://google.com')] # Kaynak URL varsa buraya
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            text = f"🆕 **YENİ HABER TESPİT EDİLDİ**\n\n" \
                   f"📌 **Başlık:** {news.baslik}\n" \
                   f"📂 **Kategori:** {news.kategori.ad}\n" \
                   f"📝 **Özet:** {news.ozet[:150]}...\n\n" \
                   f"Ne yapmak istersiniz?"

            # Resmi varsa gönder
            if news.resim:
                 # Local dosya olduğu için göndermek tricky olabilir, şimdilik text
                 pass

            await context.bot.send_message(chat_id=target_chat_id, text=text, parse_mode='Markdown', reply_markup=reply_markup)
            
            # Bot spam yapmasın diye işaretlemek lazım ama modelde 'bot_sent' alanı yok.
            # Şimdilik idare ediyoruz, production'da 'is_processed' alanı eklenmeli.

    async def button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()

        data = query.data
        action, news_id = data.split('_')
        
        try:
            news = await sync_to_async(BekleyenYetkiliHaberi.objects.get)(id=news_id)
        except BekleyenYetkiliHaberi.DoesNotExist:
            await query.edit_message_text(text="⚠️ Bu haber artık mevcut değil.")
            return

        if action == "reject":
            news.reddedildi = True
            await sync_to_async(news.save)()
            await query.edit_message_text(text=f"❌ Haber reddedildi: {news.baslik}")

        elif action == "rewrite":
            await query.edit_message_text(text=f"⏳ {news.baslik} özgünleştiriliyor... Lütfen bekleyin.")
            
            # AI ile Rewrite
            new_title, new_content = await self.rewrite_with_ai(news.baslik, news.icerik)
            
            # Yayınla
            await self.publish_news(news, new_title, new_content)
            
            await query.edit_message_text(text=f"✅ **YAYINLANDI!**\n\nBaşlık: {new_title}\n\nSiteye eklendi.")

    async def rewrite_with_ai(self, title, content):
        if GEMINI_API_KEY == 'YOUR_GEMINI_API_KEY_HERE':
            return f"ÖZGÜN: {title}", f"<p>Bu içerik Krokant tarafından otomatik olarak işlendi (AI Anahtarı Eksik).</p><hr>{content}"
        
        try:
            model = genai.GenerativeModel('gemini-pro')
            prompt = f"Aşağıdaki spor haberini SEO uyumlu, özgün ve akıcı bir dille Türkçe olarak yeniden yaz. HTML formatında çıktı ver. Başlık ve İçerik olarak ayır.\n\nBaşlık: {title}\nİçerik: {content}"
            response = await sync_to_async(model.generate_content)(prompt)
            
            # Basit parse (Geliştirilmeli)
            text = response.text
            new_title = title + " (AI)"
            new_content = text
            
            return new_title, new_content
        except Exception as e:
            return f"ÖZGÜN: {title}", f"<p>AI Hatası: {e}</p>{content}"

    @sync_to_async
    def publish_news(self, pending_news, title, content):
        # Krokant kullanıcısı
        bot_user, _ = User.objects.get_or_create(username='krokant', defaults={'is_staff': True})
        
        # Slug oluştur
        base_slug = slugify(title)
        slug = base_slug
        counter = 1
        while Haber.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
            
        haber = Haber.objects.create(
            baslik=title,
            slug=slug,
            ozet=content[:500], # Özet çıkarılmalı aslında
            icerik=content,
            kategori=pending_news.kategori,
            yazar=bot_user,
            resim=pending_news.resim,
            yayinlandi=True,
            otomatik_eklendi=True
        )
        
        # Bekleyen haberi onayla
        pending_news.onaylandi = True
        pending_news.save()
