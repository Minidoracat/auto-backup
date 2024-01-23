from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import os
import shutil
import json
import time
from datetime import datetime
import tarfile


def load_config():
    print("正在加載配置...")
    with open("config.json", "r") as file:
        config = json.load(file)
    print(f"配置加載完成: {config}")
    return config

def backup_files(source, target, compress, compress_format):
    print("開始執行備份...")
    now = datetime.now()
    date_stamp = now.strftime("%Y-%m-%d")
    time_stamp = now.strftime("%H-%M-%S")
    target_date_path = os.path.join(target, date_stamp)
    os.makedirs(target_date_path, exist_ok=True)

    archive_name = os.path.join(target_date_path, f"backup-{date_stamp}_{time_stamp}")
    if compress:
        archive_path = f"{archive_name}.{compress_format}"
        print(f"正在壓縮檔案至 {archive_path}")
        if compress_format == "tar.gz":
            with tarfile.open(f"{archive_path}", "w:gz") as tar:
                tar.add(source, arcname=os.path.basename(source))
        elif compress_format == "zip":
            shutil.make_archive(archive_name, 'zip', source)
    else:
        # 直接複製檔案
        shutil.copytree(source, archive_name, dirs_exist_ok=True)
    print("備份完成。")

def clean_old_backups(target, backup_count):
    print("開始清理舊的備份...")
    all_backups = sorted([d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))], key=lambda d: os.path.getmtime(os.path.join(target, d)))
    while len(all_backups) > backup_count:
        old_backup = all_backups.pop(0)
        shutil.rmtree(os.path.join(target, old_backup))
        print(f"已刪除舊備份：{old_backup}")
    print("舊備份清理完成。")

def scheduled_backup():
    print("執行排程備份...")
    config = load_config()
    backup_files(config['source_directory'], config['target_directory'], config['compress'], config['compress_format'])
    clean_old_backups(config['target_directory'], config['backup_count'])

    
def main():
    print("主程序開始...")
    config = load_config()
    scheduler = BackgroundScheduler()
    
    if config['schedule_mode'] == 'cron':
        scheduler.add_job(scheduled_backup, CronTrigger(**config['schedule']['cron']))
    elif config['schedule_mode'] == 'interval':
        scheduler.add_job(scheduled_backup, IntervalTrigger(**config['schedule']['interval']))

    scheduler.start()
    
    scheduled_backup()  # 程式啟動時立即執行一次備份
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()
