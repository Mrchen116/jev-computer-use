# Jev 原生桌面 Agent

只给任务，从应用列表开始：**Jev 选动作，本地 Computer Use 执行，需要输入或帮助时再调用 LLM。** 不需要初始 URL，也不需要为每个网站写操作流程。

这是一版实验性 macOS 项目。执行层不逐步经过 LLM 转发；输入生成、卡住求助和最终核验仍使用 LLM。没有受控实验支持“节省多少费用”或“快多少倍”的结论。

## 安装

需要 Python 3.9+、已安装 Computer Use 插件并保持开启的 Codex 桌面端、已登录的 Codex CLI、TypeSafe API key。沿用系统和应用的正常授权。

```sh
git clone https://github.com/Mrchen116/jev-computer-use.git
cd jev-computer-use
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install .
jev-computer-use --doctor
jev-computer-use '去 https://mrchen116.github.io/ 找输入法项目，给我 GitHub 链接'
```

没有设置 `TYPESAFE_API_KEY` 时，终端隐藏输入地询问 Key。不要把 Key 放进命令、聊天或仓库。`--clipboard-key` 可从剪贴板读取。不带任务运行时会交互询问任务。

URL 可作为任务的一部分，但不是必填参数。需要搜索时，Jev 选中地址栏/搜索框后，LLM 生成搜索词；不知道你的个人网站时，仍需要你提供身份或相关线索。

```sh
jev-computer-use '打开演示页，在 Test message 输入 原生桌面精确输入，点击 Apply locally，返回显示结果' --local-demo
jev-computer-use '完成任务' --context facts.txt --max-steps 20 --max-llm-calls 5
```

## 分工与边界

- Python 直接通过 stdio MCP 调用本机 `cua-repl`，Jev 负责应用/动作选择。
- LLM 生成字段内容或快捷键、处理歧义/循环、在 Jev 提议完成后核验任务。
- 执行前重读界面，避免使用过时编号；通过 `setValue` 填写后核对实际值。
- 无法确定动作是否生效时停止，避免自动重放；应用或风险确认需要用户响应。
- 默认日志只保存步骤类型、状态、耗时和模型调用数。`--trace-full` 才落盘完整私有调试数据，禁止未经脱敏直接上传 issue。

任务、已知资料、当前界面文字/控件值及历史会发送给相关模型。默认日志少存数据，不等于模型请求已脱敏。不要在敏感账户、密码或客户数据页面无人值守运行。模型风险判定和引用检查都不是完整安全或正确性保证。

当前支持可访问性控件点击、单行字段填写、滚动、快捷键和应用切换；没有纯图像定位、拖拽、上传和任意多行编辑策略。原生后端目前主要在 Chrome 上实测，不能宣称所有桌面应用均已验证。

完整用法见 [README](../README.md)，源码对比见 [comparison.md](comparison.md)，实际验证范围见 [testing.md](testing.md)。
