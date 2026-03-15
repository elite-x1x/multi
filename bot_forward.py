import logging
import json
import os
import asyncio
import random
import hashlib
from datetime import datetime, timedelta
from telegram import Update, InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import threading

# === KONFIGURASI SUPER ===
BOT_TOKEN = "token_bot"
TARGET_CHAT_ID = 12345
SENT_MEDIA_FILE = "sent_media.json"
PENDING_MEDIA_FILE = "pending_media.json"  # Simpan media yang ditunda karena daily limit

# === RATE LIMIT SETTINGS ===
DELAY_BETWEEN_SEND   = 2.0   # Minimal 2 detik antar pesan
DELAY_RANDOM_MIN     = 0.5   # Tambahan delay random minimal
DELAY_RANDOM_MAX     = 2.5   # Tambahan delay random maksimal
GROUP_SIZE           = 10    # Kirim 10 media sekaligus
DELAY_BETWEEN_GROUP  = 35    # 35 detik antar kelompok
WAIT_TIME            = 10    # Tunggu 10 detik sebelum kirim
BATCH_PAUSE_EVERY    = 50    # Jeda panjang setiap 50 file
BATCH_PAUSE_MIN      = 480   # Minimal 8 menit (480 detik)
BATCH_PAUSE_MAX      = 900   # Maksimal 15 menit (900 detik)
DAILY_LIMIT          = 2000  # Maksimal 2000 file per hari
MAX_RETRIES          = 5
MAX_QUEUE_SIZE       = 5000  # Batas maksimal antrian: 5000 media items

# === SETUP LOG ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot_log.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# === GLOBAL VARIABLE ===
sent_media = set()
sent_file_ids = set()
media_queue = []
pending_media = []  # Media yang ditunda karena daily limit
is_sending = False
daily_count = 0
daily_reset_date = datetime.now().date()
queue_lock = threading.Lock()  # Gunakan threading.Lock() untuk thread safety

