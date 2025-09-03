#!/usr/bin/env python3
"""
YouTube频道自动化监控脚本
监控指定频道的新视频，自动调用yt_summarizer.py进行处理
"""

import feedparser
import subprocess
import json
import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 加载环境变量
load_dotenv()

# 文件路径
CHANNELS_FILE = os.path.join(SCRIPT_DIR, "channels.json")
YT_SUMMARIZER = os.path.join(SCRIPT_DIR, "yt_summarizer.py")
LOG_FILE = os.path.join(SCRIPT_DIR, "auto.log")

# 邮件配置
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
RECIPIENT_EMAIL = 'yzhou7771@gmail.com'

def log(message):
    """记录日志到文件和控制台"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    
    # 写入日志文件
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
    except Exception as e:
        print(f"警告：无法写入日志文件: {e}")

def load_channels():
    """加载频道配置"""
    try:
        if not os.path.exists(CHANNELS_FILE):
            log(f"❌ 频道配置文件不存在: {CHANNELS_FILE}")
            return []
            
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            channels = data.get("channels", [])
            log(f"📺 加载了 {len(channels)} 个频道配置")
            return channels
    except Exception as e:
        log(f"❌ 加载频道配置失败: {e}")
        return []

def get_channel_videos(channel_id, target_date):
    """获取指定频道在目标日期发布的视频"""
    try:
        feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        log(f"🔍 检查频道: {channel_id}")
        
        feed = feedparser.parse(feed_url)
        
        if not hasattr(feed, 'entries') or not feed.entries:
            log(f"⚠️ 频道 {channel_id} 无法获取视频或无视频")
            return []
        
        videos = []
        for entry in feed.entries:
            try:
                # 解析发布时间
                published_str = entry.published.replace("Z", "+00:00")
                published = datetime.fromisoformat(published_str).date()
                
                if published == target_date:
                    video_info = {
                        'id': entry.yt_videoid,
                        'url': entry.link,
                        'title': entry.title,
                        'published': published,
                        'channel_title': entry.author
                    }
                    videos.append(video_info)
                    log(f"✅ 发现新视频: {entry.title}")
            except Exception as e:
                log(f"⚠️ 解析视频条目失败: {e}")
                continue
        
        return videos
        
    except Exception as e:
        log(f"❌ 获取频道 {channel_id} 视频失败: {e}")
        return []

def send_email_summary(video_info, folder_path, summary_text):
    """发送总结邮件到指定邮箱"""
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        log("⚠️ 未配置邮件账户信息，跳过邮件发送")
        return False
    
    try:
        log(f"📧 正在发送邮件: {video_info['title']}")
        
        # 创建邮件内容
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = RECIPIENT_EMAIL
        msg['Subject'] = f"YouTube视频总结 - {video_info['channel_title']}"
        
        # 邮件正文
        body = f"""
YouTube视频总结报告

📹 视频标题: {video_info['title']}
🔗 视频链接: {video_info['url']}
📺 频道名称: {video_info['channel_title']}
📁 保存位置: {folder_path}
📅 发布时间: {video_info['published']}
🕐 处理时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📋 内容总结:
{summary_text}

---
此邮件由YouTube自动化监控系统发送
        """
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 连接SMTP服务器并发送邮件
        server = smtplib.SMTP(EMAIL_SMTP_SERVER, EMAIL_SMTP_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_ADDRESS, RECIPIENT_EMAIL, text)
        server.quit()
        
        log(f"✅ 邮件发送成功: {video_info['title']}")
        return True
        
    except Exception as e:
        log(f"❌ 邮件发送失败: {video_info['title']}, 错误: {e}")
        return False

def process_video(video_info):
    """处理单个视频，包括邮件发送"""
    try:
        log(f"📹 开始处理视频: {video_info['title']}")
        log(f"🔗 视频链接: {video_info['url']}")
        
        # 调用yt_summarizer.py处理视频
        result = subprocess.run([
            sys.executable, YT_SUMMARIZER, video_info['url']
        ], cwd=SCRIPT_DIR, capture_output=True, text=True, timeout=3600)  # 1小时超时
        
        if result.returncode == 0:
            log(f"✅ 视频处理成功: {video_info['title']}")
            
            # 查找生成的文件夹和总结内容
            try:
                # 从输出中提取文件夹路径
                output_lines = result.stdout.split('\n')
                folder_path = None
                
                for line in output_lines:
                    if '所有文件已保存到文件夹:' in line:
                        folder_path = line.split('所有文件已保存到文件夹:')[-1].strip()
                        break
                
                if folder_path and os.path.exists(folder_path):
                    summary_file = os.path.join(folder_path, "summary.txt")
                    
                    if os.path.exists(summary_file):
                        # 读取总结内容
                        with open(summary_file, 'r', encoding='utf-8') as f:
                            summary_text = f.read()
                        
                        # 发送邮件
                        if send_email_summary(video_info, os.path.basename(folder_path), summary_text):
                            log(f"📧 邮件发送完成: {video_info['title']}")
                        else:
                            log(f"⚠️ 邮件发送失败，但视频处理成功: {video_info['title']}")
                    else:
                        log(f"⚠️ 找不到总结文件: {summary_file}")
                else:
                    log(f"⚠️ 找不到输出文件夹: {folder_path}")
            
            except Exception as e:
                log(f"⚠️ 邮件处理异常: {video_info['title']}, 错误: {e}")
            
            return True
        else:
            log(f"❌ 视频处理失败: {video_info['title']}")
            log(f"错误输出: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        log(f"⏰ 视频处理超时: {video_info['title']}")
        return False
    except Exception as e:
        log(f"❌ 处理视频异常: {video_info['title']}, 错误: {e}")
        return False

def main():
    """主函数"""
    log("🚀 YouTube自动化监控启动")
    
    # 检查必要文件
    if not os.path.exists(YT_SUMMARIZER):
        log(f"❌ yt_summarizer.py 不存在: {YT_SUMMARIZER}")
        return
    
    # 加载频道配置
    channels = load_channels()
    if not channels:
        log("❌ 没有可用的频道配置，退出")
        return
    
    # 计算目标日期（今天和昨天）
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)
    log(f"🗓️ 检查日期: {yesterday} 和 {today}")
    
    # 收集所有新视频
    all_new_videos = []
    
    for channel_id in channels:
        # 检查昨天的视频
        yesterday_videos = get_channel_videos(channel_id, yesterday)
        all_new_videos.extend(yesterday_videos)
        
        # 检查今天的视频
        today_videos = get_channel_videos(channel_id, today)
        all_new_videos.extend(today_videos)
    
    # 处理结果统计
    if not all_new_videos:
        log("✅ 昨天和今天都没有新视频，任务完成")
        return
    
    log(f"📊 共发现 {len(all_new_videos)} 个新视频")
    
    # 处理每个视频
    success_count = 0
    failed_count = 0
    
    for video in all_new_videos:
        if process_video(video):
            success_count += 1
        else:
            failed_count += 1
    
    # 总结
    log(f"📈 处理完成: 成功 {success_count} 个，失败 {failed_count} 个")
    log("🎉 YouTube自动化监控完成")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("⚠️ 用户中断操作")
        sys.exit(0)
    except Exception as e:
        log(f"❌ 程序异常: {e}")
        sys.exit(1)