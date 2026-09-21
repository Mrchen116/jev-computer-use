# Jev Computer Use：Skill + 执行代码

给外层 Agent 一句任务：**Agent 调用 Skill，Skill 启动代码，Jev 选择动作，代码执行桌面操作。需要文字、推理帮助或完成核验时，交回同一个外层 Agent。**

普通点击不经过外层 Agent 逐步转发。默认模式不会在内部另开 `codex exec`，外层 Agent 可以使用当前对话里已有的目标、资料和授权。不要求起始 URL，也不要求为每个网站写流程。

## 用户怎么用

请你的 Agent 从本仓库安装 `skills/jev-computer-use`，或者把整个目录复制到 Agent 的技能目录。Codex 的首次安装示例：

```sh
git clone https://github.com/Mrchen116/jev-computer-use.git
mkdir -p ~/.codex/skills
cp -R jev-computer-use/skills/jev-computer-use ~/.codex/skills/
```

已有同名技能时先检查再更新。新开 Agent 会话，让它发现技能，然后直接说：

> 用 $jev-computer-use 去 https://mrchen116.github.io/ 找我的输入法项目，给我 GitHub 链接。

> 用 $jev-computer-use 在我的网站找多 agent 项目，返回最新的一个 issue。

如果对话里还没有你的网站等必要事实，Agent 会询问。用户不需要手写任务 JSON、按钮名单或模型提示词。Skill 内含完整 Python 代码，不需要 pip 安装。

需要 macOS、Python 3.9+、保持开启且装有 Computer Use 的 Codex 桌面端，以及 TypeSafe key。通过运行环境的 `TYPESAFE_API_KEY` 或 `TYPESAFE_API_KEY_FILE` 配置；文件放在仓库外，权限设为 0600，不把 key 放进聊天或命令参数。外层 Agent 需要能运行持续进程、读写文件，并在执行器等待时回复。**换外层 Agent 不代表摆脱 Codex 桌面执行依赖**；目前实际宿主验收为 Codex，其他 Agent 尚未逐一实测。

## 交接如何工作

1. 外层 Agent 读取 Skill，传入用户任务及必要事实，启动一个持续执行的 worker。
2. worker 从应用列表开始，连续运行观察 → Jev 决策 → 原生 CUA 执行。
3. 需要帮助时暂停，返回请求 ID、类型、当前界面证据和所需回答字段。
4. 外层 Agent 根据当前对话与证据给出输入、动作建议或核验结果，必要时向用户询问。
5. 同一个 worker 接收回答，执行前重读界面；界面已变就重新决策，不执行旧动作。
6. Jev 提议完成后，由外层 Agent 核对所有要求。证据仍然匹配才结束，最终答案由外层 Agent 给用户。

求助与响应通过本机私有 JSON 文件交接，不要求宿主实现新的 MCP 服务，也不启动嵌套 LLM。默认最多 30 轮动作决策、20 次外层求助、每次等待 600 秒。求助等待时间不等于 LLM 推理耗时。

## 边界与验证

任务、当前 UI 内容和历史会发送给 Jev；相关证据也会交给外层 Agent。默认报告只有元数据，但临时交接目录包含私有上下文和最终答案，由宿主完成后清理。不要发布这些文件。风险模型与原文引用都不是完整授权或正确性保证。

支持可访问性控件点击、单行填写、滚动、快捷键和应用切换；不支持纯图像定位、拖拽、上传和任意多行编辑。原生后端主要在 Chrome 验证。没有受控实验支持“省多少费用”或“快多少倍”。

保留手动 CLI：安装 Python 包后，显式使用 `jev-computer-use '任务' --helper codex`，才启用内部 Codex CLI 文字助手。默认 Skill 路径不需要它。

完整入口见 [SKILL.md](../skills/jev-computer-use/SKILL.md)，[架构](architecture.md)、[源码对比](comparison.md)、[验证记录](testing.md)。
