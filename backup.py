import os
import shutil
import json
import schedule
import time
from datetime import datetime

def load_config():
    # 嘗試從環境變量讀取配置
    config = {
        "source_directory": os.getenv("SOURCE_DIRECTORY"),
        "target_directory": os.getenv("TARGET_DIRECTORY"),
        "backup_count": os.getenv("BACKUP_COUNT"),
        "backup_frequency_hours": os.getenv("BACKUP_FREQUENCY_HOURS"),
        "compress": os.getenv("COMPRESS"),
    }

    # 檢查是否所有必要配置都從環境變量讀取到了，否則從 config.json 讀取
    if not all(config.values()):
        print("某些環境變量未設定，正在從 config.json 讀取配置...")
        with open("config.json", "r") as file:
            config = json.load(file)
    else:
        # 環境變量是字串，需要將相關值轉換為正確的類型
        config["backup_count"] = int(config["backup_count"])
        config["backup_frequency_hours"] = int(config["backup_frequency_hours"])
        config["compress"] = config["compress"].lower() in ["true", "1", "t"]
    
    return config

def backup_files(source, target, compress):
    now = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
    target = os.path.join(target, now)
    os.makedirs(target, exist_ok=True)
    if compress:
        shutil.make_archive(target, 'zip', source)
    else:
        shutil.copytree(source, target, dirs_exist_ok=True)

def clean_old_backups(target, backup_count):
    backups = sorted([os.path.join(target, d) for d in os.listdir(target)], key=os.path.getmtime)
    while len(backups) > backup_count:
        old_backup = backups.pop(0)
        if os.path.isdir(old_backup):
            shutil.rmtree(old_backup)
        else:
            os.remove(old_backup)

def main():
    config = load_config()
    schedule.every(config['backup_frequency_hours']).hours.do(
        backup_files,
        source=config['source_directory'],
        target=config['target_directory'],
        compress=config['compress']
    )
    schedule.every(config['backup_frequency_hours']).hours.do(
        clean_old_backups,
        target=config['target_directory'],
        backup_count=config['backup_count']
    )

    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
