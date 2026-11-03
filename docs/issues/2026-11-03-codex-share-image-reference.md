# Codex 分享导出遗漏图片项目的本地引用

- **触发条件和影响**：Codex 公开分享 JSON 中存在 `imageView.url` 或 `imageGeneration.result`，而非用户消息 `content` 中的图片时，旧导出器会下载 `assets` 文件，但 Markdown 只保留原始 `codex:shared-asset/...` 引用，不便本地 Agent 直接打开图片。
- **证据**：一次较长分享包含 17 个 `imageView`、2 个 `imageGeneration` 和 19 个附件；附件均下载成功，但原 Markdown 中这些图片项目没有对应的本地图片引用。
- **根因**：导出器只把用户消息 `content` 中的图片转换为本地 Markdown 链接，没有处理另外两种项目的图片引用。
- **修复**：为图片查看和图片生成结果生成指向已下载文件的相对链接；图片无法对应共享附件时记录未解析项和警告。原始 JSON 字段仍保留。
- **来源限制**：另一个长分享中部分图片被源数据标记为 `codex:shared-image-unavailable`；这类图片无法从分享快照中恢复，必须与下载失败区分。
- **验证**：单元测试覆盖三种图片引用及未解析场景；对实际分享逐项核对 Markdown 引用、附件大小和 SHA-256。分享 JSON 接口并非稳定的官方 API，未来字段变化仍需重新核验。
