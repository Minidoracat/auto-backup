FROM python:3.9-slim

# 設定工作目錄
WORKDIR /app

# 安裝虛擬環境
RUN pip install --upgrade pip && \
    pip install virtualenv && \
    virtualenv venv

# 啟用虛擬環境
ENV PATH="/app/venv/bin:$PATH"

# 複製依賴檔案到容器中
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製專案檔案到容器中
COPY config.json .
COPY . .

# 執行備份腳本
CMD ["python", "./backup.py"]
