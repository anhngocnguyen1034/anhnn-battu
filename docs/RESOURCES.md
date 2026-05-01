# 八字命理开源资源调研报告

> 为 FOR-BAZI 项目收集的开源资源、库、数据集和工具参考。

---

## 一、八字计算引擎 / 排盘库

### 1. china-testing/bazi（八字排盘软件）
- **URL**: https://github.com/china-testing/bazi
- **语言**: Python
- **星标**: 1.3k
- **功能**: Python 八字排盘软件，可清晰看出冲刑合会、阴阳等关系，包含凝聚大师多年经验的评判功能，另有合婚、风水等功能
- **集成评估**: 最成熟的 Python 八字排盘开源项目，适合作为核心计算引擎参考

### 2. 6tail/lunar-python（农历工具库）
- **URL**: https://github.com/6tail/lunar-python
- **语言**: Python | 许可证: MIT
- **星标**: 594 | 版本: v1.4.8
- **功能**: 无第三方依赖的日历工具库，支持公历、农历、佛历、道历。涵盖干支、生肖、八字、五行、十神、纳音、节气、节日、喜神/福神/财神方位、胎神方位、彭祖百忌、每日宜忌、星宿、建除十二值星等
- **集成评估**: 功能非常全面的底层历法库，八字计算依赖准确的历法转换，适合作为基础依赖

### 3. 6tail/lunar-javascript（JavaScript 版农历库）
- **URL**: https://github.com/6tail/lunar-javascript
- **语言**: JavaScript | 许可证: MIT
- **星标**: 1.5k | 版本: v1.7.7
- **功能**: 与 lunar-python 同源的 JavaScript 版本，功能完全一致
- **集成评估**: 前端八字排盘的最佳选择
- **API 示例**:
  ```javascript
  const { Lunar, Solar, EightChar } = require('lunar-javascript');
  const solar = Solar.fromYmd(2000, 1, 1);
  const lunar = solar.getLunar();
  const eightChar = lunar.getEightChar();
  ```

### 4. sxtwl（寿星天文历 Python 封装）
- **URL**: https://github.com/yuangu/sxtwl_cpp
- **PyPI**: `pip install sxtwl`
- **语言**: C++ 核心 + Python 封装 | 许可证: BSD
- **版本**: 2.0.7
- **功能**: 基于 C++ 实现的天文历法库，BC722年以后与实历相符，支持公历农历互转、天干地支查询、二十四节气、生肖星座、四柱反查（根据八字反查日期）
- **集成评估**: 计算精度高（基于天文算法），查询范围广，适合作为高精度计算后端

### 5. cnlunar（中国农历历法库）
- **URL**: https://github.com/opn48/cnlunar
- **PyPI**: `pip install cnlunar`
- **语言**: Python | 许可证: MIT
- **版本**: 0.2.4
- **功能**: 基于《钦定协纪辨方书》的农历历法库，提供八字表达、每日宜忌、十二神、二十八星宿、纳音、七十二物候、星次、彭祖百忌、中医时辰经络等。使用香港天文台数据确保精度
- **集成评估**: 特色在于神煞宜忌均有古籍依据，适合需要黄历功能的场景

---

## 二、紫微斗数相关库（与八字互补）

### 6. SylarLong/iztro（紫微斗数排盘库）
- **URL**: https://github.com/SylarLong/iztro
- **语言**: TypeScript | 许可证: MIT
- **星标**: 3.6k（命理类最高星标项目）| 版本: v2.5.8
- **功能**: 紫微斗数排盘的轻量级 JavaScript 开源库。支持星盘生成、命理信息获取、运限分析（大限/小限/流年/流月/流日/流时）、星耀查询、飞星判断、链式调用 API。支持简繁中文、英文、日文、韩文、越南语。v2.3.0 起支持插件系统适配不同流派
- **在线工具**: https://ziwei.pub
- **集成评估**: 紫微斗数领域最成熟的开源库

---

## 三、MCP 服务器