# === LOAD & SAVE FILE ===
def load_sent_media():
    if os.path.exists(SENT_MEDIA_FILE):
        try:
            with open(SENT_MEDIA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    hashes   = set(data.get("hashes", []))
                    file_ids = set(data.get("file_ids", []))
                    return hashes, file_ids
        except Exception as e:
            logging.error(f"Error membaca sent_media.json: {e}")
    return set(), set()

def save_sent_media():
    try:
        data = {
            "hashes": list(sent_media),
            "file_ids": list(sent_file_ids)
        }
        with open(SENT_MEDIA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logging.error(f"Error menyimpan sent_media.json: {e}")

def load_pending_media():
    if os.path.exists(PENDING_MEDIA_FILE):
        try:
            with open(PENDING_MEDIA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    # Format: [[file_id, media_type, fingerprint_dict], ...]
                    return [(item, item, item) for item in data if len(item) == 3]
        except Exception as e:
            logging.error(f"Error membaca pending_media.json: {e}")
    return []

def save_pending_media():
    try:
        # Format: [[file_id, media_type, fingerprint_dict], ...]
        serializable = [[item, item, item] for item in pending_media]
        with open(PENDING_MEDIA_FILE, "w", encoding="utf-8") as f:
            json.dump(serializable, f, indent=2)
    except Exception as e:
        logging.error(f"Error menyimpan pending_media.json: {e}")

# === DAILY LIMIT RESET ===
def check_daily_reset():
    global daily_count, daily_reset_date
    today = datetime.now().date()
    if today != daily_reset_date:
        logging.info(f"✅ Reset daily count. Kemarin terkirim: {daily_count}")
        daily_count = 0
        daily_reset_date = today
        
        loaded_pending = load_pending_media()
        if loaded_pending:
            logging.info(f"🔄 Memuat ulang {len(loaded_pending)} media yang tertunda...")
            new_pending = []
            for item in loaded_pending:
                file_id, media_type, fingerprint = item
                if not is_duplicate(fingerprint):
                    new_pending.append(item)
                else:
                    logging.info(f"[SKIP] Duplikat di pending: {file_id}")
            
            with queue_lock:  # <-- LOCK DI SINI
                media_queue.extend(new_pending)
                pending_media.clear()  # <-- CLEAR DI DALAM LOCK
            save_pending_media()

# === BUAT HASH FINGERPRINT ===
def make_hash(fingerprint):
    fp_copy = {k: v for k, v in fingerprint.items() if k != 'file_id'}
    fingerprint_str = json.dumps(fp_copy, sort_keys=True)
    return hashlib.md5(fingerprint_str.encode()).hexdigest()

# === DETEKSI DUPLIKAT ===
def get_media_fingerprint(msg):
    fingerprint = {}

    if msg.photo:
        photo = msg.photo[-1]
        fingerprint = {
            'type': 'photo',
            'width': photo.width,
            'height': photo.height,
            'file_size': photo.file_size,
            'file_id': photo.file_id
        }
    elif msg.video:
        fingerprint = {
            'type': 'video',
            'duration': msg.video.duration,
            'width': msg.video.width,
            'height': msg.video.height,
            'file_size': msg.video.file_size,
            'file_id': msg.video.file_id
        }
    elif msg.document:
        fingerprint = {
            'type': 'document',
            'file_name': msg.document.file_name,
            'file_size': msg.document.file_size,
            'mime_type': msg.document.mime_type,
            'file_id': msg.document.file_id
        }
    elif msg.audio:
        fingerprint = {
            'type': 'audio',
            'duration': msg.audio.duration,
            'file_size': msg.audio.file_size,
            'mime_type': msg.audio.mime_type,
            'file_id': msg.audio.file_id
        }
    elif msg.voice:
        fingerprint = {
            'type': 'voice',
            'duration': msg.voice.duration,
            'file_size': msg.voice.file_size,
            'file_id': msg.voice.file_id
        }
    elif msg.sticker:
        fingerprint = {
            'type': 'sticker',
            'width': msg.sticker.width,
            'height': msg.sticker.height,
            'file_size': msg.sticker.file_size,
            'file_id': msg.sticker.file_id
        }
    elif msg.video_note:
        fingerprint = {
            'type': 'video_note',
            'duration': msg.video_note.duration,
            'length': msg.video_note.length,
            'file_size': msg.video_note.file_size,
            'file_id': msg.video_note.file_id
        }

    return fingerprint

def is_duplicate(fingerprint):
    if not fingerprint:
        return False

    # Lapis 1: Cek file_id
    file_id = fingerprint.get('file_id', '')
    if file_id in sent_file_ids:
        logging.info(f"[SKIP] Duplikat file_id: {file_id}")
        return True

    # Lapis 2: Cek hash konten
    fp_hash = make_hash(fingerprint)
    if fp_hash in sent_media:
        logging.info(f"[SKIP] Duplikat konten: {file_id}")
        return True

    # Lapis 3: Cek di queue (dengan lock)
    with queue_lock:
        for item in media_queue:
            q_file_id, _, q_fp = item
            if q_file_id == file_id or make_hash(q_fp) == fp_hash:
                logging.info(f"[SKIP] Sudah ada di queue: {file_id}")
                return True

    # Lapis 4: Cek di pending_media (dengan lock)
    with queue_lock:
        for item in pending_media:
            q_file_id, _, q_fp = item
            if q_file_id == file_id or make_hash(q_fp) == fp_hash:
                logging.info(f"[SKIP] Sudah ada di pending: {file_id}")
                return True

    return False

def add_to_sent_media(fingerprint):
    if not fingerprint:
        return
    fp_hash = make_hash(fingerprint)
    sent_media.add(fp_hash)
    file_id = fingerprint.get('file_id', '')
    if file_id:
        sent_file_ids.add(file_id)

# === FUNGSI KIRIM MEDIA GROUP ===
async def send_media_group_with_retry(bot, chat_id, media_items, max_retries=MAX_RETRIES):
    """Kirim media sebagai grup (bersebelahan seperti folder)"""
    for attempt in range(max_retries):
        try:
            input_media = []
            
            for file_id, media_type in media_items:
                if media_type == "photo":
                    input_media.append(InputMediaPhoto(media=file_id))
                elif media_type == "video":
                    input_media.append(InputMediaVideo(media=file_id))
                elif media_type == "document":
                    input_media.append(InputMediaDocument(media=file_id))
                elif media_type == "audio":
                    input_media.append(InputMediaAudio(media=file_id))
            
            if input_media:
                await bot.send_media_group(chat_id=chat_id, media=input_media)
                logging.info(f"[✓] Media group ({len(input_media)} item) dikirim (attempt {attempt + 1})")
                return True

        except Exception as e:
            err = str(e)

            # Handle Flood Control
            if "Flood control" in err or "Too Many Requests" in err:
                try:
                    wait_time = int(err.split("Retry in ")[-1].split(" seconds")) + 5
                except:
                    wait_time = 120
                logging.warning(f"[!] Flood control! Tunggu {wait_time} detik...")
                await asyncio.sleep(wait_time)

            # Handle Timeout
            elif "Timed out" in err or "timeout" in err.lower():
                wait = 30 * (attempt + 1)  # Makin lama tiap retry
                logging.warning(f"[!] Timeout. Tunggu {wait} detik...")
                await asyncio.sleep(wait)

            # Handle Chat tidak ditemukan / banned
            elif "chat not found" in err.lower() or "forbidden" in err.lower():
                logging.error(f"[!!!] Bot diblokir atau grup tidak ditemukan: {err}")
                return False

            # Handle Retry After
            elif "retry after" in err.lower():
                try:
                    wait_time = int(err.lower().split("retry after ")[-1].split(" ")) + 5
                except:
                    wait_time = 120
                logging.warning(f"[!] Retry after {wait_time} detik...")
                await asyncio.sleep(wait_time)

            # Handle Media Invalid / Not Found
            elif "invalid file" in err.lower() or "not found" in err.lower():
                logging.warning(f"[!] File tidak valid atau sudah dihapus: {err}")
                return False  # Skip grup ini, jangan retry

            # Handle Rate Limit (Telegram API)
            elif "rate limit" in err.lower():
                wait_time = 60 + random.randint(10, 30)
                logging.warning(f"[!] Rate limit terdeteksi. Tunggu {wait_time} detik...")
                await asyncio.sleep(wait_time)

            else:
                # Exponential backoff + random jitter
                wait = min(60, (2 ** attempt) * 5 + random.uniform(1, 5))
                logging.error(f"[!] Error (attempt {attempt + 1}): {err}")
                logging.info(f"    Tunggu {wait:.1f} detik...")
                await asyncio.sleep(wait)

                if attempt == max_retries - 1:
                    return False

    return False

# === BACKGROUND WORKER ===
async def queue_worker(bot):
    global media_queue, is_sending, daily_count, pending_media

    while True:
        await asyncio.sleep(WAIT_TIME)

        # Reset daily counter jika hari baru
        check_daily_reset()

        if not media_queue or is_sending:
            continue

        # Cek daily limit
        if daily_count >= DAILY_LIMIT:
            logging.warning(f"[!] Daily limit tercapai ({DAILY_LIMIT}). Tunggu besok.")
            continue

        # Batasi ukuran antrian untuk mencegah memori penuh
        with queue_lock:
            if len(media_queue) > MAX_QUEUE_SIZE:
                logging.warning(f"[!] Antrian melebihi {MAX_QUEUE_SIZE}. Menghapus 10% terlama...")
                media_queue = media_queue[int(len(media_queue) * 0.1):]  # Hapus 10% awal

        is_sending = True
        
        # Ambil batch dengan lock
        with queue_lock:
            batch = media_queue.copy()
            media_queue.clear()

        total = len(batch)
        logging.info(f"=== Mulai kirim {total} media ===")
        logging.info(f"=== Daily count: {daily_count}/{DAILY_LIMIT} ===")

        sent_count = 0
        failed_items = []  # Simpan item yang gagal

        for i in range(0, total, GROUP_SIZE):
            # Cek daily limit di setiap kelompok
            check_daily_reset()
            if daily_count >= DAILY_LIMIT:
                logging.warning(f"[!] Daily limit tercapai. Sisa {total - i} file ditunda ke esok hari.")
                # Simpan sisa ke pending_media
                with queue_lock:
                    pending_media.extend(batch[i:])
                save_pending_media()
                break

            group = batch[i:i + GROUP_SIZE]
            group_num = (i // GROUP_SIZE) + 1
            logging.info(f"--- Kelompok {group_num}/{(total + GROUP_SIZE - 1) // GROUP_SIZE}: {len(group)} media ---")

            # Siapkan media untuk dikirim sebagai group
            media_group_items = []
            for file_id, media_type, fingerprint in group:
                # Double check duplikat sebelum kirim
                if is_duplicate(fingerprint):
                    logging.info(f"[SKIP] Duplikat saat kirim: {file_id}")
                    continue

                media_group_items.append((file_id, media_type))
                add_to_sent_media(fingerprint)  # Tandai sebagai sudah dikirim

            # Kirim sebagai group
            if media_group_items:
                success = await send_media_group_with_retry(bot, TARGET_CHAT_ID, media_group_items)

                if success:
                    save_sent_media()
                    daily_count += len(media_group_items)
                    sent_count += len(media_group_items)
                    logging.info(f"[✓] Terkirim {sent_count}/{total} | Daily: {daily_count}/{DAILY_LIMIT}")
                else:
                    logging.error(f"[✗] Gagal kirim group: {len(media_group_items)} media")
                    # Simpan ke pending_media agar tidak hilang
                    for item in group:
                        file_id, media_type, fingerprint = item
                        if not is_duplicate(fingerprint):
                            failed_items.append((file_id, media_type, fingerprint))

            # Delay acak antar kelompok
            delay = DELAY_BETWEEN_SEND + random.uniform(DELAY_RANDOM_MIN, DELAY_RANDOM_MAX)
            logging.info(f"    Delay {delay:.1f} detik...")
            await asyncio.sleep(delay)

            # Jeda panjang setiap BATCH_PAUSE_EVERY file
            if sent_count > 0 and sent_count % BATCH_PAUSE_EVERY == 0:
                pause_duration = random.uniform(BATCH_PAUSE_MIN, BATCH_PAUSE_MAX)
                logging.info(
                    f"--- [JEDA PANJANG] {pause_duration:.0f} detik "
                    f"({pause_duration/60:.1f} menit) setelah {sent_count} file ---"
                )
                await asyncio.sleep(pause_duration)
            else:
                # Jeda normal antar kelompok
                logging.info(f"--- Kelompok {group_num} selesai. Jeda {DELAY_BETWEEN_GROUP} detik ---")
                await asyncio.sleep(DELAY_BETWEEN_GROUP)

        # Simpan item yang gagal
        if failed_items:
            with queue_lock:
                pending_media.extend(failed_items)
            save_pending_media()

        logging.info(f"=== Selesai! Terkirim {sent_count}/{total} media ===")
        is_sending = False  # Selalu reset, meski error

# === HANDLER UTAMA ===
async def forward_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if msg is None:
        return

    fingerprint = get_media_fingerprint(msg)
    if not fingerprint:
        return

    if is_duplicate(fingerprint):
        return

    file_id = fingerprint.get('file_id')
    media_type = fingerprint.get('type')

    if not file_id or not media_type:
        return

    # Batasi antrian agar tidak membanjiri memori
    with queue_lock:
        if len(media_queue) >= MAX_QUEUE_SIZE:
            logging.warning(f"[!] Antrian penuh ({MAX_QUEUE_SIZE}). Mengabaikan media baru.")
            return

        media_queue.append((file_id, media_type, fingerprint))
    
    logging.info(
        f"[+] {media_type} masuk queue | "
        f"Ukuran: {fingerprint.get('file_size', 0):,} bytes | "
        f"Durasi: {fingerprint.get('duration', '-')} detik | "
        f"Total antrian: {len(media_queue)}"
    )

# === START WORKER ===
async def on_startup(app):
    global sent_media, sent_file_ids, pending_media
    sent_media, sent_file_ids = load_sent_media()
    pending_media = load_pending_media()
    
    # Muat pending media jika hari baru
    check_daily_reset()
    
    logging.info("Worker queue dimulai...")
    asyncio.create_task(queue_worker(app.bot))

# === MAIN ===
def main():
    global sent_media, sent_file_ids, pending_media
    sent_media, sent_file_ids = load_sent_media()
    pending_media = load_pending_media()
    
    # Muat ulang pending media jika hari baru
    check_daily_reset()

    logging.info(f"Total media sudah terkirim sebelumnya: {len(sent_file_ids)}")
    logging.info(f"Total hash tersimpan: {len(sent_media)}")
    logging.info(f"Media tertunda: {len(pending_media)}")

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()
    app.add_handler(MessageHandler(filters.ALL, forward_media))

    logging.info(f"╔══════════════════════════════════════╗")
    logging.info(f"║         BOT FORWARD MEDIA v.0.5.1           ║")
    logging.info(f"╠══════════════════════════════════════╣")
    logging.info(f"║ Kumpul media  : {WAIT_TIME} detik            ║")
    logging.info(f"║ Kirim per     : {GROUP_SIZE} media/kelompok      ║")
    logging.info(f"║ Delay kirim   : {DELAY_BETWEEN_SEND}s + random          ║")
    logging.info(f"║ Jeda kelompok : {DELAY_BETWEEN_GROUP} detik             ║")
    logging.info(f"║ Jeda panjang  : {BATCH_PAUSE_MIN}-{BATCH_PAUSE_MAX}s / {BATCH_PAUSE_EVERY} file  ║")
    logging.info(f"║ Daily limit   : {DAILY_LIMIT} file/hari          ║")
    logging.info(f"║ Max queue     : {MAX_QUEUE_SIZE} media          ║")
    logging.info(f"╚══════════════════════════════════════╝")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True  # Abaikan pesan lama saat bot restart
    )

if __name__ == "__main__":
    main()