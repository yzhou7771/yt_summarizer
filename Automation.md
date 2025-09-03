# 📂 项目目录结构建议
YT_SUMMARIZER/
  ├─ yt_summarizer.py   # 已有的流水线脚本 (输入: YouTube 链接, 输出: 邮件)
  ├─ auto_runner.py     # 自动化检测 + 调用 pipeline
  ├─ channels.json      # 要跟踪的频道ID列表
  

# 要跟踪的频道ID列表
channels.json 
{
  "channels": [
    "UCFQsi7WaF5X41tcuOryDk8w",  
    "UC2I5em6UyBpQiO-8ZW0nV3w",  
    "UCGDMLMZtjCd5P4fhTCetwsw",  
    "UCBUH38E0ngqvmTqdchWunwQ"
  ]
}



# 📝 auto_runner.py
import feedparser
import subprocess
from datetime import datetime, timedelta, timezone
import json

# 文件路径
CHANNELS_FILE = "channels.json"

# 加载频道ID
with open(CHANNELS_FILE, "r") as f:
    channels = json.load(f)["channels"]

# 获取昨天的时间范围 (UTC时间)
today = datetime.now(timezone.utc).date()
yesterday = today - timedelta(days=1)

new_videos = []

# 遍历频道
for channel_id in channels:
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(feed_url)

    for entry in feed.entries:
        # 发布时间 (转换为 UTC 日期)
        published = datetime.fromisoformat(entry.published.replace("Z", "+00:00")).date()

        if published == yesterday:
            video_id = entry.yt_videoid
            video_url = entry.link
            title = entry.title

            print(f"[NEW] {title} ({video_url}) 发布于 {published}")
            new_videos.append((video_id, video_url))

# 处理新视频
if new_videos:
    for video_id, video_url in new_videos:
        try:
            subprocess.run(["python3", "pipeline.py", video_url], check=True)
        except Exception as e:
            print(f"❌ 处理失败: {video_url}, 错误: {e}")
else:
    print("✅ 昨天没有新视频，跳过。")


# 使用方法

先运行一次，检查能否检测到新视频并调用 pipeline.py：

python3 auto_runner.py


加到 cron，比如每天早上 9 点跑一次：

0 9 * * * /usr/bin/python3 /path/to/yt_auto/auto_runner.py >> /path/to/yt_auto/auto.log 2>&1
