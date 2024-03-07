# **自動備份系統**

## **專案描述**

這是一個用於自動備份特定目錄檔案的 Python 專案。它支持定時備份、檔案壓縮以及透過 Docker Compose 進行容器化部署。

## **配置說明**

您可以通過編輯 **`config.json`** 檔案或設置環境變量來配置備份系統。配置選項包括：

- **`source_directory`**: 要備份的源目錄路徑。
- **`target_directory`**: 備份檔案存儲的目標目錄路徑。
- **`backup_count`**: 保留的備份數量。超過此數量，最舊的備份將被刪除。
- **`compress`**: 是否壓縮備份檔案。
- **`compress_format`**: 壓縮格式，例如 "zip" 或 "tar.gz"。
- **`schedule_mode`**: 排程模式，可選 "cron" 或 "interval"。
- **`schedule`**: 根據選擇的 **`schedule_mode`**，設置具體的排程參數。

### **Cron 配置**

- 使用 **`cron`** 模式時，您可以通過 `schedule_time` 以 "HH:MM" 格式指定具體的執行時間。例如，`"schedule_time": "01:00"` 將在每天的 01:00 執行備份。

### **Interval 配置**

- 使用 **`interval`** 模式，您可以設置任務執行的間隔時間。例如：
    - **`days`**: 天數間隔
    - **`hours`**: 小時數間隔
    - **`minutes`**: 分鐘數間隔
    - **`seconds`**: 秒數間隔
    - 例如，設置為 **`{"hours": 1}`** 將每小時執行一次備份。

## **使用方法**

### **透過 Python 直接運行**

1. 確保已安裝 Python 和必要的依賴。
2. 修改 **`config.json`** 中的設定以符合您的需求。
3. 執行 **`python backup.py`** 啟動備份任務。

### **使用 Docker Compose 部署**

1. 確保您的系統已安裝 Docker 和 Docker Compose。
2. 創建或更新 **`config.json`** 文件以符合您的需求，並確保它與 Dockerfile 在同一目錄中。
3. 根據需要調整 **`docker-compose.yml`** 文件中的服務設定，尤其是源目錄和目標備份目錄的卷映射，以及環境變量的配置。
4. 運行 **`docker-compose up -d`** 來啟動服務。使用 **`d`** 參數將服務放到背景運行。
5. 若要停止並移除容器，運行 **`docker-compose down`**。

## **Docker Compose 詳細配置**

您可以在 **`docker-compose.yml`** 文件中設置以下選項：

```yaml
version: '3.8'
services:
  auto_backup:
    #  for testing 
    # build: .
    image: minidoracat/auto-backup:latest
    volumes:
      - /etc/localtime:/etc/localtime:ro
      - /path/to/source:/app/source
      - /path/to/backup:/app/backup
      - ./config.json:/app/config.json
    environment:
      - TZ=Asia/Taipei # 時區


## **注意事項**

- 確保在啟動容器之前已正確設置了所有必要的環境變量或 **`config.json`** 檔案中的配置。
- 當使用 Docker Compose 運行時，源目錄和目標備份目錄必須是絕對路徑，且對應到您的宿主機上的實際目錄。
- **`config.json`** 應放在 Dockerfile 所在的同一目錄中，以便在構建鏡像時被正確複製到容器中。