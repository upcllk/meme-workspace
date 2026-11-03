---
name: chat-share-export
description: 导出 ChatGPT 网页分享链接和 Codex 分享链接，供本地 Agent 读取；保留对话 JSON、Markdown、附件及缺失记录。用户要求读取、保存、归档或分析 chatgpt.com/share/ 或 chatgpt.com/s/cx_ 链接时使用。
---

# ChatGPT / Codex 分享导出

使用本技能的 Python 标准库脚本，不安装浏览器或第三方服务。只访问用户提供的公开分享快照，不读取浏览器 Cookie、登录态或私有会话。普通 `/c/` 对话不是公开分享链接：请用户自行生成 `/share/` 链接。

```bash
python3 .agents/skills/chat-share-export/scripts/export.py \
  'https://chatgpt.com/share/分享ID' --out /path/to/new-export
python3 .agents/skills/chat-share-export/scripts/export.py \
  'https://chatgpt.com/s/cx_分享ID' --out /path/to/new-export
```

目标目录必须不存在；默认保存到当前目录下以分享 ID 命名的新目录。不要将导出的对话、附件或带敏感信息的链接提交到仓库。

## 输出与读取

- `conversation.md`：按分享中的消息顺序整理，适合 Agent 先阅读；用户图片、Codex 图片查看和生成结果在可下载时引用本地文件。结构化项目无法转成文本时保留 JSON 原文片段，不假称完整呈现。
- `source.json`：Codex 为接口原始 JSON；普通 ChatGPT 为页面内嵌的解码后分享对话数据，保留消息树和元数据。Markdown 不包含的分支或结构化信息应查此文件。
- `manifest.json`：来源类型、附件逐项状态和警告；下载成功的附件在 `attachments/`，Markdown 引用本地相对路径。确认附件状态，不要把没有下载的附件当作已保存。

Codex 使用当前可访问、但不保证稳定的非官方接口 `backend-api/wham/shared_threads`，其中 `assets` 对应共享附件。普通 ChatGPT 使用网页内嵌数据；检测到附件标识但无法通过公开快照解析为可下载文件时，记录 `unresolved`，不猜测地址。普通网页的外部引用图片不是用户附件，不自动下载。无法访问、链接失效、格式变化和附件失败均须明确报告；脚本附件未完整下载时以非零状态退出，但保留已导出的文件和清单供检查。用户必须有权访问分享内容，不绕过权限或反爬限制。

Codex 的 `codex:shared-image-unavailable` 表示分享源已标记图片不可用，不等于下载故障；应单独报告，不能从中恢复原图。

运行后检查 `manifest.json` 和错误输出，再根据问题读取 Markdown、JSON 和实际附件；图片应使用有图像能力的工具查看，不要只看文件名。分享快照可能不包含原对话的所有文件、工具调用或内部推理。
