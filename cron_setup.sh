#!/bin/bash
# Cron定时任务设置脚本

# 获取当前脚本目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH=$(which python3)
AUTO_RUNNER="$SCRIPT_DIR/auto_runner.py"
LOG_FILE="$SCRIPT_DIR/auto.log"

echo "🔧 YouTube自动化监控 - Cron设置"
echo "================================"
echo "项目目录: $SCRIPT_DIR"
echo "Python路径: $PYTHON_PATH"
echo "脚本路径: $AUTO_RUNNER"
echo "日志文件: $LOG_FILE"
echo ""

# 检查文件是否存在
if [[ ! -f "$AUTO_RUNNER" ]]; then
    echo "❌ auto_runner.py 不存在"
    exit 1
fi

if [[ ! -x "$PYTHON_PATH" ]]; then
    echo "❌ Python3 不可执行"
    exit 1
fi

# 生成cron条目
CRON_ENTRY="0 9 * * * cd '$SCRIPT_DIR' && '$PYTHON_PATH' '$AUTO_RUNNER' >> '$LOG_FILE' 2>&1"

echo "📋 建议的Cron条目 (每天早上9点运行):"
echo "$CRON_ENTRY"
echo ""

# 显示当前cron任务
echo "📅 当前的Cron任务:"
crontab -l 2>/dev/null || echo "无现有的cron任务"
echo ""

# 询问是否自动添加
read -p "🤔 是否自动添加这个cron任务？ (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # 备份现有crontab
    crontab -l > /tmp/crontab_backup 2>/dev/null
    
    # 添加新任务
    (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Cron任务添加成功！"
        echo "📝 备份文件: /tmp/crontab_backup"
        echo ""
        echo "验证安装："
        crontab -l | grep auto_runner
    else
        echo "❌ Cron任务添加失败"
        exit 1
    fi
else
    echo "ℹ️ 手动设置Cron任务："
    echo "1. 运行: crontab -e"
    echo "2. 添加以下行:"
    echo "   $CRON_ENTRY"
    echo "3. 保存退出"
fi

echo ""
echo "🎉 设置完成！"
echo ""
echo "📖 使用说明："
echo "- 每天早上9点自动运行"
echo "- 检查昨天的新视频"
echo "- 自动生成总结并发送邮件"
echo "- 日志保存在: $LOG_FILE"
echo ""
echo "🔧 管理命令："
echo "- 查看任务: crontab -l"
echo "- 编辑任务: crontab -e"
echo "- 删除任务: crontab -r"
echo "- 查看日志: tail -f '$LOG_FILE'"