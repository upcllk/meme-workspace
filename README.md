# Meme Workspace

这里是 meme 相关项目的统一入口。各项目仍保留独立 Git 仓库；根目录 Git 仓库仅管理工作区说明、索引和配置，不收录链接目标中的代码。

## 项目

| 路径 | 说明 | Git 仓库 |
|---|---|---|
| [`pig-pet-mac/`](pig-pet-mac/) | Pig Pet Mac 桌面宠物项目 | 本机独立 Git 仓库 |

以上目录是本机软链接，Git 忽略，不会提交绝对路径或目标仓库文件。换机器或链接失效时，请按 `AGENTS.md` 中的说明重新建立链接。

工作区级 Agent Skills 位于 [`.agents/skills/`](.agents/skills/)，每个角色生成技能使用的图片素材和说明文件都保存在各自的 Skill 文件夹内；项目自身的规则仍以各仓库内的 `AGENTS.md` 为准。

工作区根目录暂不维护独立的素材库；项目代码和项目素材保留在各自项目中。

## 使用

用 VS Code 打开 [`workspace.code-workspace`](workspace.code-workspace)，即可在一个窗口查看工作区说明与 Pig Pet Mac 项目。进入或修改项目时，先阅读该项目自己的 `AGENTS.md`（如有），并在该项目的 Git 仓库内完成代码变更和提交。

通用协作、自动提交和问题沉淀规则见 [AGENTS.md](AGENTS.md)。
