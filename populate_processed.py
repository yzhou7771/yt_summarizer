#!/usr/bin/env python3
"""
填充现有视频到processed.json
"""

import os
import re
import json
from datetime import datetime

# 获取当前目录下的所有视频文件夹
def get_existing_video_folders():
    """获取现有的视频文件夹"""
    folders = []
    current_dir = '.'
    
    for item in os.listdir(current_dir):
        if os.path.isdir(item) and re.match(r'\d{4}_', item):
            folders.append(item)
    
    return sorted(folders)

def extract_video_info_from_folder(folder_name):
    """从文件夹名称提取视频信息"""
    # 文件夹格式：MMDD_频道名称
    parts = folder_name.split('_', 1)
    if len(parts) != 2:
        return None
    
    date_part = parts[0]
    channel_name = parts[1]
    
    # 假设年份为2025年（根据实际情况调整）
    try:
        month = int(date_part[:2])
        day = int(date_part[2:])
        published_date = f"2025-{month:02d}-{day:02d}"
    except ValueError:
        return None
    
    return {
        'channel_name': channel_name,
        'published_date': published_date
    }

def populate_processed_videos():
    """填充已处理的视频记录"""
    print("🔄 填充现有视频到processed.json")
    print("=" * 40)
    
    # 加载现有的processed.json
    processed_file = "processed.json"
    if os.path.exists(processed_file):
        with open(processed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {"processed_videos": {}}
    
    processed_videos = data["processed_videos"]
    
    # 获取现有文件夹
    folders = get_existing_video_folders()
    print(f"📁 发现 {len(folders)} 个视频文件夹")
    
    added_count = 0
    
    for folder in folders:
        print(f"\n📂 处理文件夹: {folder}")
        
        # 提取视频信息
        info = extract_video_info_from_folder(folder)
        if not info:
            print(f"  ⚠️ 无法解析文件夹名称")
            continue
        
        # 检查是否有summary.txt文件
        summary_file = os.path.join(folder, "summary.txt")
        if not os.path.exists(summary_file):
            print(f"  ⚠️ 找不到summary.txt，跳过")
            continue
        
        # 读取summary内容获取视频标题
        try:
            with open(summary_file, 'r', encoding='utf-8') as f:
                summary_content = f.read()
            
            # 尝试从文件夹中的内容推断标题（简化处理）
            video_title = f"视频来自 {info['channel_name']} - {info['published_date']}"
            
            # 生成一个唯一ID（基于文件夹名）
            video_id = folder.replace('_', '-')
            
            # 如果还没有记录这个视频
            if video_id not in processed_videos:
                processed_videos[video_id] = {
                    "title": video_title,
                    "url": f"https://youtube.com/watch?v={video_id}",  # 占位符URL
                    "channel": info['channel_name'],
                    "published": info['published_date'],
                    "processed_at": "已存在文件夹",
                    "note": "从现有文件夹导入"
                }
                
                print(f"  ✅ 添加记录: {video_title}")
                added_count += 1
            else:
                print(f"  ⏭️ 已存在记录，跳过")
        
        except Exception as e:
            print(f"  ❌ 处理异常: {e}")
    
    # 保存更新的记录
    if added_count > 0:
        with open(processed_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 成功添加 {added_count} 个视频记录")
        print(f"📋 总共记录了 {len(processed_videos)} 个已处理视频")
    else:
        print(f"\n✅ 没有新增记录，总共 {len(processed_videos)} 个已处理视频")

if __name__ == "__main__":
    populate_processed_videos()