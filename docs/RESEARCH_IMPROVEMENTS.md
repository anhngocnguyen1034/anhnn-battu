# 玄冥 Cyber-Bazi 调研与改进建议

本文档为「先参考成熟方案、再改进」的调研结论，**不直接修改业务代码**。供后续基于 lunar-python 与开源实现做五行/格局/古籍增强时参考。

---

## 一、已参考的成熟方案

### 1. lunar-python（6tail/lunar-python）

- **用途**：排盘已在使用；其 `LunarUtil` 提供权威常量，可替代手写表。
- **路径**：pip 安装包内的 `lunar_python/util/LunarUtil.py`（即 `lunar_python.util.LunarUtil`）。

**可直接引用的常量：**

| 常量 | 说明 | 与当前项目对比 |
|------|------|----------------|
| `LunarUtil.WU_XING_GAN` | 天干→五行（甲乙木、丙丁火…） | 与 `wuxing_calculator.GAN_TO_ELEMENT`、china-testing `gan5` 一致 |
| `LunarUtil.WU_XING_ZHI` | 地支本气五行（寅卯木、巳午火…） | 可用于地支五行、冲刑合会辅助 |
| `LunarUtil.ZHI_HIDE_GAN` | 地支藏干列表（子→[癸]，丑→[己,癸,辛]…） | 与当前 `ZHI_HIDDEN_STEMS`、china-testing `zhi5_list` 完全一致 |
| `LunarUtil.SHI_SHEN` | 十神：键为「日干+他干」如 "甲丙"→"食神" | 与当前 `geju_analyzer.SHISHEN_MAP` 逻辑一致，可统一用 lunar 表 |

**EightChar API（若用 lunar 排盘扩展）：**

- `getYearHideGan()` / `getMonthHideGan()` 等：月令藏干可直接取，避免手写。
- `getYearDiShi()` 等：十二长生（地势），可与现有 `dishi` 对接或替代。

**建议**：五行/格局模块中，藏干、十神、天干地支五行**优先从 `LunarUtil` 读取**，删除或收敛手写常量，减少维护与出错面。

---

### 2. china-testing/bazi（Python 八字排盘）

- **仓库**：<https://github.com/china-testing/bazi>
- **特点**：五行分数、冲刑合会、十神、十二长生、建禄/从格等；README 称「凝聚大师多年经验的评判」。

**核心文件与逻辑：**

- **datas.py**：纳音、旬空、命宫、日柱释义、神煞等大量静态数据。
- **ganzhi.py**：
  - `zhi5`：地支藏干**本中余气权重**（OrderedDict），如 `子: {癸:8}`，`丑: {己:5, 癸:2, 辛:1}`，`寅: {甲:5, 丙:2, 戊:1}`。与 lunar `ZHI_HIDE_GAN` 顺序一致，权重可参考。
  - `zhi5_list`：藏干列表，与 lunar 一致。
  - `ten_deities`：按日干给出十神（天干）与十二长生（地支），如甲见丙为食、见寅为建禄。
  - `zhi_atts`：每支的冲、刑、被刑、合、会、害、破、六合、暗合。
  - `chongs`、`zhi_6hes`、`zhi_3hes`、`zhi_half_3hes`、`zhi_xings`、`zhi_poes`、`zhi_haies`：冲、六合、三合、半三合、刑、破、害的完整关系。
  - `gan5` / `zhi_wuhangs`：天干/地支五行。
- **bazi.py**（约 204–260 行）：
  - **五行分数**：`scores = {金:0, 木:0, ...}`；天干每字 +5 到对应五行（`gan5[item]`）；地支按 `zhi5[支][干]` 权重加分，**月支重复计一次**（`list(zhis) + [zhis.month]`）。参考：<http://www.131.com.tw/word/b3_2_14.htm>。
  - **身强**：`strong = 比+劫+枭+印` 的 `gan_scores` 之和（按天干计）；「弱」看十二长生是否有 长/帝/建，或比+库>2。
  - **专格/从格提示**：`max(scores.values()) > 25` 时提示考虑专格或从格。

**与当前实现的对比：**

| 项目 | china-testing/bazi | 当前 cyber-bazi |
|------|--------------------|-----------------|
| 藏干数据 | 与 lunar 一致，另有本中余权重 8/5,2,1 | 藏干列表一致；权重 6,3,1 + 月令 1.5 倍 |
| 五行分数 | 天干 5 分/字；地支 zhi5 权重；月支×2 | 天干 10×月令系数×长生系数；藏干 6,3,1×月令 1.5 |
| 身强 | 比劫枭印 gan_scores 和 | 日主五行占比 ≥35% 为身旺 |
| 从格 | 某行>25 分提示 | 日主≤15% 且他行≥40% 判从格可能 |