### 7. SiwuXue/yijing-bazi-mcp-server（易经八字分析 MCP 服务器）
- **URL**: https://github.com/SiwuXue/yijing-bazi-mcp-server
- **语言**: JavaScript (Node.js)
- **星标**: 27 | 安装: `npx yijing-bazi-mcp@latest`
- **功能**: 基于 MCP 协议的易经与八字分析服务，提供 10 个工具：
  - 易经类：`yijing_generate_hexagram`、`yijing_interpret`、`yijing_advise`
  - 八字类：`bazi_generate_chart`、`bazi_analyze`、`bazi_forecast`
  - 综合类：`combined_analysis`、`destiny_consult`
  - 学习类：`knowledge_learn`、`case_study`
- **客户端支持**: Claude Desktop、Trae、Cursor、Cherry Studio
- **集成评估**: 直接可用的 MCP 服务器，npx 一键启动

### 8. AlbertHuangKSFO/lunar_mcp_server（中国农历 MCP 服务器）
- **URL**: https://github.com/AlbertHuangKSFO/lunar_mcp_server
- **语言**: Python | 星标: 3
- **功能**: 中国农历 MCP 服务器，包含八字、命理、节气等功能
- **集成评估**: Python 实现，适合 Python 技术栈集成

### 9. YuchengMaUTK/fortune-teller（霄占 - AI 算命平台）
- **URL**: https://github.com/YuchengMaUTK/fortune-teller
- **语言**: Python | 许可证: MIT | 星标: 11
- **功能**: 基于 Python 的 AI 算命平台，支持八字命理、塔罗牌、西方星座三大体系。每种占卜系统有专门的 AI Agent，基于 MCP Tools 实现精确计算。支持 AWS Bedrock/OpenAI/Anthropic 多后端，支持中英双语，流式输出
- **集成评估**: 架构设计优秀（Agent + MCP Tools 分离），适合作为 AI 命理应用的参考架构

---

## 四、AI 命理分析系统

### 10. DadanLuo/bazi_agent（赛博司命八字分析 Agent）
- **URL**: https://github.com/DadanLuo/bazi_agent
- **语言**: Python | 星标: 3
- **技术栈**: FastAPI, LangChain, LangGraph, ChromaDB, OpenAI GPT-4
- **功能**: 基于大语言模型的智能八字命理分析系统，将传统命理规则与现代 AI 技术融合。使用 LangGraph 工作流编排，ChromaDB 向量数据库存储命理规则知识
- **集成评估**: LangGraph + RAG 架构值得参考

### 11. curionox/lifekline（人生K线）
- **URL**: https://github.com/curionox/lifekline
- **语言**: TypeScript (React 19 + Vite + Recharts) | 星标: 666
- **功能**: 将八字命理与金融K线图结合，可视化人生运势走势。用户输入四柱干支和大运信息，通过精心设计的 Prompt 让 AI 生成运势数据，以K线图展示1-100岁运势
- **特色**: 无需 API Key，生成 Prompt 后复制到任意 AI 平台即可
- **集成评估**: 创新的可视化方案，前端技术可参考

---

## 五、命理评测基准

### 12. DestinyLinker/MingLi-Bench（命理基准测试）
- **URL**: https://github.com/DestinyLinker/MingLi-Bench
- **语言**: Python | 许可证: MIT | 星标: 117
- **功能**: 评估 LLM 在中国传统命理（八字和紫微斗数）上表现的基准测试。题库来源于"全球算命师大赛"2022-2025年真题，包含 160 道标准化多选题，覆盖事业、健康、婚姻、子女、财运等12个人生维度
- **特色**:
  - Chain-of-Thought 模式测试推理能力
  - 星盘注入模式（使用 iztro 预计算命盘）分离排盘准确性与推理能力
  - 支持 OpenRouter/OpenAI/Anthropic/Google/DeepSeek 多模型评测
- **集成评估**: 评估 AI 命理能力的标准工具，数据集本身也是宝贵的命理知识资源

---

## 六、综合命理平台（参考架构）

### 13. FateAtelier（命运工坊）
- **URL**: https://github.com/sy-vendor/FateAtelier
- **语言**: TypeScript + React 18 + Vite | 许可证: MIT | 星标: 25
- **功能**: 17个模块的综合占卜 Web 应用，包含八字算命、紫微斗数、奇门遁甲、塔罗占卜、风水罗盘、择日吉时等
- **在线**: https://www.fateatelier.cloud
- **集成评估**: 功能最全面的前端参考项目

