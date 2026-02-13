#!/bin/bash
# OpenClaw 自动启动脚本
# Codespace 启动时自动运行

echo "🦞 启动 OpenClaw Gateway..."

# 检查 openclaw 是否安装
if command -v openclaw &> /dev/null; then
    openclaw gateway start
    echo "✅ OpenClaw Gateway 已启动"
else
    echo "❌ openclaw 命令未找到，请检查安装"
fi
