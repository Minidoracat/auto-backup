# 自動備份系統

## 專案描述
這是一個用於自動備份特定目錄檔案的 Python 專案。它支持定時備份、檔案壓縮以及透過 Docker Compose 進行容器化部署。

## 配置說明
您可以通過編輯 `config.json` 檔案或設置環境變量來配置備份系統。配置選項包括：

- `SOURCE_DIRECTORY`: 要備份的源目錄路徑。
- `TARGET_DIRECTORY`: 備份檔案存儲的目標目錄路徑。
- `BACKUP_COUNT`: 保留的備份數量。超過此數量，最舊的備份將被刪除。
- `BACKUP_FREQUENCY_HOURS`: 備份執行的頻率（以小時為單位）。
- `COMPRESS`: 是否壓縮備份檔案。

## 使用方法

### 透過 Python 直接運行

1. 確保已安裝 Python 和必要的依賴。
2. 修改 `config.json` 中的設定以符合您的需求。
3. 執行 `python backup.py` 啟動備份任務。

### 使用 Docker Compose 部署

1. 確保您的系統已安裝 Docker 和 Docker Compose。
2. 根據需要調整 `docker-compose.yml` 文件中的服務設定，尤其是源目錄和目標備份目錄的卷映射，以及環境變量的配置。
3. 運行 `docker-compose up -d` 來啟動服務。使用 `-d` 參數將服務放到背景運行。
4. 若要停止並移除容器，運行 `docker-compose down`。

## Docker Compose 詳細配置

您可以在 `docker-compose.yml` 文件中設置以下選項：

- `volumes`: 用於將源目錄和目標備份目錄從宿主機映射到容器內。請根據您的實際路徑進行調整。
- `environment`: 如果您選擇不使用 `config.json`，可以直接在這裡設置環境變量。

```yaml
version: '3.8'
services:
  backup_service:
    build: .
    environment:
      - SOURCE_DIRECTORY=/path/to/source
      - TARGET_DIRECTORY=/path/to/backup
      - BACKUP_COUNT=5
      - BACKUP_FREQUENCY_HOURS=1
      - COMPRESS=true
    volumes:
      - /path/to/source:/path/to/source
      - /path/to/backup:/path/to/backup

```
## 注意事項

- 確保在啟動容器之前已正確設置了所有必要的環境變量或 config.json 檔案中的配置。
- 當使用 Docker Compose 運行時，源目錄和目標備份目錄必須是絕對路徑，且對應到您的宿主機上的實際目錄。