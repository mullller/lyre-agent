# Lyre Desktop Client — Design Blueprint

参考 Hermes Desktop 的设计理念，为 Lyre Agent 设计原生桌面客户端。

## 核心理念（借鉴 Hermes Desktop）

| 原则 | 说明 |
|------|------|
| **克制与专注** | 不取代 CLI，而是增强它。CLI 做重活，GUI 做管理和概览。 |
| **直连 SSH** | 直接通过 SSH 连接到 Lyre Agent 主机，无需额外网关 API。 |
| **单一事实来源** | 始终以远程 Lyre Agent 主机为唯一数据来源。 |
| **无本地镜像** | 不在客户端缓存或镜像文件，避免同步延迟和状态冲突。 |
| **零远程依赖** | 不需要在远程主机安装任何辅助服务。 |

## Lyre Agent 的差异化定位

Lyre Agent 相比 Hermes Agent 更轻量：

| 维度 | Hermes | Lyre |
|------|--------|------|
| 依赖 | 多（数据库、网关、多平台） | 极少（仅 rich） |
| 配置 | YAML + 运行时代理 | 单文件 JSON (`~/.lyre-agent/config.json`) |
| 会话 | 持久化到 state.db | 暂未实现（可参考设计） |
| 工具 | 丰富的内置工具集 | 6 个核心工具 (shell/file×3/git×2) |
| 平台 | 多平台网关 | 纯 CLI 本地优先 |

因此 Lyre Desktop 的设计应比 Hermes Desktop 更**精简**：

- **无技能管理**：Lyre 暂无 skills 体系，暂不需要图形化技能浏览器。
- **无用量统计**：Lyre 暂未设计 token 计数，可后续添加。
- **聚焦核心**：SSH 连接、会话管理、配置文件编辑、终端。

## 架构概览

```
┌─────────────────────────────────────────┐
│              Lyre Desktop                │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐  │
│  │ 会话管理 │ │ 配置编辑 │ │ SSH 终端  │  │
│  └────┬────┘ └────┬─────┘ └────┬─────┘  │
│       │           │            │         │
│       └───────────┼────────────┘         │
│                   │                      │
│            ┌──────┴──────┐               │
│            │  SSH Layer   │               │
│            └──────┬──────┘               │
└───────────────────┼─────────────────────┘
                    │
            ════════╪════════
                    │
┌───────────────────┴─────────────────────┐
│           Lyre Agent Host               │
│  ~/.lyre-agent/config.json              │
│  lyre-agent CLI (run/chat/config)       │
└─────────────────────────────────────────┘
```

## 功能规划

### MVP（最小可用版本）

1. **SSH 连接管理**
   - 支持 `~/.ssh/config` 别名
   - 支持直接填写 Host/User/Port
   - 连接测试按钮（检查 SSH 可达 + python3 + lyre-agent CLI）

2. **会话 TUI**
   - 在 SSH 会话中启动 `lyre-agent chat`
   - 终端内的 Rich TUI 完美呈现

3. **配置文件编辑**
   - 远程编辑 `~/.lyre-agent/config.json`
   - 模型切换的可视化预设选择器
   - 冲突感知（多人编辑时提示）

### 第二阶段

4. **工作空间概览**
   - 显示当前 workspace 文件结构
   - Git 状态预览

5. **命令执行**
   - 预设常用命令按钮（如 `lyre-agent run "查看当前目录文件"`）
   - 自定义 prompt 输入

### 第三阶段

6. **会话历史**
   - 如果 Lyre 后续实现会话持久化，支持浏览历史会话

7. **跨平台**
   - 从 macOS 起步，后续扩展到 Windows/Linux

## 技术选型建议

参考 Hermes Desktop 的原生 Mac 路线，Lyre Desktop 可考虑两种路径：

### 方案 A：原生 SwiftUI（推荐，与 Hermes Desktop 一致）

- ✅ 最原生的 Mac 体验
- ✅ 内置 SSH 库支持好
- ❌ 开发成本高，需 Swift 开发能力
- ❌ 仅限 macOS

### 方案 B：基于 Tauri/Electron + xterm.js（跨平台优先）

- ✅ 跨平台（macOS/Windows/Linux）
- ✅ Web 前端技术，开发效率高
- ❌ 不如原生流畅
- ❌ 包体积大

### 方案 C：纯 CLI 增强（最小成本）

在 lyre-agent CLI 内增加：
- SSH 连接子命令：`lyre-agent remote add hermes-pi`
- 远程会话：`lyre-agent remote chat hermes-pi`
- 远程配置：`lyre-agent remote config hermes-pi`

✅ 零新增依赖，完全契合 Lyre 的极简哲学
❌ 没有 GUI

## 推荐的实现路径

**第一步（本文档当前阶段）：** 在 Lyre Agent 中实现方案 C 的 CLI 远程连接能力，作为 desktop 客户端的 CLI 基础层。

### CLI 远程连接子命令设计

```bash
# 添加远程主机
lyre-agent remote add pi   --host raspberrypi.local   --user alex   --port 22

# 列出已配置的主机
lyre-agent remote list

# 通过 SSH 在远程主机执行 lyre-agent
lyre-agent remote run pi "查看当前目录文件"

# 通过 SSH 启动远程交互式会话
lyre-agent remote chat pi

# 远程切换模型
lyre-agent remote model switch pi openai:gpt-4.1-mini

# 远程查看配置
lyre-agent remote config-show pi

# 远程编辑配置
lyre-agent remote config-edit pi
```

### 配置存储

远程主机配置存储在 `~/.lyre-agent/remotes.json`：

```json
{
  "remotes": {
    "pi": {
      "host": "raspberrypi.local",
      "user": "alex",
      "port": 22,
      "description": "客厅的树莓派"
    },
    "vps": {
      "host": "vps.example.com",
      "user": "root",
      "port": 22,
      "description": "云端 VPS"
    }
  }
}
```

## 参考资源

- Hermes Desktop 原文：https://m.aitntnews.com/newDetail.html?newId=24012
- Lyre Agent 仓库：https://github.com/mullller/lyre-agent
