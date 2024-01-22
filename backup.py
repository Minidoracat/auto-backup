from apscheduler.schedulers.background import BackgroundScheduler
import os
import shutil
import json
import time
from datetime import datetime
import tarfile

def load_config():
    # 優先從環境變量讀取配置
    config = {
        "source_directory": os.getenv("SOURCE_DIRECTORY"),
        "target_directory": os.getenv("TARGET_DIRECTORY"),
        "backup_count": os.getenv("BACKUP_COUNT"),
        "compress": os.getenv("COMPRESS", "false").lower() in ["true", "1", "t"],
        "compress_format": os.getenv("COMPRESS_FORMAT", "zip"),  # 新增壓縮格式選項
        "schedule_mode": os.getenv("SCHEDULE_MODE", "interval"),  # 默認為間隔模式
        "cron_hour": os.getenv("CRON_HOUR", "0"),
        "cron_minute": os.getenv("CRON_MINUTE", "0"),
        "interval_hours": os.getenv("INTERVAL_HOURS", "24"),  # 默認間隔24小時
        "interval_minutes": os.getenv("INTERVAL_MINUTES", "0")  # 新增間隔分鐘數
    }

    # 如果缺少任何必要的環境變量，則從 config.json 加載配置
    if not all(value is not None for value in [config["source_directory"], config["target_directory"], config["backup_count"]]):
        print("從 config.json 加載配置...")
        with open("config.json", "r") as file:
            config_from_file = json.load(file)
            config.update({k: config_from_file.get(k, v) for k, v in config.items()})

    # 確保數字類型的配置項正確轉換
    config["backup_count"] = int(config["backup_count"])
    config["cron_hour"] = int(config["cron_hour"])
    config["cron_minute"] = int(config["cron_minute"])
    config["interval_hours"] = int(config["interval_hours"])
    config["interval_minutes"] = int(config["interval_minutes"])  # 轉換間隔分鐘數

    return config

def backup_files(source, target, compress, compress_format):
    now = datetime.now()
    date_stamp = now.strftime("%Y-%m-%d")
    time_stamp = now.strftime("%H-%M")
    target_date_path = os.path.join(target, date_stamp)
    os.makedirs(target_date_path, exist_ok=True)  # 確保當天的資料夾存在

    if compress:
        # 壓縮時，將檔案放在當天日期的資料夾內，檔名包含時間戳
        archive_name = os.path.join(target_date_path, f"backup-{date_stamp}_{time_stamp}")  # 加入時間戳
        if compress_format == "zip":
            shutil.make_archive(archive_name, 'zip', source)
        elif compress_format == "tar.gz":
            with tarfile.open(f"{archive_name}.tar.gz", "w:gz") as tar:
                for item in os.listdir(source):
                    tar.add(os.path.join(source, item), arcname=item)
    else:
        # 如果不壓縮，創建一個以時間戳命名的資料夾來存放備份
        target_time_path = os.path.join(target_date_path, time_stamp)
        os.makedirs(target_time_path, exist_ok=True)
        for item in os.listdir(source):
            s_item = os.path.join(source, item)
            d_item = os.path.join(target_time_path, item)
            if os.path.isdir(s_item):
                shutil.copytree(s_item, d_item, dirs_exist_ok=True)
            else:
                shutil.copy2(s_item, d_item)


def clean_old_backups(target, backup_count):
    all_backups = sorted([os.path.join(target, d) for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))], key=os.path.getmtime)
    while len(all_backups) > backup_count:
        old_backup = all_backups.pop(0)
        shutil.rmtree(old_backup)

def scheduled_backup():
    config = load_config()
    backup_files(config['source_directory'], config['target_directory'], config['compress'], config['compress_format'])
    clean_old_backups(config['target_directory'], config['backup_count'])

def main():
    config = load_config()
    scheduler = BackgroundScheduler()
    
    # 根據配置的排程模式添加任務
    if config['schedule_mode'] == 'cron':
        scheduler.add_job(scheduled_backup, 'cron', hour=config['cron_hour'], minute=config['cron_minute'])
    elif config['schedule_mode'] == 'interval':
        # 支持小時和分鐘的間隔設定
        scheduler.add_job(scheduled_backup, 'interval', hours=config['interval_hours'], minutes=config['interval_minutes'])

    # 啟動排程器
    scheduler.start()
    
    # 程式啟動時立即執行一次備份，以確認功能正常
    scheduled_backup()
    
    try:
        # 保持腳本運行
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        # 收到中斷信號時關閉排程器
        scheduler.shutdown()

if __name__ == "__main__":
    main()
