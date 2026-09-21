# 与搜索结果中四个项目的对比

检索日期：2026-09-21。范围是用户提供的 GitHub 查询 `Codex computer use jev` 返回的四个仓库。以下结论来自 README 与固定提交源码阅读；没有运行这些项目的模型调用，也没有在统一机器/任务集上比较性能。我们的开发记录同样只是少量样本。

**核心判断：降低逐动作 LLM 往返并非本项目独有；主要差异在于任务开始之前，宿主需要准备多少信息，以及自由度与可控性的取舍。**

| 项目 | 实际承担的工作 | 任务前置准备 | 我们应学习的地方 |
| --- | --- | --- | --- |
| `yikangy873-gif/jev-desktop` | 在已有 CUA 目标内运行限定动作循环；一次请求预测操作与各操作的目标 | Codex 提供目标、动作白名单、文本槽和本地 verifier | 只校验选中操作的目标头；文本留本地；状态新鲜度；不重放不确定动作 |
| `kerpopule/hermes-jev-skills` | 广泛的 Jev 工具集；桌面 runner 经独立 `cua-driver` MCP 执行；可先用小模型规划一次 | 基本模式给目标窗口与验收期望；plan 模式可从前台或打开应用开始 | 隐私数据最小化、环境诊断、候选数量预算、规划成本与重用的明确记录 |
| `tacticocc/Jevbridge` | Jev/LLM/heuristic 决策协议与 MCP/ACP 适配，返回动作和目标 | 外部宿主提供观测并执行动作 | 提供者边界、离线测试和协议化结果；不是可直接替换我们的桌面执行器 |
| `kangshifu1/jev-computer-use` | 独立 Playwright 浏览器适配器、已有 Codex tab 接口与任务验证协议 | 独立模式必须给 startUrl、来源范围、控件和断言 | 安装后实测、确定性断言、合成证据与测量条件 |
| 本项目 | 从应用列表起步，自动提取控件，Jev 选择，缺内容时再请 LLM | 一句任务；必要的用户事实；不要求初始 URL | 更适合探索性任务，但模型请求包含更多 UI 内容，权限/验收不如限定工作流严格 |

## Skill 入口与外层 Agent 的分工

四个项目都已有 Skill 入口，因此“Skill + 代码”本身不是差异点：

