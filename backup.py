import shutil
import time
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
    """設置日誌保存的目錄和保留日誌的數量"""
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
    """從 config.json 加載配置"""
    logging.info("正在加載配置...")
    with open("config.json", "r") as file:
        config = json.load(file)
    logging.info(f"配置加載完成: {config}")
    return config

def reload_config():
    """重新加載全局配置"""
    global global_config
    global_config = load_config()
    
def parse_schedule_times(time_str_list):
    """解析時間字符串列表為 cron 格式"""
    return [{"hour": part.split(':')[0], "minute": part.split(':')[1]} for part in time_str_list]

def backup_files():
    """進行備份操作"""
    start_time = datetime.now()
    date_stamp = start_time.strftime('%Y-%m-%d')
    target_date_path = os.path.join(global_config['target_directory'], date_stamp)
    os.makedirs(target_date_path, exist_ok=True)

    logging.info(f"開始執行備份... 時間: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    total_files_count = 0  # 初始化檔案計數器
    total_size_bytes = 0  # 初始化總大小計算器

    if global_config['compress']:
        archive_path = f"{os.path.join(target_date_path, 'backup_' + start_time.strftime('%Y-%m-%d_%H-%M-%S'))}.tar.gz"
        tar_command = ['tar', '-czf', archive_path]

        for directory in global_config['source_directories']:
            if os.path.isdir(directory):
                # 計算檔案數量和大小
                for root, dirs, files in os.walk(directory):
                    total_files_count += len(files)
                    total_size_bytes += sum(os.path.getsize(os.path.join(root, name)) for name in files)
                tar_command.extend(['-C', os.path.dirname(directory), os.path.basename(directory)])
            else:
                logging.warning(f"指定的目錄不存在: {directory}")

        try:
            subprocess.run(tar_command, check=True)
            logging.info(f"壓縮完成: {archive_path}, 檔案數量: {total_files_count}, 大小: {(total_size_bytes / (1024*1024)):.2f} MB")
        except subprocess.CalledProcessError as e:
            logging.error(f"壓縮過程中出錯: {e}")
    else:
        # 直接複製模式
        for directory in global_config['source_directories']:
            if os.path.isdir(directory):
                destination_path = os.path.join(target_date_path, os.path.basename(directory))
                shutil.copytree(directory, destination_path)
                for root, dirs, files in os.walk(directory):
                    total_files_count += len(files)
                    total_size_bytes += sum(os.path.getsize(os.path.join(root, name)) for name in files)
                logging.info(f"複製完成: {directory} 到 {destination_path}")
            else:
                logging.warning(f"指定的目錄不存在: {directory}")

    end_time = datetime.now()
    duration = end_time - start_time
    logging.info(f"備份完成。檔案數量: {total_files_count}, 總大小: {(total_size_bytes / (1024*1024)):.2f} MB, 耗時: {duration}")

def clean_old_backups(target, backup_count):
    """清理舊的備份文件"""
    logging.info("開始清理舊的備份...")
    all_backup_dates = [d for d in os.listdir(target) if os.path.isdir(os.path.join(target, d))]
    all_backup_dates.sort()

    # 保留最新的 backup_count 個備份
    while len(all_backup_dates) > backup_count:
        old_backup = all_backup_dates.pop(0)
        shutil.rmtree(os.path.join(target, old_backup))
        logging.info(f"已刪除舊備份：{old_backup}")

    logging.info("舊備份清理完成。")

def scheduled_backup():
    """設置定時備份任務"""
    logging.info("執行排程備份...")
    reload_config()
    backup_files()
    clean_old_backups(global_config['target_directory'], global_config['backup_count'])

def main():
    """主函數入口"""
    reload_config()
    setup_logging(global_config['log_directory'], global_config['log_count'])
    logging.info("主程序開始...")
    scheduler = BackgroundScheduler()

    if global_config['schedule_mode'] == 'cron':
        schedule_times = parse_schedule_times(global_config['schedule']['cron']['schedule_time'])
        for schedule_time in schedule_times:
            scheduler.add_job(scheduled_backup, CronTrigger(hour=schedule_time['hour'], minute=schedule_time['minute']))
    elif global_config['schedule_mode'] == 'interval':
        scheduler.add_job(scheduled_backup, IntervalTrigger(days=global_config['schedule']['interval']['days'], hours=global_config['schedule']['interval']['hours'], minutes=global_config['schedule']['interval']['minutes'], seconds=global_config['schedule']['interval']['seconds']))
    
    scheduler.start()
    
    scheduled_backup()  # 程序啟動時立即執行一次備份
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()

if __name__ == "__main__":
    main()