### 14. tianjiyao-ai-fortune（天机爻）
- **URL**: https://github.com/wych1987/tianjiyao-ai-fortune
- **技术栈**: Next.js 14, Azure Functions, Supabase, MongoDB, Redis, Pinecone
- **星标**: 18 | 许可证: MIT
- **功能**: AI 驱动的在线命理平台，含八字、紫微斗数、配对匹配。使用 GPT-4 Turbo + 知识图谱增强，多层缓存实现 <200ms 响应
- **集成评估**: 完整的商业化架构参考

---

## 七、历法工具库（6tail 生态）

### 15. 6tail/tyme4ts（Tyme - Lunar 升级版）
- **URL**: https://github.com/6tail/tyme4ts
- **语言**: TypeScript | 许可证: MIT | 星标: 425
- **版本**: v1.4.6
- **功能**: Lunar 的升级版日历工具库，支持公历、农历、藏历、星座、干支、生肖、节气、法定假日
- **文档**: https://6tail.cn/tyme.html
- **集成评估**: 6tail 生态的最新力作，设计更优、扩展性更强

---

## 八、古典文本 / 数据集资源

### 16. chinese-poetry/chinese-poetry（中华古诗词数据库）
- **URL**: https://github.com/chinese-poetry/chinese-poetry
- **星标**: 49k+
- **内容**: 最全面的中国古典诗词数据库，含唐诗、宋词、宋诗、楚辞、诗经等，约10万+首，JSON/CSV 格式
- **集成评估**: 数据组织方式可作为命理古籍数字化的参考

### 17. ctext.org（中国哲学书电子化计划）
- **URL**: https://ctext.org | API: https://ctext.org/tools/api
- **内容**: 最大的先秦至清代中文文本数字图书馆，包含易经及注释
- **集成评估**: 提供公开 API，可用于获取易经相关文本

### 18. 古典命理文本获取建议
目前未发现将滴天髓、子平真诠、渊海子平、穷通宝鉴、三命通会等命理经典系统数字化并结构化为数据集的开源项目。建议：
- **ctext.org** API 获取易经相关文本
- **国学大师** (guoxuedashi.com) 获取命理古籍全文
- 自行构建命理知识库，将古籍文本分段标注后存入向量数据库（如 ChromaDB/Milvus）

---

## 九、综合评估与集成建议

### 推荐技术栈组合

| 层级 | 推荐方案 | 理由 |
|------|---------|------|
| **八字计算引擎** | china-testing/bazi 或 6tail/lunar-python | 最成熟的开源方案 |
| **历法基础** | sxtwl + cnlunar | 高精度天文计算 + 神煞宜忌 |
| **前端排盘** | 6tail/lunar-javascript 或 tyme4ts | 1.5k 星标，API 友好 |
| **紫微斗数** | SylarLong/iztro | 3.6k 星标，最成熟的紫微库 |
| **MCP 接入** | yijing-bazi-mcp-server | 即开即用的 MCP 服务器 |
| **AI Agent 架构** | 参考 fortune-teller 的 Agent + MCP Tools 分离设计 | 架构清晰 |
| **命理评测** | MingLi-Bench | 标准化评测基准 |
| **可视化** | 参考 lifekline 的 K 线图方案 | 创新的运势可视化 |
| **命理知识库** | 自建向量数据库 + 古籍文本 | 无现成开源数据集 |

### 关键发现

1. **八字计算引擎方面**，Python 生态最成熟的是 `china-testing/bazi`（1.3k 星）和 `6tail/lunar-python`（594 星），JavaScript 生态最强的是 `6tail/lunar-javascript`（1.5k 星）
2. **MCP 服务器**已有 `yijing-bazi-mcp-server`（27 星）可直接使用
3. **命理古籍数字化**是明显空白，需自行构建
4. **AI + 命理**方向项目众多但成熟度普遍不高，MingLi-Bench（117 星）是最有价值的评测工具
5. **6tail 生态**（lunar-python / lunar-javascript / tyme4ts）是底层历法计算的最佳选择