**建议**：  
- 五行分数算法可保留当前思路，但**数据源**（藏干、十神、五行）改为 lunar；权重可对照 china-testing 的 `zhi5`（8/5,2,1）做一次校准或提供选项。  
- 冲刑合会：当前 `bazi_engine` 已有一部分；可对照 `ganzhi.py` 的 `zhi_atts`、`zhi_3hes`、`zhi_xings` 等查漏（如三会、半三合、破、害）。

---

### 3. Cantian AI 格局说明（三命通会 / 渊海子平）

- **链接**：<https://www.cantian.ai/wiki/zh-Hans/other_words_explanations/geju/>

**取格要点（摘要）：**

- 以**月令地支**为主，看本气、中气、余气；天干**透出**（天透地藏）则取格；除比劫外八格（正偏印、食伤、正偏财、正官、七杀）。
- **取格顺序**：  
  1）地支三会/三合且无隔，可取偏格；  
  2）多格并存时以当令与排位先后论；  
  3）同五行两格（如官杀并存）视作七杀格等；  
  4）有天透地藏即取格；  
  5）月支藏干不透时，以月干坐根与年日时支为第三优先；  
  6）月支藏干透年/时为第二优先；  
  7）月支藏干透月干为第一优先。
- **分类**：普通格（八格）、专旺格（曲直、炎上、稼穑、从革、润下）、从格、特殊格（飞天禄马、壬骑龙背等）；成格/破格条件各格不同。

**与当前 `geju_analyzer` 的对比：**

- 当前：月令主气、是否透干、日主力量占比 → 正格/身旺身弱/从格、格局名称。
- 缺失：取格顺序（透年/时/月）、三会三合取偏格、成格破格细则、专旺五格与大量特殊格名称与条件。

**建议**：  
- 先做「取格顺序」与「天透地藏」的严格实现（月干/年干/时干谁透、按顺序取格）。  
- 再逐步把 Cantian 文档中的常见格局（建禄、魁罡、从财从杀等）做成规则或查表，与 `analyze_geju` 输出对齐；成格/破格可先做少数常见格（如正官格忌官杀混杂、刑冲）。

---

### 4. 穷通宝鉴 / 调候用神

- **当前**：`prompts/ancient_texts.py` 已按「10 天干 × 4 季节」收录调候用神条文，并在 `build_system_prompt` 中注入。
- **外部参考**：大家找算命网等有按月份逐条文本；完整开源电子版较少，多为网站或 PDF。  
- **建议**：保持现有静态条文；若扩展，可对照权威版本校对「月令-用神」对应关系，并注明出处（如《穷通宝鉴》某章）。

---

## 二、改进项汇总（实施时再改代码）

1. **统一数据源**  
   - 在 `wuxing_calculator`、`geju_analyzer` 中改用 `LunarUtil.WU_XING_GAN`、`LunarUtil.WU_XING_ZHI`、`LunarUtil.ZHI_HIDE_GAN`、`LunarUtil.SHI_SHEN`，逐步移除手写 `GAN_TO_ELEMENT`、`ZHI_HIDDEN_STEMS`、`SHISHEN_MAP`（或仅作 fallback）。

2. **五行分数**  
   - 保持「天干 + 月令加权 + 十二长生 + 藏干」思路；  
   - 藏干权重可参考 china-testing 的 8/5,2,1 做对比或可选方案；  
   - 若使用 lunar 的 `EightChar.getXxxDiShi()`，十二长生与现有 `dishi` 统一。

3. **格局**  
   - 按 Cantian 取格顺序实现「月干透 / 年时透 / 月干坐根」优先级；  
   - 增加三会、三合取偏格判断；  
   - 常见格（建禄、魁罡、从财从杀、伤官配印等）与 `analyze_geju` 输出字段对齐；成格/破格先做少数常见规则。

4. **刑冲合会**  
   - 对照 china-testing `ganzhi.py` 的 `zhi_atts`、三合/三会/刑/破/害 表，在 `bazi_engine` 或单独模块中补全并复用，与 `query_xing_chong_he_hai` 等工具一致。

5. **古籍与调候**  
   - 维持 `ancient_texts` 静态条文；若有新增，注明出处并尽量与权威版本校对。

---

## 三、参考链接与本地路径

- lunar-python 源码：见 PyPI 包 `lunar_python`（pip 安装后的 `lunar_python/` 目录），或上游仓库 <https://github.com/6tail/lunar-python>
- china-testing/bazi：<https://github.com/china-testing/bazi>（本次调研已抓取 bazi.py / datas.py / ganzhi.py 关键片段）
- Cantian 格局：<https://www.cantian.ai/wiki/zh-Hans/other_words_explanations/geju/>
- 五行分数参考：<http://www.131.com.tw/word/b3_2_14.htm>

文档结束。后续实现时按本文「改进项汇总」逐项落地，并保持纯 Python、可部署 Streamlit Cloud。
