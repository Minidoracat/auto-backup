import shutil
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import os
import json
from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
import subprocess

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

def backup_files():
    start_time = datetime.now()
    logging.info(f"開始執行備份... 時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    target_archive_path = os.path.join(global_config['target_directory'], f"backup_{start_time.strftime('%Y-%m-%d_%H-%M-%S')}")

    if global_config['compress']:
        # 壓縮模式
        archive_path = f"{target_archive_path}.tar.gz"
        tar_command = ['tar', '-czf', archive_path]

        for directory in global_config['source_directories']:
            tar_command.extend(['-C', os.path.dirname(directory), os.path.basename(directory)])
        
        try:
            subprocess.run(tar_command, check=True)
            logging.info(f"壓縮完成: {archive_path}")
        except subprocess.CalledProcessError as e:
            logging.error(f"壓縮過程中出錯: {e}")
    else:
        # 直接複製模式
        for directory in global_config['source_directories']:
            target_dir_path = os.path.join(target_archive_path, os.path.basename(directory))
            try:
                shutil.copytree(directory, target_dir_path)
                logging.info(f"複製完成: {directory} 到 {target_dir_path}")
            except Exception as e:
                logging.error(f"複製過程中出錯: {directory} 到 {target_dir_path}, 錯誤: {e}")

    end_time = datetime.now()
    duration = end_time - start_time

    if global_config['compress']:
        # 獲取壓縮檔大小
        total_size = os.path.getsize(archive_path)
        total_size_mb = total_size / (1024 * 1024)
        logging.info(f"備份完成。壓縮檔大小: {total_size_mb:.2f} MB，耗時: {duration}")
    else:
        logging.info(f"備份完成。耗時: {duration}")


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
    
    scheduled_backup()  # 程序啟動時立即執行一次備份
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()
