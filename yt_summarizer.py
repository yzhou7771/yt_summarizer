import os
import random
import time
import subprocess
import openai
import google.generativeai as genai
import sys
from datetime import datetime
from dotenv import load_dotenv

# ========== 配置 ==========
# 加载环境变量
load_dotenv()

# 从环境变量获取 API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY') 
ASSEMBLYAI_API_KEY = os.getenv('ASSEMBLYAI_API_KEY')

# 验证必要的 API Keys 是否存在
if not OPENAI_API_KEY:
    print("❌ 错误：未找到 OPENAI_API_KEY 环境变量")
    print("请在 .env 文件中设置您的 OpenAI API Key")
    sys.exit(1)

if not GOOGLE_API_KEY:
    print("❌ 错误：未找到 GOOGLE_API_KEY 环境变量")
    print("请在 .env 文件中设置您的 Google API Key")
    sys.exit(1)

if not ASSEMBLYAI_API_KEY:
    print("❌ 错误：未找到 ASSEMBLYAI_API_KEY 环境变量")
    print("请在 .env 文件中设置您的 AssemblyAI API Key")
    sys.exit(1)

# 配置 APIs
openai.api_key = OPENAI_API_KEY
genai.configure(api_key=GOOGLE_API_KEY)
# ==========================


# 获取视频信息并创建文件夹
def get_video_info_and_create_folder(video_url):
    print("▶️ 正在获取视频信息...")
    
    # 使用 yt-dlp 获取视频元数据
    cmd = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "--print", "%(upload_date)s",
        "--print", "%(uploader)s",
        "--no-download",
        video_url
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        lines = result.stdout.strip().split('\n')
        
        if len(lines) >= 2:
            upload_date = lines[0]  # 格式：20250828
            uploader = lines[1]     # 频道名
            
            # 格式化日期：20250828 -> 0828
            formatted_date = upload_date[4:8] if len(upload_date) == 8 else upload_date[-4:]
            
            # 创建文件夹名：日期_频道名
            folder_name = f"{formatted_date}_{uploader}"
            
            # 创建文件夹
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"✅ 创建文件夹: {folder_name}")
            
            return folder_name
        else:
            # 如果无法获取信息，使用当前日期
            current_date = datetime.now().strftime("%m%d")
            folder_name = f"{current_date}_unknown"
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
                print(f"✅ 创建文件夹: {folder_name}")
            return folder_name
            
    except Exception as e:
        print(f"⚠️ 获取视频信息失败: {e}")
        # 使用当前日期作为备选
        current_date = datetime.now().strftime("%m%d")
        folder_name = f"{current_date}_unknown"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
            print(f"✅ 创建文件夹: {folder_name}")
        return folder_name


# Step 1: 稳定下载音频
def download_audio(video_url, folder_path, max_retries=3):
    output_file = os.path.join(folder_path, "audio.mp3")
    attempt = 0
    while attempt < max_retries:
        try:
            # 随机等待，模拟正常观看
            delay = random.randint(3, 10)
            print(f"⏳ 等待 {delay}s 再开始下载...")
            time.sleep(delay)

            cmd = [
                "yt-dlp",
                "--cookies", "cookies.txt",
                "-x",
                "--audio-format", "mp3",
                "-o", output_file,
                video_url
            ]

            print("▶️ 正在运行 yt-dlp 下载音频...")
            subprocess.run(cmd, check=True)
            print("✅ 下载成功:", output_file)
            return output_file

        except subprocess.CalledProcessError as e:
            attempt += 1
            print(f"⚠️ 下载失败 (第 {attempt}/{max_retries} 次)，错误: {e}")
            if attempt >= max_retries:
                print("❌ 超过最大重试次数，下载失败。")
                raise
            else:
                cooldown = random.randint(20, 60)
                print(f"🔄 等待 {cooldown}s 后重试...")
                time.sleep(cooldown)


# # Step 2: Whisper 转录
# def transcribe_audio(audio_file, folder_path):
#     transcript_file = os.path.join(folder_path, "transcript.txt")
#     print("▶️ 正在转录音频...")
#     client = openai.OpenAI(api_key=openai.api_key)
#     with open(audio_file, "rb") as f:
#         transcript = client.audio.transcriptions.create(
#             model="whisper-1",
#             file=f
#         )
#     text = transcript.text
#     with open(transcript_file, "w", encoding="utf-8") as f:
#         f.write(text)
#     print("✅ 转录完成，保存到:", transcript_file)
#     return text

# Step 2 - A: AssemblyAI 转录
import requests

