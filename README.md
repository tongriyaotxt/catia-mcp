# CATIA MCP Server

> 作者：**田晓潼**

用于 Dassault Systèmes **CATIA V5**（及通过兼容 COM 接口的 V6）Windows 自动化控制的 Model Context Protocol (MCP) 服务器。

它将几乎所有常用 CATIA 操作——文档管理、2D 草图、3D 零件设计、装配、工程图、参数与公式、测量/分析、导出/视图控制——封装为强类型的 MCP 工具。任何兼容 MCP 的客户端（Claude Code、Claude Desktop、Continue 等）都可以直接驱动 CATIA，无需编写自定义胶水代码。

## 架构

```
Claude / MCP Client
       │  stdio / SSE (MCP JSON-RPC)
       ▼
catia_mcp/server.py  (FastMCP)
       │
       ▼
catia_mcp/tools/*.py  (业务逻辑)
       │
       ▼
win32com.client  →  CATIA.Application (COM)
```

## 环境要求

- **Windows** 系统，已安装 CATIA V5（或 V6）并注册为 COM 服务器
- **Python 3.11+**
- `pywin32`（已包含在依赖中）

> **提示：** 如果 CATIA 未作为 COM 服务器出现，请以管理员身份在 CATIA `bin` 目录下运行 `cnext.exe /regserver`。

## 安装

```bash
# 克隆或复制本文件夹
cd catia-mcp

# 安装依赖
pip install -e .

# 或使用 uv
uv pip install -e .
```

## 使用方式

### 1. stdio（默认 —— 适用于 Claude Code / Claude Desktop）

```bash
python -m catia_mcp
```

添加到 Claude Code：

```bash
claude mcp add catia -- python -m catia_mcp
```

或在 Claude Desktop 的 `settings.json` 中：

```json
{
  "mcpServers": {
    "catia": {
      "command": "python",
      "args": ["-m", "catia_mcp"]
    }
  }
}
```

### 2. Streamable HTTP（适用于远程 / Web 客户端）

```bash
python -m catia_mcp streamable-http
```

然后连接到 `http://localhost:8000/mcp`。

## 可用工具一览

| 类别 | 工具 |
|------|------|
| **元信息 / 连接** | `catia_status`, `ensure_catia_visible` |
| **文档** | `list_documents`, `get_active_document_info`, `open_document`, `new_document`, `save_document`, `save_as_document`, `close_document`, `close_all_documents`, `get_document_type` |
| **草图** | `create_sketch_on_plane`, `add_point`, `add_line`, `add_circle`, `add_rectangle`, `add_arc`, `close_sketch`, `get_sketch_elements` |
| **零件设计** | `create_pad`, `create_pocket`, `create_shaft`, `create_hole`, `create_fillet`, `create_chamfer`, `create_mirror`, `create_pattern`, `create_rib`, `create_slot`, `add_body`, `insert_in_body` |
| **装配** | `create_product`, `add_component`, `add_existing_component`, `update_product`, `get_product_tree`, `apply_constraint`, `move_component`, `explode_product`, `activate_product` |
| **测量** | `measure_distance`, `measure_length`, `measure_area`, `measure_volume`, `measure_inertia`, `get_bounding_box` |
| **参数** | `list_parameters`, `get_parameter_value`, `set_parameter_value`, `add_parameter`, `add_formula`, `update` |
| **工程图** | `create_drawing`, `create_sheet`, `create_view`, `add_dimension`, `add_annotation`, `update_sheet_links` |
| **导出 / 视图** | `export_to_stl`, `export_to_step`, `export_to_iges`, `export_to_pdf`, `capture_screenshot`, `fit_all_in`, `update_view` |

## 示例提示词

> *以下是将 MCP 服务器连接后，可以发送给 Claude 的自然语言请求示例。*

1. **打开零件并创建一个简单支架**
   > "新建一个零件，在 XY 平面上草绘一个 50×30 的矩形，拉伸到 10 mm，然后在中心打一个 5 mm 的孔。"

2. **驱动参数**
   > "将参数 `Length_1` 设为 120 mm，然后更新模型。"

3. **装配操作**
   > "新建一个产品，从 `C:\Parts\Base.CATPart` 添加一个现有组件，再添加一个新组件并沿 X 方向移动 50 mm。"

4. **导出**
   > "将当前文档导出为 `C:\Export\model.stp`，格式为 STEP AP214。"

5. **测量**
   > "测量当前 PartBody 的体积和包围盒。"

## 开发

```bash
# 代码检查
ruff check catia_mcp

# 使用 MCP Inspector 运行（需要 Node）
npx -y @modelcontextprotocol/inspector
# 若使用 HTTP 传输，连接至 http://localhost:8000/mcp
```

## 故障排除

| 问题 | 解决方案 |
|------|----------|
| 找不到 `CATIA.Application` | 确认已安装 CATIA。以管理员身份在 CATIA `bin` 文件夹中运行 `cnext.exe /regserver`。 |
| `No active document` | CATIA 必须已打开文档，或先使用 `new_document` / `open_document`。 |
| `Active document is not a Part document` | 某些工具仅适用于 `.CATPart`；切换到零件文档或使用 `new_document("Part")` 创建一个。 |
| 草图或特征失败 | 确保草图位于有效的支撑平面上，且轮廓在需要的位置是闭合的。 |

## 许可证

MIT
