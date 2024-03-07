from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import os
import shutil
import json
import time
from datetime import datetime
import tarfile
import logging
from logging.handlers import TimedRotatingFileHandler

# 初始化 logging
def setup_logging(log_directory, log_count):
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    # 根據當天日期建立日誌檔案名稱
    today = datetime.now().strftime("%Y-%m-%d")
    log_file_path = os.path.join(log_directory, f"{today}.log")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # 修改 TimedRotatingFileHandler 設定，使其每天根據日期分開日誌檔案
    file_handler = TimedRotatingFileHandler(log_file_path, when="D", interval=1, backupCount=log_count, utc=True)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(message)s'))
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)


# 定義全局變量用於存儲配置
global_config = None

def load_config():
    logging.info("正在加載配置...")
    with open("config.json", "r") as file:
        config = json.load(file)
    logging.info(f"配置加載完成: {config}")
    return config

def reload_config():
    global global_config
    global_config = load_config()
    
def parse_schedule_times(time_str_list):
    """將時間字符串列表 "HH:MM" 解析為多個 cron 格式的小時和分鐘"""
    return [{"hour": time_part.split(':')[0], "minute": time_part.split(':')[1]} for time_part in time_str_list]

def backup_files(source, target, compress, compress_format):
    start_time = datetime.now()
    logging.info(f"開始執行備份... 時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    file_count = 0  # 初始化檔案計數器
    date_stamp = start_time.strftime("%Y-%m-%d")
    time_stamp = start_time.strftime("%H-%M-%S")
    target_date_path = os.path.join(target, date_stamp)
    os.makedirs(target_date_path, exist_ok=True)

    archive_name = os.path.join(target_date_path, f"backup-{date_stamp}_{time_stamp}")
    if compress:
        archive_path = f"{archive_name}.{compress_format}"
        logging.info(f"正在壓縮檔案至 {archive_path}")
        if compress_format == "tar.gz":
            with tarfile.open(f"{archive_path}", "w:gz") as tar:
                for root, dirs, files in os.walk(source):
                    for file in files:
                        file_count += 1
                        tar.add(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), source))
        elif compress_format == "zip":
            shutil.make_archive(archive_name, 'zip', source)
    else:
        shutil.copytree(source, archive_name, dirs_exist_ok=True)
    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"備份完成。檔案數量: {file_count}，耗時: {duration}")

def clean_old_backups(target, backup_count):
    logging.info("開始清理舊的備份...")
    all_backups = sorted([d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))], key=lambda d: os.path.getmtime(os.path.join(target, d)))
    while len(all_backups) > backup_count:
        old_backup = all_backups.pop(0)
        shutil.rmtree(os.path.join(target, old_backup))
        logging.info(f"已刪除舊備份：{old_backup}")
    logging.info("舊備份清理完成。")

def scheduled_backup():
    logging.info("執行排程備份...")
    reload_config()  # 重新加載配置以使用最新設定
    backup_files(global_config['source_directory'], global_config['target_directory'], global_config['compress'], global_config['compress_format'])
    clean_old_backups(global_config['target_directory'], global_config['backup_count'])

def main():
    reload_config()  # 初始加載配置
    setup_logging(global_config['log_directory'], global_config['log_count'])  # 初始化 logging
    logging.info("主程序開始...")
    scheduler = BackgroundScheduler()
    
    if global_config['schedule_mode'] == 'cron':
        schedule_times = parse_schedule_times(global_config['schedule']['cron']['schedule_time'])
        for schedule_time in schedule_times:
            scheduler.add_job(scheduled_backup, CronTrigger(hour=schedule_time['hour'], minute=schedule_time['minute']))
    elif global_config['schedule_mode'] == 'interval':
        scheduler.add_job(scheduled_backup, IntervalTrigger(
            days=global_config['schedule']['interval']['days'],
            hours=global_config['schedule']['interval']['hours'],
            minutes=global_config['schedule']['interval']['minutes'],
            seconds=global_config['schedule']['interval']['seconds']
        ))
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()