def transcribe_audio(audio_file, folder_path):
    """
    使用 AssemblyAI API 将音频文件转录为文本
    
    Args:
        audio_file (str): 音频文件的完整路径
        folder_path (str): 目标文件夹路径，用于保存转录文件
    
    Returns:
        str: 转录后的文本内容
    """
    # 构建转录文件的保存路径
    transcript_file = os.path.join(folder_path, "transcript.txt")
    print("▶️ 正在转录音频...")
    
    # AssemblyAI 配置
    base_url = "https://api.assemblyai.com"
    
    headers = {
        "authorization": ASSEMBLYAI_API_KEY
    }
    
    # Step 1: 上传本地音频文件
    print("📤 正在上传音频文件...")
    with open(audio_file, "rb") as f:
        response = requests.post(base_url + "/v2/upload", 
                               headers=headers, 
                               data=f)
    
    if response.status_code != 200:
        raise RuntimeError(f"文件上传失败: {response.text}")
    
    audio_url = response.json()["upload_url"]
    print("✅ 文件上传成功")
    
    # Step 2: 创建转录任务
    print("🔄 创建转录任务...")
    data = {
        "audio_url": audio_url,
        "speech_model": "universal",
        "language_detection": True,  # 启用自动语言检测
        "auto_chapters": False,
        "summarization": False,
        "sentiment_analysis": False
    }
    
    url = base_url + "/v2/transcript"
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code != 200:
        raise RuntimeError(f"转录任务创建失败: {response.text}")
    
    transcript_id = response.json()['id']
    polling_endpoint = base_url + "/v2/transcript/" + transcript_id
    print(f"📋 转录任务已创建，ID: {transcript_id}")
    
    
    # Step 3: 轮询转录状态
    print("⏳ 等待转录完成...")
    while True:
        transcription_result = requests.get(polling_endpoint, headers=headers).json()
        
        if transcription_result['status'] == 'completed':
            transcript_text = transcription_result['text']
            print("✅ 转录完成!")
            break
        
        elif transcription_result['status'] == 'error':
            raise RuntimeError(f"转录失败: {transcription_result['error']}")
        
        else:
            print(f"📊 转录状态: {transcription_result['status']}...")
            time.sleep(3)
    
    # Step 4: 保存转录文本到文件
    with open(transcript_file, "w", encoding="utf-8") as f:
        f.write(transcript_text)
    
    print("✅ 转录完成，保存到:", transcript_file)
    return transcript_text


# Step 3: Gemini 总结
def summarize_text(text, folder_path):
    summary_file = os.path.join(folder_path, "summary.txt")
    print("▶️ 正在总结内容...")
    
    # 使用 Gemini 1.5 Flash 模型
    model = genai.GenerativeModel('gemini-1.5-flash')
    prompt = f"你是一个帮我总结 YouTube 视频的助手。请帮我总结以下视频内容:\n\n{text}"
    
    response = model.generate_content(prompt)
    summary = response.text
    
    print("✅ 总结完成:\n")
    print(summary)

    # 保存总结
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write(summary)
    print("📂 总结已保存到", summary_file)

    return summary


def print_usage():
    """打印使用说明"""
    print("🎬 YouTube 视频总结器")
    print("使用方法:")
    print("  python yt_summarizer.py <YouTube链接>")
    print("")
    print("示例:")
    print("  python yt_summarizer.py https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    print("  python yt_summarizer.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s'")
    print("")
    print("功能:")
    print("  ✅ 自动下载音频")
    print("  ✅ AssemblyAI 转录")
    print("  ✅ Gemini 1.5 Flash 总结")
    print("  ✅ 自动文件夹管理")


if __name__ == "__main__":
    # 检查命令行参数
    if len(sys.argv) != 2:
        print("❌ 错误：请提供 YouTube 链接")
        print("")
        print_usage()
        sys.exit(1)
    
    # 获取 YouTube 链接
    video_url = sys.argv[1]
    
    # 简单验证链接格式
    if not ("youtube.com/watch" in video_url or "youtu.be/" in video_url):
        print("❌ 错误：请提供有效的 YouTube 链接")
        print("")
        print_usage()
        sys.exit(1)
    
    print(f"🎯 处理视频: {video_url}")
    print("")
    
    try:
        # 获取视频信息并创建文件夹
        folder_path = get_video_info_and_create_folder(video_url)
        
        # 下载音频
        audio_file = download_audio(video_url, folder_path)
        
        # 转录音频
        text = transcribe_audio(audio_file, folder_path)
        
        # 生成总结
        try:
            summarize_text(text, folder_path)
            
            # 只有总结成功生成后才删除音频文件以节省空间
            if os.path.exists(audio_file):
                os.remove(audio_file)
                print(f"🗑️ 已删除音频文件: {audio_file}")
                
        except Exception as e:
            print(f"❌ 总结生成失败: {e}")
            print(f"💾 保留音频文件: {audio_file}")
        
        print(f"\n🎉 所有文件已保存到文件夹: {folder_path}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断操作")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        print("请检查 YouTube 链接是否有效，或稍后重试")
        sys.exit(1)
