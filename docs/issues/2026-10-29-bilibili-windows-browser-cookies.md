# Windows 上 B 站下载的浏览器登录态读取问题

- 触发与影响：在 Windows 上用 `yt-dlp --cookies-from-browser edge` 查询需大会员权限的视频格式时，无法取得 Edge 当前登录态，最高可用格式查询因此不完整。
- 观察证据：Edge 运行时提示 `Could not copy Chrome cookie database`；完全退出 Edge 后改为 `Failed to decrypt with DPAPI`。指定另一个 Edge 配置文件可以读取 Cookie，但目标视频仍只列出公开格式。以上过程没有导出或保存 Cookie 文件。
- 分析：数据库占用和 DPAPI 解密失败是两个不同的错误。后者与 Chromium 在 Windows 上的 Cookie 加密问题相符，但本次没有独立确认具体加密机制，不将它记为确定根因。
- 处理：在 Firefox 中由用户自行登录 B 站，再用 `--cookies-from-browser firefox`。无需向 Agent 提供账号密码，也无需导出 Cookie 文件。未改动浏览器安全设置。
- 验证：同一视频在未登录状态只列出最高 1080P；Firefox 登录态下列出 3840×2160、120 fps 视频流和 FLAC 音轨。`yt-dlp` 成功下载并合并为 MP4，`ffmpeg` 核对流信息及解码首秒均通过。
- 遗留事项：未验证 Edge 后续版本是否恢复直接读取；不同浏览器版本和配置文件可能表现不同。
