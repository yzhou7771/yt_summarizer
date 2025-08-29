# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a YouTube video summarizer that downloads audio from YouTube videos, transcribes it using OpenAI's Whisper API, and generates summaries using OpenAI's GPT models. The project consists of a single Python script that handles the complete pipeline.

## Dependencies and Setup

The project requires:
- `yt-dlp` for YouTube audio download (must be installed separately)
- `openai` Python library for Whisper transcription 
- `google-generativeai` for Gemini summarization
- `requests` for AssemblyAI API calls
- `python-dotenv` for environment variable management
- Chrome browser for cookie-based authentication with YouTube

Install Python dependencies:
```bash
pip install openai google-generativeai requests python-dotenv
```

Install yt-dlp separately (system-wide or via package manager).

### Environment Variables Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:
```bash
OPENAI_API_KEY=your_openai_api_key_here
GOOGLE_API_KEY=your_google_api_key_here  
ASSEMBLYAI_API_KEY=your_assemblyai_api_key_here
```

The script will automatically load these environment variables and validate they exist before running.

## Running the Application

Execute the main script with a YouTube URL:
```bash
python yt_summarizer.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

The script will:
1. Validate the YouTube URL and API keys
2. Create a date+channel folder (e.g., `0828_视野环球财经/`)
3. Download audio from the YouTube video
4. Transcribe the audio using AssemblyAI
5. Generate a summary using Gemini 1.5 Flash
6. Save outputs to `transcript.txt` and `summary.txt`
7. Clean up audio files automatically

## Configuration

The script uses environment variables for API key configuration:
- `OPENAI_API_KEY`: OpenAI API key (currently used for future Whisper integration)
- `GOOGLE_API_KEY`: Google Gemini API key for content summarization
- `ASSEMBLYAI_API_KEY`: AssemblyAI API key for audio transcription

All configuration is handled through the `.env` file - no code changes needed.

## Architecture Notes

**Single-file architecture**: The entire pipeline is contained in one Python script with three main functions:

1. `download_audio()`: Handles YouTube audio extraction with retry logic and rate limiting
2. `transcribe_audio()`: Uses OpenAI Whisper API for speech-to-text
3. `summarize_text()`: Uses OpenAI GPT models for content summarization

**Error handling**: The download function includes robust retry mechanisms with exponential backoff and random delays to avoid rate limiting.

**Authentication**: Uses Chrome browser cookies for YouTube authentication, allowing access to content that might require login.

## Security Considerations

**API Key Exposure**: The OpenAI API key is currently hardcoded in the script. This should be moved to an environment variable or secure configuration file before any commits or sharing.

**Rate Limiting**: The script includes built-in delays and rate limiting for YouTube downloads but may still be subject to API limits from OpenAI.

## File Outputs

- `audio.mp3`: Downloaded audio file from YouTube
- `transcript.txt`: Raw transcription from Whisper
- `summary.txt`: Final GPT-generated summary

## Common Development Tasks

Since this is a simple single-file project, there are no build processes, test suites, or linting configurations. Development involves:

1. Modifying the Python script directly
2. Testing with different YouTube URLs
3. Adjusting prompt templates for better summaries
4. Handling different video formats or languages

# 使用方法：

# 基本使用
python yt_summarizer.py "https://www.youtube.com/watch?v=VIDEO_ID"

# 带时间戳的链接
python yt_summarizer.py "https://www.youtube.com/watch?v=VIDEO_ID&t=10s"

# 短链接格式
python yt_summarizer.py "https://youtu.be/VIDEO_ID"