- [jev-desktop 的 Skill](https://github.com/yikangy873-gif/jev-desktop/blob/9b02783ed96a81f2529827492de708ca1956c265/plugins/jev-desktop/skills/jev-desktop/SKILL.md) 让宿主准备目标、允许动作、文本槽和 verifier，再启动本地批量循环；缺少文字时退回宿主。它最接近把推理与执行拆开的产品形态。
- [Hermes 的 Skill](https://github.com/kerpopule/hermes-jev-skills/blob/29e64b57026eb040b355c260a2480015bd459611/skills/jev-computer-use/SKILL.md) 说明候选动作协议并提供现成 runner；可选 `--plan` 仍会在 runner 中调用文字模型一次，所以不能把所有模式都概括成外层推理。
- [Jevbridge 的 Skill](https://github.com/tacticocc/Jevbridge/blob/84fcdc30e69a72bcf362e651779aaf38a9897b32/skills/jevbridge/SKILL.md) 教宿主使用 typed decision/MCP/ACP 接口，生成模型留在宿主侧，但桌面执行仍由宿主集成。
- [同名项目的 Skill](https://github.com/kangshifu1/jev-computer-use/blob/0cd5c076445c00e0d56529a5e0471320a0564a4d/skills/jev-computer-use/SKILL.md) 把规划、自由文本输入、图像理解和结果核验留给宿主，按环境选择已有 Codex tab 或独立浏览器后端。

本项目 0.2.0 改为自包含 Skill：外层 Agent 传任务；同一个持续 worker 自己发现动作并循环执行；需要文字、推理或核验时以结构化请求暂停，宿主回答后继续。不要求事先填好所有文本槽，也不在默认路径另开 `codex exec`。这利用了外层已有对话上下文，但每次交接仍有工具调度开销；不能直接推导出净节费或速度优势。执行后端仍依赖本机 Codex macOS runtime，换宿主不等于跨平台。

## Jev Desktop 的执行约束

其 `createSession` 要求 `targetName` 和 `verify`，候选动作经 `clickLabels`、`textSlots` 等约束后才暴露给 Jev。`buildDecisionSpace` 在一次请求中建立操作头及对应目标头；循环只执行选中操作允许的目标，填值使用本地准备的文本槽。它已经避免每次点击都返回 Codex 主模型，因此不能把这一点当作我们的独创优势。它的循环范围更可控，而本项目免去了为每项任务预制这些规则的要求。参见固定提交的 [runner](https://github.com/yikangy873-gif/jev-desktop/blob/9b02783ed96a81f2529827492de708ca1956c265/plugins/jev-desktop/scripts/runner.mjs)、[policy](https://github.com/yikangy873-gif/jev-desktop/blob/9b02783ed96a81f2529827492de708ca1956c265/plugins/jev-desktop/scripts/policy.mjs)。

## Hermes：能独立循环，也能一次规划

不能把它概括成“每步都要宿主 LLM”。它提供真实桌面 runner，从 `cua-driver` 获取界面、构建候选、调用 Jev、执行并检查；`--plan` 可先调用文字模型，将多步任务拆成直接动作或 Jev 定位的步骤。其 `--expect` 验证依赖窗口标题或选中元素匹配；没有期望时不宣称验证通过。这比只看目标按钮存在更严谨，但不等价于任意信息检索任务的语义验收。参见 [GUI runner](https://github.com/kerpopule/hermes-jev-skills/blob/29e64b57026eb040b355c260a2480015bd459611/skills/jev-computer-use/scripts/jev_gui_agent.py)、[chooser](https://github.com/kerpopule/hermes-jev-skills/blob/29e64b57026eb040b355c260a2480015bd459611/jevkit/choose.py)。

## Jevbridge：决策接口不等于执行闭环

MCP 的 `jev_computer_use` 接收可见控件并返回决策/门控；此路径没有本机桌面驱动。所查提交的 ACP `runDecisionTurn` 直接调用 heuristic，演示结果也不能视为真实 GUI 执行。其多后端协议适配值得参考；我们已有的原生执行和观测结果验证是另一层能力。参见 [MCP tools](https://github.com/tacticocc/Jevbridge/blob/84fcdc30e69a72bcf362e651779aaf38a9897b32/src/mcp/tools.ts)、[ACP turn](https://github.com/tacticocc/Jevbridge/blob/84fcdc30e69a72bcf362e651779aaf38a9897b32/src/acp/turn.ts)。

## 同名项目：浏览器任务协议更明确

其独立入口验证 `startUrl`、`allowedOrigins`、显式 controls 与 assertions，拒绝无独立断言的任务。强项是可复现的有限浏览器流程，不是自然语言任意桌面任务；README 也明确原生桌面尚未实现。它区分了模拟响应测试、真实 API 样本和对比测量条件，我们采用同样的证据边界，不把一次成功扩大成通用成功率。参见 [contracts](https://github.com/kangshifu1/jev-computer-use/blob/0cd5c076445c00e0d56529a5e0471320a0564a4d/skills/jev-computer-use/scripts/contracts.mjs)、[browser adapter](https://github.com/kangshifu1/jev-computer-use/blob/0cd5c076445c00e0d56529a5e0471320a0564a4d/skills/jev-computer-use/scripts/playwright-adapter.mjs)。

## 本项目的长处与短处

长处是部署同一套程序后就能从任务开始；不需要为新网站写动作名单或验收脚本。操作和目标使用同一个 opaque action ID，避免组合出不存在的动作；执行前重读界面，填写后检查实际值；LLM 调用按输入、决策帮助、核验分别统计。

短处是当前模型输入包含任务相关窗口的正文和控件值，隐私最小化弱于只发受限标签的项目；动作范围更宽，模型风险分类不是确定性授权边界；完成核验中的原文匹配不能证明语义判断正确；当前测试主要是 Chrome 原生 AX 路径，小样本不能支持跨应用泛化或节费结论。原型两个成功样本分别用了 3 和 6 次 LLM 调用，不能称为“只用一次 LLM”。

本次已采用：标准安装入口与 doctor、默认元数据日志、私有调试数据显式开启、LLM 调用预算、不重放不确定动作、合成测试与版本条件记录。保留现有决策结构，避免一次整理同时改变所有模型行为。

待做受控实验：flat choice 与操作/目标多头、按需文本生成与一次预备文本、语义核验与可选确定性断言。比较时必须固定任务、环境、成功标准和模型，并将首次规划、所有求助/核验、风险请求、UI 观测和失败重试计入总成本。

没有复制上述项目实现或分发其代码；这里记录的是源码观察和设计借鉴。四个来源在所查提交均为 MIT 项目，本项目代码独立维护。
