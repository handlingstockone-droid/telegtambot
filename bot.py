import sqlite3
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import os

BOT_TOKEN = "8429901774:AAG025PzvM0SM-myZKthEhX4SLhpfDlRMKc"

# Veritabanı
def init_db():
    conn = sqlite3.connect('hesap.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  company TEXT,
                  type TEXT,
                  amount REAL,
                  category TEXT,
                  description TEXT,
                  person TEXT,
                  customer_name TEXT,
                  date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS packages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  count INTEGER,
                  date TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS liters
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  amount REAL,
                  date TEXT)''')
    
    conn.commit()
    return conn

conn = init_db()

# States
(COMPANY_SELECT, AMOUNT, CATEGORY, PERSON, DESCRIPTION, CUSTOMER_NAME, 
 PACKAGE_COUNT, LITER_AMOUNT, REPORT_TYPE, DATE_RANGE) = range(10)

# Ana menü
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    
    keyboard = [
        ['📦 Kargo İşlemleri', '⛽ Yakıt İşlemleri'],
        ['📊 Raporlar', '💰 Bakiye']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        '👋 Hoş geldiniz!\n\n'
        '📦 Barlas ve Uras Express (Kargo)\n'
        '⛽ TrendOil (Yakıt)\n\n'
        'Ne yapmak istersiniz?',
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# KARGO MENÜSÜ
async def kargo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_menu'] = 'kargo'
    keyboard = [
        ['📦 Paket Ekle', '💰 Gelir Ekle'],
        ['💸 Gider Ekle', '🔙 Ana Menü']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('📦 KARGO İŞLEMLERİ', reply_markup=reply_markup)
    return ConversationHandler.END

# YAKIT MENÜSÜ
async def yakit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['current_menu'] = 'yakıt'
    keyboard = [
        ['⛽ Litre Ekle', '💰 Gelir Ekle'],
        ['💸 Gider Ekle', '🔙 Ana Menü']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('⛽ YAKIT İŞLEMLERİ', reply_markup=reply_markup)
    return ConversationHandler.END

# PAKET EKLEME
async def paket_ekle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['🔙 İptal']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('📦 Bugün kaç paket işlendi?', reply_markup=reply_markup)
    return PACKAGE_COUNT

async def paket_ekle_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🔙 İptal':
        return await cancel(update, context)
    
    try:
        count = int(update.message.text)
        user_id = update.effective_user.id
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c = conn.cursor()
        c.execute('INSERT INTO packages (user_id, count, date) VALUES (?, ?, ?)',
                  (user_id, count, date))
        conn.commit()
        
        await update.message.reply_text(f'✅ {count} paket kaydedildi!')
        await start(update, context)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('❌ Lütfen geçerli bir sayı girin!')
        return PACKAGE_COUNT

# LİTRE EKLEME
async def litre_ekle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [['🔙 İptal']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('⛽ Bugün kaç litre satıldı?', reply_markup=reply_markup)
    return LITER_AMOUNT

async def litre_ekle_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🔙 İptal':
        return await cancel(update, context)
    
    try:
        amount = float(update.message.text)
        user_id = update.effective_user.id
        date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        c = conn.cursor()
        c.execute('INSERT INTO liters (user_id, amount, date) VALUES (?, ?, ?)',
                  (user_id, amount, date))
        conn.commit()
        
        await update.message.reply_text(f'✅ {amount} litre kaydedildi!')
        await start(update, context)
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text('❌ Lütfen geçerli bir sayı girin!')
        return LITER_AMOUNT

# GELİR EKLEME
async def gelir_ekle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('current_menu') == 'kargo':
        context.user_data['company'] = 'kargo'
        context.user_data['type'] = 'gelir'
        
        keyboard = [
            ['Morex', 'Findex', '166'],
            ['Kango', 'ASE', '🔙 İptal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('💰 Gelir kategorisi seçin:', reply_markup=reply_markup)
        return CATEGORY
    else:
        context.user_data['company'] = 'yakıt'
        context.user_data['type'] = 'gelir'
        context.user_data['category'] = 'Yakıt Satışı'
        
        keyboard = [['🔙 İptal']]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('👤 Müşteri adı/açıklama yazın:', reply_markup=reply_markup)
        return CUSTOMER_NAME

# GİDER EKLEME
async def gider_ekle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('current_menu') == 'kargo':
        context.user_data['company'] = 'kargo'
        context.user_data['type'] = 'gider'
        
        keyboard = [
            ['Maaş', 'İnternet', 'Su'],
            ['Ford Yakıt', 'Kira', 'Elektrik'],
            ['Diğer', '🔙 İptal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('💸 Gider kategorisi seçin:', reply_markup=reply_markup)
        return CATEGORY
    else:
        context.user_data['company'] = 'yakıt'
        context.user_data['type'] = 'gider'
        
        keyboard = [
            ['Rusya Alfa', 'Dahili Masraf'],
            ['🔙 İptal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('💸 Gider kategorisi seçin:', reply_markup=reply_markup)
        return CATEGORY

# KATEGORİ SEÇİMİ
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🔙 İptal':
        return await cancel(update, context)
    
    context.user_data['category'] = update.message.text
    
    keyboard = [['🔙 İptal']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('💵 Miktarı yazın (AZN):', reply_markup=reply_markup)
    return AMOUNT

# MÜŞTERİ ADI
async def customer_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🔙 İptal':
        return await cancel(update, context)
    
    context.user_data['customer_name'] = update.message.text
    
    keyboard = [['🔙 İptal']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('💵 Miktarı yazın (AZN):', reply_markup=reply_markup)
    return AMOUNT

# MİKTAR
async def amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🔙 İptal':
        return await cancel(update, context)
    
    try:
        amount = float(update.message.text)
        context.user_data['amount'] = amount
        
        keyboard = [
            ['Sanan', 'Ali'],
            ['Nijat', 'Caner'],
            ['🔙 İptal']
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text('👤 Harcamayı yapan kişi:', reply_markup=reply_markup)
        return PERSON
    except ValueError:
        await update.message.reply_text('❌ Lütfen geçerli bir sayı girin!')
        return AMOUNT

# KİŞİ SEÇİMİ
async def person_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🔙 İptal':
        return await cancel(update, context)
    
    context.user_data['person'] = update.message.text
    
    keyboard = [['🔙 İptal']]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('📝 Açıklama yazın (veya "yok" yazın):', reply_markup=reply_markup)
    return DESCRIPTION

# AÇIKLAMA VE KAYDETME
async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == '🔙 İptal':
        return await cancel(update, context)
    
    user_id = update.effective_user.id
    company = context.user_data.get('company', 'kargo')
    trans_type = context.user_data.get('type', 'gider')
    amount = context.user_data.get('amount', 0)
    category = context.user_data.get('category', '-')
    person = context.user_data.get('person', '-')
    customer_name = context.user_data.get('customer_name', '-')
    description = update.message.text if update.message.text.lower() != 'yok' else '-'
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO transactions 
                     (user_id, company, type, amount, category, description, person, customer_name, date)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (user_id, company, trans_type, amount, category, description, person, customer_name, date))
        conn.commit()
        
        emoji = '💰' if trans_type == 'gelir' else '💸'
        company_name = '📦 Barlas ve Uras Express' if company == 'kargo' else '⛽ TrendOil'
        
        message = f'✅ Kaydedildi!\n\n{company_name}\n{emoji} {trans_type.upper()}\n'
        message += f'Miktar: {amount} AZN\n'
        message += f'Kategori: {category}\n'
        message += f'Kişi: {person}\n'
        if customer_name != '-':
            message += f'Müşteri: {customer_name}\n'
        message += f'Açıklama: {description}'
        
        await update.message.reply_text(message)
        
        context.user_data.clear()
        await start(update, context)
        return ConversationHandler.END
    except Exception as e:
        await update.message.reply_text(f'❌ Hata oluştu: {str(e)}')
        await start(update, context)
        return ConversationHandler.END

# BAKİYE
async def bakiye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = conn.cursor()
    
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="kargo" AND type="gelir"')
    kargo_gelir = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="kargo" AND type="gider"')
    kargo_gider = c.fetchone()[0] or 0
    kargo_bakiye = kargo_gelir - kargo_gider
    
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="yakıt" AND type="gelir"')
    yakit_gelir = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="yakıt" AND type="gider"')
    yakit_gider = c.fetchone()[0] or 0
    yakit_bakiye = yakit_gelir - yakit_gider
    
    c.execute('SELECT SUM(count) FROM packages')
    total_packages = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(amount) FROM liters')
    total_liters = c.fetchone()[0] or 0
    
    message = '💰 BAKİYE DURUMU\n\n'
    message += '📦 BARLAS VE URAS EXPRESS\n'
    message += f'Gelir: {kargo_gelir:.2f} AZN\n'
    message += f'Gider: {kargo_gider:.2f} AZN\n'
    message += f'Bakiye: {kargo_bakiye:.2f} AZN\n'
    message += f'Toplam Paket: {total_packages}\n\n'
    
    message += '⛽ TRENDOIL\n'
    message += f'Gelir: {yakit_gelir:.2f} AZN\n'
    message += f'Gider: {yakit_gider:.2f} AZN\n'
    message += f'Bakiye: {yakit_bakiye:.2f} AZN\n'
    message += f'Toplam Litre: {total_liters:.2f}\n'
    
    await update.message.reply_text(message)

# RAPORLAR MENÜSÜ
async def raporlar_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ['📦 Paket Raporu', '⛽ Litre Raporu'],
        ['📊 Gelir/Gider Raporu', '📥 Excel İndir'],
        ['🔙 Ana Menü']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text('📊 RAPORLAR', reply_markup=reply_markup)

# PAKET RAPORU
async def paket_raporu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT SUM(count) FROM packages WHERE date LIKE ?', (f'{today}%',))
    today_count = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(count) FROM packages')
    total_count = c.fetchone()[0] or 0
    
    message = '📦 PAKET RAPORU\n\n'
    message += f'Bugün: {today_count} paket\n'
    message += f'Toplam: {total_count} paket'
    
    await update.message.reply_text(message)

# LİTRE RAPORU
async def litre_raporu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute('SELECT SUM(amount) FROM liters WHERE date LIKE ?', (f'{today}%',))
    today_amount = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(amount) FROM liters')
    total_amount = c.fetchone()[0] or 0
    
    message = '⛽ LİTRE RAPORU\n\n'
    message += f'Bugün: {today_amount:.2f} litre\n'
    message += f'Toplam: {total_amount:.2f} litre'
    
    await update.message.reply_text(message)

# GELİR/GİDER RAPORU
async def gelir_gider_raporu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = conn.cursor()
    
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="kargo" AND type="gelir"')
    kargo_gelir = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="kargo" AND type="gider"')
    kargo_gider = c.fetchone()[0] or 0
    
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="yakıt" AND type="gelir"')
    yakit_gelir = c.fetchone()[0] or 0
    c.execute('SELECT SUM(amount) FROM transactions WHERE company="yakıt" AND type="gider"')
    yakit_gider = c.fetchone()[0] or 0
    
    c.execute('SELECT company, type, amount, category, person, date FROM transactions ORDER BY date DESC LIMIT 5')
    recent = c.fetchall()
    
    message = '📊 GELİR/GİDER RAPORU\n\n'
    message += '📦 KARGO\n'
    message += f'Gelir: {kargo_gelir:.2f} AZN\n'
    message += f'Gider: {kargo_gider:.2f} AZN\n'
    message += f'Net: {(kargo_gelir - kargo_gider):.2f} AZN\n\n'
    
    message += '⛽ YAKIT\n'
    message += f'Gelir: {yakit_gelir:.2f} AZN\n'
    message += f'Gider: {yakit_gider:.2f} AZN\n'
    message += f'Net: {(yakit_gelir - yakit_gider):.2f} AZN\n\n'
    
    if recent:
        message += '📋 SON 5 İŞLEM:\n'
        for r in recent:
            company_emoji = '📦' if r[0] == 'kargo' else '⛽'
            type_emoji = '💰' if r[1] == 'gelir' else '💸'
            message += f'{company_emoji} {type_emoji} {r[2]:.2f} AZN - {r[3]} ({r[4]})\n'
    
    await update.message.reply_text(message)

# EXCEL RAPORU
async def excel_rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🔍 excel_rapor çağrıldı!")  # DEBUG
    
    try:
        c = conn.cursor()
        
        c.execute('SELECT company, type, amount, category, person, customer_name, description, date FROM transactions ORDER BY date DESC')
        transactions = c.fetchall()
        
        print(f"📊 {len(transactions)} işlem bulundu")  # DEBUG
        
        if not transactions:
            await update.message.reply_text('❌ Henüz kayıt yok.')
            return
        
        df = pd.DataFrame(transactions, columns=['Şirket', 'Tür', 'Miktar (AZN)', 'Kategori', 'Kişi', 'Müşteri', 'Açıklama', 'Tarih'])
        
        filename = f'rapor_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        df.to_excel(filename, index=False, engine='openpyxl')
        
        print(f"📁 Dosya oluşturuldu: {filename}")  # DEBUG
        
        with open(filename, 'rb') as f:
            await update.message.reply_document(document=f, filename=filename)
        
        await update.message.reply_text('✅ Excel raporu hazırlandı!')
        
        print("✅ Excel gönderildi!")  # DEBUG
        
        try:
            os.remove(filename)
            print(f"🗑️ Dosya silindi: {filename}")  # DEBUG
        except:
            pass
            
    except Exception as e:
        print(f"❌ HATA: {str(e)}")  # DEBUG
        await update.message.reply_text(f'❌ Hata: {str(e)}')
# İPTAL
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text('❌ İşlem iptal edildi.')
    await start(update, context)
    return ConversationHandler.END

# MAIN
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Conversation Handler'ları tanımla
    paket_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^📦 Paket Ekle$'), paket_ekle_start)],
        states={
            PACKAGE_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, paket_ekle_save)],
        },
        fallbacks=[
            MessageHandler(filters.Regex('^🔙 İptal$'), cancel),
            MessageHandler(filters.Regex('^🔙 Ana Menü$'), start)
        ]
    )
    
    litre_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex('^⛽ Litre Ekle$'), litre_ekle_start)],
        states={
            LITER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, litre_ekle_save)],
        },
        fallbacks=[
            MessageHandler(filters.Regex('^🔙 İptal$'), cancel),
            MessageHandler(filters.Regex('^🔙 Ana Menü$'), start)
        ]
    )
    
    transaction_conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex('^💰 Gelir Ekle$'), gelir_ekle_start),
            MessageHandler(filters.Regex('^💸 Gider Ekle$'), gider_ekle_start),
        ],
        states={
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler)],
            CUSTOMER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, customer_name_handler)],
            AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, amount_handler)],
            PERSON: [MessageHandler(filters.TEXT & ~filters.COMMAND, person_handler)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler)],
        },
        fallbacks=[
            MessageHandler(filters.Regex('^🔙 İptal$'), cancel),
            MessageHandler(filters.Regex('^🔙 Ana Menü$'), start)
        ]
    )
    
    # 1. ÖNCE: Command handler
    app.add_handler(CommandHandler('start', start))
    
    # 2. SONRA: Conversation handler'lar
    app.add_handler(paket_conv)
    app.add_handler(litre_conv)
    app.add_handler(transaction_conv)
    
    # 3. EN SON: Basit buton handler'ları
    app.add_handler(MessageHandler(filters.Regex('^📦 Kargo İşlemleri$'), kargo_menu))
    app.add_handler(MessageHandler(filters.Regex('^⛽ Yakıt İşlemleri$'), yakit_menu))
    app.add_handler(MessageHandler(filters.Regex('^💰 Bakiye$'), bakiye))
    app.add_handler(MessageHandler(filters.Regex('^📊 Raporlar$'), raporlar_menu))
    app.add_handler(MessageHandler(filters.Regex('^📦 Paket Raporu$'), paket_raporu))
    app.add_handler(MessageHandler(filters.Regex('^⛽ Litre Raporu$'), litre_raporu))
    app.add_handler(MessageHandler(filters.Regex('^📊 Gelir/Gider Raporu$'), gelir_gider_raporu))
    app.add_handler(MessageHandler(filters.Regex('^📥 Excel İndir$'), excel_rapor))
    app.add_handler(MessageHandler(filters.Regex('^🔙 Ana Menü$'), start))
    
    print('🤖 Bot çalışıyor...')
    app.run_polling()

if __name__ == '__main__':
    main()