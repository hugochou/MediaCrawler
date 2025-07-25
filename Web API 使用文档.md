# MediaCrawler Web API 使用文档

这份文档描述了如何通过 Web API 接口远程触发和控制 MediaCrawler 爬虫的运行。这使得您可以将 MediaCrawler 集成到自动化工作流中，例如使用 `n8n`。

## 目录
1.  简介 [<sup>1</sup>](#1-简介)
2.  先决条件 [<sup>2</sup>](#2-先决条件)
    *   项目结构 [<sup>3</sup>](#项目结构)
    *   Python 虚拟环境与依赖 [<sup>4</sup>](#python-虚拟环境与依赖)
    *   Playwright 浏览器 [<sup>5</sup>](#playwright-浏览器)
3.  API 端点详情 [<sup>6</sup>](#3-api-端点详情)
    *   请求 URL [<sup>7</sup>](#请求-url)
    *   请求方法 [<sup>8</sup>](#请求方法)
    *   请求体 (JSON) 参数 [<sup>9</sup>](#请求体-json-参数)
    *   响应格式 [<sup>10</sup>](#响应格式)
    *   示例请求 [<sup>11</sup>](#示例请求)
4.  如何运行 API 服务 [<sup>12</sup>](#4-如何运行-api-服务)
5.  数据存储与获取 [<sup>13</sup>](#5-数据存储与获取)
6.  重要注意事项与限制 [<sup>14</sup>](#6-重要注意事项与限制)
    *   登录方式 [<sup>15</sup>](#登录方式)
    *   并发请求与全局配置 [<sup>16</sup>](#并发请求与全局配置)
    *   错误处理 [<sup>17</sup>](#错误处理)
    *   声明与责任 [<sup>18</sup>](#声明与责任)

---

## 1. 简介

本 Web API 封装了 MediaCrawler 的核心功能，允许通过发送 HTTP POST 请求来触发爬取任务。API 接收 JSON 格式的参数，动态配置爬虫行为（如选择平台、爬取类型、关键词等），并通过 MediaCrawler 自身的机制将数据存储到配置的数据库中。

## 2. 先决条件

在运行和使用 MediaCrawler Web API 之前，请确保您的系统满足以下条件：

### 项目结构

确保您的 `MediaCrawler` 项目目录包含以下文件和结构（基于我之前提供的文件）：

```
MediaCrawler/
├── venv/                     # Python 虚拟环境
├── config/                   # MediaCrawler 配置文件
├── media_platform/           # 各平台爬虫实现
├── main.py                   # MediaCrawler 主入口
├── requirements.txt          # 项目依赖
├── mediacrawler_runner.py    # API 核心运行封装 (新文件)
└── api_server.py             # Flask Web API 服务器 (新文件)
```

### Python 虚拟环境与依赖

1.  **激活虚拟环境：** 在终端中导航到 `MediaCrawler` 项目的根目录，并激活您的 Python 虚拟环境 `venv`。
    *   **macOS/Linux:** `source venv/bin/activate`
    *   **Windows (Command Prompt):** `.\venv\Scripts\activate.bat`
    *   **Windows (PowerShell):** `.\venv\Scripts\Activate.ps1`
    激活后，您的命令行提示符前应显示 `(venv)`。

2.  **安装 Flask：** `api_server.py` 使用 Flask 框架。在激活的虚拟环境中，执行以下命令安装 Flask：
    ```bash
    pip install Flask
    ```
    *   **推荐：** 更新您的 `requirements.txt` 文件以包含 Flask。在激活的虚拟环境中运行 `pip freeze > requirements.txt`。

3.  **其他依赖：** 确保 `requirements.txt` 中列出的所有 MediaCrawler 核心依赖（包括 `playwright`, `httpx`, `aiomysql` 等）都已在虚拟环境中安装。如果尚未安装，请在激活虚拟环境后运行：
    ```bash
    pip install -r requirements.txt
    ```

### Playwright 浏览器

MediaCrawler 依赖 Playwright 来模拟浏览器行为。请确保您已在运行 `api_server.py` 的机器上安装了 Playwright 浏览器驱动：

```bash
playwright install
```

## 3. API 端点详情

### 请求 URL

*   **本地开发/测试:** `http://127.0.0.1:5000/crawl` 或 `http://localhost:5000/crawl`
*   **n8n (Docker 容器访问主机):** `http://host.docker.internal:5000/crawl`
*   **其他机器/外部网络访问:** `http://<您的Mac的IP地址>:5000/crawl` (如果防火墙允许)

### 请求方法

`POST`

### 请求体 (JSON) 参数

`Content-Type: application/json`

| 参数名              | 类型      | 是否必需 | 描述                                                                                                       | 示例值                                                    |
| :------------------ | :-------- | :------- | :--------------------------------------------------------------------------------------------------------- | :-------------------------------------------------------- |
| `platform`          | `string`  | 是       | 要爬取的媒体平台。                                                                                         | `"xhs"`, `"dy"`, `"ks"`, `"bili"`, `"wb"`, `"tieba"`, `"zhihu"` |
| `type`              | `string`  | 是       | 爬取类型。值必须为 `"search"` (按关键词搜索帖子) 或 `"detail"` (按帖子ID获取详情)。                     | `"search"`, `"detail"`                                    |
| `login_type`        | `string`  | 否       | 登录方式。目前主要支持 `"qrcode"`。默认为 `"qrcode"`。                                                    | `"qrcode"`                                                |
| `save_data_option`  | `string`  | 否       | 数据保存选项。`"sqlite"` (SQLite数据库), `"db"` (MySQL等，需在 `config` 中配置), 或 `null`/不提供 (不保存)。 | `"sqlite"`, `"db"`, `null`                                |
| `keywords`          | `array`   | 当 `type="search"` 时必需 | 关键词列表，用于搜索模式。例如 `["健身食谱", "国风穿搭"]`。当 `type="detail"` 时忽略。 | `["健身食谱", "国风穿搭"]`                                |
| `detail_ids`        | `array`   | 当 `type="detail"` 时必需 | 帖子 ID 列表，用于详情模式。例如 `["63273418e...", "63273418e..."]`。当 `type="search"` 时忽略。 | `["63273418e2ddb40001010101", "63273418e2ddb40001010102"]` |
| `enable_get_comments` | `boolean` | 否       | 是否开启评论爬取。默认为 `MediaCrawler` `config/base_config.py` 中的值。                                   | `true`, `false`                                           |
| `[其他config参数]`  | `any`     | 否       | 您可以通过键值对形式传入 `config` 模块中定义的其他大写参数 (例如 `MAX_CONCURRENT_REQUESTS`)。               | `{"MAX_CONCURRENT_REQUESTS": 5}`                          |

### 响应格式

API 将返回一个 JSON 对象，指示爬取任务的状态和基本信息。

**成功响应示例:**
```json
{
  "status": "success",
  "message": "MediaCrawler task initiated successfully.",
  "platform": "xhs",
  "type": "search",
  "keywords": ["健身食谱"],
  "detail_ids": null,
  "save_data_option": "sqlite"
}
```

**错误响应示例 (客户端参数错误):**
```json
{
  "error": "Missing 'platform' parameter.",
  "status": "error",
  "message": "Missing 'platform' parameter."
}
```

**错误响应示例 (内部服务器错误):**
```json
{
  "status": "error",
  "message": "An internal server error occurred: [Error details]",
  "details": "..."
}
```

### 示例请求

**1. 搜索小红书关键词并保存到 SQLite (开启评论)：**

```json
{
  "platform": "xhs",
  "type": "search",
  "keywords": ["宠物搞笑", "家常菜"],
  "save_data_option": "sqlite",
  "enable_get_comments": true
}
```

**2. 获取B站指定帖子详情并保存到 MySQL (不获取评论)：**

```json
{
  "platform": "bili",
  "type": "detail",
  "detail_ids": ["BV1Px411F7b3", "BV1Sx411F7c7"],
  "save_data_option": "db",
  "enable_get_comments": false
}
```

**3. 搜索抖音视频 (不保存数据)：**

```json
{
  "platform": "dy",
  "type": "search",
  "keywords": ["城市风光"],
  "save_data_option": null
}
```

## 4. 如何运行 API 服务

1.  **打开终端/命令行工具。**
2.  **导航到 `MediaCrawler` 项目的根目录** (即 `api_server.py` 所在的目录)。
3.  **激活 Python 虚拟环境：**
    ```bash
    source venv/bin/activate
    ```
    (Windows: `.\venv\Scripts\activate.bat` 或 `.\venv\Scripts\Activate.ps1`)
4.  **运行 API 服务器：**
    ```bash
    python api_server.py
    ```
    您将看到类似 `* Running on http://0.0.0.0:5000/ (Press CTRL+C to quit)` 的输出。这意味着 API 服务已在您的 macOS 主机上启动并监听 5000 端口。

## 5. 数据存储与获取

*   **API 的职责：** 本 Web API 的主要职责是触发并管理 MediaCrawler 爬取任务的执行。
*   **数据保存：** 爬取到的数据将根据您在请求中指定的 `save_data_option` (例如 `sqlite` 或 `db`)，由 MediaCrawler 自行保存到配置的数据库文件或数据库服务器中。
*   **数据获取：** **本 API 默认不会将爬取到的数据通过 HTTP 响应返回。** 如果您需要通过 API 获取爬取结果，您需要：
    1.  在 `mediacrawler_runner.py` 的爬取完成逻辑中，添加代码从 MediaCrawler 使用的数据库中查询最新数据。
    2.  将这些查询到的数据序列化为 JSON，并包含在 API 的响应体中。
    这需要您熟悉 MediaCrawler 的数据存储结构。

## 6. 重要注意事项与限制

### 登录方式

*   当 `login_type` 设置为 `"qrcode"` 时，MediaCrawler 将会尝试在运行 API 服务的机器上打开一个浏览器窗口，显示二维码供您扫码登录。这意味在自动化过程中，您可能需要手动干预完成登录步骤（例如，首次运行时）。
*   对于完全自动化，如果 MediaCrawler 支持，您可能需要考虑配置基于 Cookie 的登录方式，以避免频繁的手动扫码。

### 并发请求与全局配置

*   `mediacrawler_runner.py` 通过临时修改 MediaCrawler 内部的全局 `config` 变量来设置爬取参数。
*   **潜在风险：** 如果有多个 `n8n` 工作流或 HTTP 请求几乎同时调用此 API，它们可能会相互覆盖 `config` 设置，导致爬取结果混淆或出现意外行为。
*   **建议 (生产环境)：** 对于高并发或需要严格任务隔离的场景，建议在 API 层和爬虫执行层之间引入一个任务队列（如 Redis + Celery/RQ）。API 接收请求后，将任务参数推送到队列，由独立的 Worker 消费者按顺序或并行处理。

### 错误处理

*   API 提供了基本的错误处理，会返回带有 `error` 或 `status: "error"` 字段的 JSON 响应。
*   请检查响应状态码 (例如 400 Bad Request, 500 Internal Server Error) 和响应体中的错误信息以诊断问题。
*   详细的爬取日志将输出到运行 `api_server.py` 的终端窗口。

### 声明与责任

*   本代码仅供学习和研究目的使用。
*   使用者应遵守目标平台的使用条款和 `robots.txt` 规则。
*   不得进行大规模爬取或对平台造成运营干扰。
*   应合理控制请求频率，避免给目标平台带来不必要的负担。
*   不得用于任何非法或不当的用途。
*   使用本代码即表示您同意遵守上述原则和项目根目录下 `LICENSE` 文件中的所有条款。