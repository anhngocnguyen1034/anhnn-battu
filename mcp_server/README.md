# FOR-BAZI MCP Server

Model Context Protocol (MCP) server for Chinese calendar and Bazi (八字) calculations.
Exposes the FOR-BAZI engine as MCP tools for use with Claude Desktop and other MCP clients.

## Tools

| Tool | Description |
|------|-------------|
| `get_bazi` | 计算完整八字命盘：四柱、藏干、纳音、神煞、大运、五行、刑冲合害等 |
| `get_annual_ganzhi` | 查询某年干支与纳音 |
| `get_lunar_date` | 公历转农历日期 |
| `get_dayun` | 获取大运序列 |
| `get_shensha` | 获取四柱神煞信息 |
| `check_xingchong` | 检查刑冲合害关系 |
| `get_qiongtong_guidance` | 查询《穷通宝鉴》调候用神 |

## Installation

```bash
pip install -r mcp_server/requirements.txt
```

This installs:
- `mcp>=1.0.0` - MCP Python SDK
- `lunar-python>=1.4.8` - Chinese lunar calendar library

## Running

### As a module (recommended)

```bash
python -m mcp_server.server
```

### Directly

```bash
python mcp_server/server.py
```

## Claude Desktop Configuration

Add the following to your Claude Desktop config file:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "for-bazi": {
      "command": "python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:\\Users\\Gaaiyun\\Projects\\FOR-BAZI"
    }
  }
}
```

If using a virtual environment, specify the full Python path:

```json
{
  "mcpServers": {
    "for-bazi": {
      "command": "C:\\Users\\Gaaiyun\\Projects\\FOR-BAZI\\.venv\\Scripts\\python.exe",
      "args": ["-m", "mcp_server.server"],
      "cwd": "C:\\Users\\Gaaiyun\\Projects\\FOR-BAZI"
    }
  }
}
```

## Example Tool Calls

### get_bazi

Request:
```json
{
  "datetime_str": "1990-05-15 08:30:00",
  "gender": "male"
}
```

Returns the full Bazi chart with four pillars, ten gods, nayin, shensha, wuxing balance, dayun sequence, etc.

### get_annual_ganzhi

Request:
```json
{
  "year": 2026
}
```

Returns: `{"year": 2026, "ganzhi": "丙午", "nayin": "天河水", ...}`

### get_lunar_date

Request:
```json
{
  "date_str": "2026-01-29"
}
```

Returns lunar date details including year, month, day, ganzhi, zodiac, and leap month info.

### get_qiongtong_guidance

Request:
```json
{
  "day_master": "甲",
  "month_zhi": "寅"
}
```

Returns Qiongtong Baojian seasonal adjustment guidance for Jiǎ day master in Yín month.

### check_xingchong

Request:
```json
{
  "datetime_str": "1990-05-15 08:30:00",
  "gender": "male",
  "relation_type": "冲"
}
```

Returns all clash (冲) relationships found in the chart. Omit `relation_type` to get all relationship types.

## Project Structure

```
FOR-BAZI/
├── engine/
│   ├── bazi_engine.py    # Core Bazi calculation engine
│   └── shensha.py        # Shen Sha (spirit sha) calculations
├── tools/
│   └── bazi_tools.py     # Tool functions (dayun, xingchong, etc.)
├── prompts/
│   └── ancient_texts.py  # Qiongtong Baojian text database
└── mcp_server/
    ├── __init__.py
    ├── __main__.py        # Entry point for python -m
    ├── server.py          # MCP server implementation
    ├── requirements.txt
    └── README.md
```
