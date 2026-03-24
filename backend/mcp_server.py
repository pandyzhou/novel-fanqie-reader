#!/usr/bin/env python3
"""
番茄小说 MCP 服务器

为AI写作Agent提供番茄小说搜索和内容提取能力。
使用stdio模式，通过HTTP调用Flask API。

作者: Fanqie Reader Team
"""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# ==================== 配置 ====================

# Flask API基础URL（可通过环境变量配置）
API_BASE_URL = os.getenv("FLASK_API_URL", "http://localhost:5000")

# 轮询间隔（秒）
POLL_INTERVAL = 5

# 请求超时（秒）
REQUEST_TIMEOUT = 30


# ==================== HTTP客户端 ====================

class FlaskAPIClient:
    """Flask API HTTP客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
    
    def get(self, path: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """GET请求"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"HTTP请求失败: {str(e)}"}
    
    def post(self, path: str, json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """POST请求"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.post(url, json=json_data, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"HTTP请求失败: {str(e)}"}


# ==================== 辅助函数 ====================

def format_error(message: str) -> str:
    """格式化错误信息"""
    return json.dumps({"error": message}, ensure_ascii=False, indent=2)


def format_success(data: Any) -> str:
    """格式化成功响应"""
    return json.dumps(data, ensure_ascii=False, indent=2)


# 下载功能已禁用
# async def wait_for_download(...) 函数已被移除


def get_all_chapters(client: FlaskAPIClient, novel_id: str) -> List[Dict]:
    """
    获取小说所有章节列表（处理分页）
    
    Args:
        client: API客户端
        novel_id: 小说ID
    
    Returns:
        章节列表
    
    Raises:
        RuntimeError: 获取章节列表失败
    """
    all_chapters = []
    page = 1
    
    while True:
        data = client.get(
            f"/api/novels/{novel_id}/chapters",
            params={"page": page, "per_page": 200}
        )
        
        if "error" in data:
            raise RuntimeError(f"获取章节列表失败: {data['error']}")
        
        chapters = data.get("chapters", [])
        all_chapters.extend(chapters)
        
        # 检查是否还有更多页
        total_pages = data.get("pages", 1)
        if page >= total_pages:
            break
        
        page += 1
    
    return all_chapters


# ==================== MCP服务器 ====================

class FanqieNovelMCPServer:
    """番茄小说MCP服务器"""
    
    def __init__(self):
        self.server = Server("fanqie-novel-reader")
        self.client = FlaskAPIClient(API_BASE_URL)
        
        # 注册工具
        self._register_tools()
    
    def _register_tools(self):
        """注册所有MCP工具"""
        
        # 1. 搜索小说
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            return [
                Tool(
                    name="list_fanqie_novels",
                    description=(
                        "列出所有已就绪（可阅读）的番茄小说。只返回已下载并可以阅读的小说。"
                        "\n就绪条件：总章节数>100 或 已下载章节数>总章节数/3"
                        "\n\n参数："
                        "\n- page: 页码（可选，默认1）"
                        "\n- per_page: 每页数量（可选，默认20，最大50）"
                        "\n- search: 按标题搜索（可选，支持模糊匹配）"
                        "\n- sort: 排序字段（可选，可选值：last_crawled_at, created_at, total_chapters, title）"
                        "\n- order: 排序方式（可选，asc或desc，默认desc）"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "page": {
                                "type": "integer",
                                "description": "页码（默认1）",
                                "default": 1,
                                "minimum": 1
                            },
                            "per_page": {
                                "type": "integer",
                                "description": "每页数量（默认20，最大50）",
                                "default": 20,
                                "minimum": 1,
                                "maximum": 50
                            },
                            "search": {
                                "type": "string",
                                "description": "按标题搜索（可选）"
                            },
                            "sort": {
                                "type": "string",
                                "description": "排序字段（默认last_crawled_at）",
                                "enum": ["last_crawled_at", "created_at", "total_chapters", "title"],
                                "default": "last_crawled_at"
                            },
                            "order": {
                                "type": "string",
                                "description": "排序方式（默认desc）",
                                "enum": ["asc", "desc"],
                                "default": "desc"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="search_fanqie_novels",
                    description=(
                        "搜索番茄小说。支持按关键词搜索番茄小说网站，返回小说列表（包含ID、标题、作者、封面、简介、分类）。"
                        "\n参数："
                        "\n- query: 搜索关键词（必需）"
                        "\n- offset: 分页偏移量（可选，默认0，每次返回10条结果）"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "搜索关键词（必需）"
                            },
                            "offset": {
                                "type": "integer",
                                "description": "分页偏移量（默认0）",
                                "default": 0
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_fanqie_novel_info",
                    description=(
                        "获取番茄小说的详情信息，包括标题、作者、简介、分类、章节数、下载状态等。"
                        "\n参数："
                        "\n- novel_id: 番茄小说ID（必需）"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "novel_id": {
                                "type": "string",
                                "description": "番茄小说ID（必需）"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="get_fanqie_novel_chapters_outline",
                    description=(
                        "获取番茄小说的章节大纲（目录），包含所有章节的序号和标题，用于了解小说结构。"
                        "\n参数："
                        "\n- novel_id: 番茄小说ID（必需）"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "novel_id": {
                                "type": "string",
                                "description": "番茄小说ID（必需）"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="read_fanqie_chapters",
                    description=(
                        "读取番茄小说的章节内容（按章节序号范围）。支持单章或批量读取。"
                        "\n⚠️ 注意：只能读取已下载的小说，不会触发下载。如果小说未下载，将返回错误。"
                        "\n\n参数："
                        "\n- novel_id: 番茄小说ID（必需）"
                        "\n- start_index: 起始章节序号（从1开始，必需）"
                        "\n- end_index: 结束章节序号（从1开始，必需）"
                        "\n\n用法："
                        "\n- 读取单章：start_index = end_index（如 read_fanqie_chapters('123', 5, 5) 读第5章）"
                        "\n- 批量读取：start_index < end_index（如 read_fanqie_chapters('123', 1, 10) 读第1-10章）"
                    ),
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "novel_id": {
                                "type": "string",
                                "description": "番茄小说ID（必需）"
                            },
                            "start_index": {
                                "type": "integer",
                                "description": "起始章节序号，从1开始（必需）",
                                "minimum": 1
                            },
                            "end_index": {
                                "type": "integer",
                                "description": "结束章节序号，从1开始（必需）",
                                "minimum": 1
                            }
                        },
                        "required": []
                    }
                )
            ]
        
        # 2. 调用工具
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            try:
                if name == "list_fanqie_novels":
                    result = await self._list_novels(arguments)
                elif name == "search_fanqie_novels":
                    result = await self._search_novels(arguments)
                elif name == "get_fanqie_novel_info":
                    result = await self._get_novel_info(arguments)
                elif name == "get_fanqie_novel_chapters_outline":
                    result = await self._get_novel_outline(arguments)
                elif name == "read_fanqie_chapters":
                    result = await self._read_chapters(arguments)
                else:
                    result = format_error(f"未知工具: {name}")
                
                return [TextContent(type="text", text=result)]
            
            except (RuntimeError, ValueError, KeyError) as e:
                error_msg = format_error(f"工具执行失败: {str(e)}")
                return [TextContent(type="text", text=error_msg)]
    
    # ==================== 工具实现 ====================
    
    async def _list_novels(self, args: Dict) -> str:
        """列出所有已就绪的小说"""
        page = args.get("page", 1)
        per_page = args.get("per_page", 20)
        search_query = args.get("search", "")
        sort_field = args.get("sort", "last_crawled_at")
        order = args.get("order", "desc")
        
        # 构建请求参数
        params = {
            "page": page,
            "per_page": per_page,
            "sort": sort_field,
            "order": order
        }
        
        if search_query:
            params["search"] = search_query
        
        # 调用 Flask API
        novels_data = self.client.get("/api/novels", params=params)
        
        if "error" in novels_data:
            return format_error(novels_data["error"])
        
        # 只保留 is_ready=True 的小说
        all_novels = novels_data.get("novels", [])
        ready_novels = [novel for novel in all_novels if novel.get("is_ready", False)]
        
        # 构建返回数据
        result = {
            "novels": ready_novels,
            "total_ready": len(ready_novels),
            "total_all": len(all_novels),
            "page": novels_data.get("page", page),
            "pages": novels_data.get("pages", 1),
            "per_page": novels_data.get("per_page", per_page),
            "filters": {
                "search": search_query,
                "sort": sort_field,
                "order": order
            },
            "note": "只显示已就绪（可阅读）的小说。就绪条件：总章节数>100 或 已下载章节数>总章节数/3"
        }
        
        return format_success(result)
    
    async def _search_novels(self, args: Dict) -> str:
        """搜索小说（增强版：包含下载状态）"""
        query = args.get("query")
        offset = args.get("offset", 0)
        
        if not query:
            return format_error(
                "缺少必需参数 'query'。\n"
                "用法：search_fanqie_novels(query='关键词', offset=0)\n"
                "示例：search_fanqie_novels(query='修仙')"
            )
        
        # 1. 调用搜索API
        params = {"query": query}
        if offset > 0:
            params["offset"] = offset
        
        search_data = self.client.get("/api/search", params=params)
        
        if "error" in search_data:
            return format_error(search_data["error"])
        
        # 2. 获取所有任务状态
        tasks_data = self.client.get("/api/tasks/list")
        tasks = tasks_data.get("tasks", []) if "error" not in tasks_data else []
        
        # 3. 为每个搜索结果添加下载状态信息
        results = search_data.get("results", [])
        for result in results:
            novel_id = result.get("id")
            if not novel_id:
                continue
            
            # 获取该小说的详细信息（包含下载章节数）
            novel_info = self.client.get(f"/api/novels/{novel_id}")
            
            if "error" not in novel_info:
                # 添加下载状态（确保数值字段不会是None）
                chapters_in_db = novel_info.get("chapters_in_db") or 0
                total_chapters = novel_info.get("total_chapters_source") or 0
                
                result["download_status"] = {
                    "is_downloaded": chapters_in_db > 0,
                    "chapters_downloaded": chapters_in_db,
                    "total_chapters": total_chapters,
                    "last_crawled_at": novel_info.get("last_crawled_at"),
                }
                
                # 查找该小说的最新任务状态
                novel_tasks = [t for t in tasks if str(t.get("novel_id")) == str(novel_id)]
                if novel_tasks:
                    # 按创建时间排序，取最新的
                    latest_task = max(novel_tasks, key=lambda t: t.get("created_at") or "")
                    result["download_status"]["task"] = {
                        "status": latest_task.get("status"),
                        "progress": latest_task.get("progress") or 0,
                        "message": latest_task.get("message"),
                        "updated_at": latest_task.get("updated_at"),
                    }
            else:
                # 小说不在数据库中，未下载
                result["download_status"] = {
                    "is_downloaded": False,
                    "chapters_downloaded": 0,
                    "total_chapters": 0,
                    "last_crawled_at": None,
                }
        
        return format_success(search_data)
    
    async def _get_novel_info(self, args: Dict) -> str:
        """获取小说详情（增强版：包含详细下载状态）"""
        novel_id = args.get("novel_id")
        
        if not novel_id:
            return format_error(
                "缺少必需参数 'novel_id'。\n"
                "用法：get_fanqie_novel_info(novel_id='小说ID')\n"
                "示例：get_fanqie_novel_info(novel_id='7208454824847739938')\n"
                "提示：可以先使用 list_fanqie_novels 或 search_fanqie_novels 获取小说ID"
            )
        
        # 1. 获取小说基本信息
        novel_data = self.client.get(f"/api/novels/{novel_id}")
        
        if "error" in novel_data:
            # 小说不存在（404）- 提供友好的错误提示
            error_msg = novel_data["error"]
            if "404" in error_msg or "not found" in error_msg.lower():
                return format_error(
                    f"小说 {novel_id} 尚未下载到本地数据库。"
                    f"\n提示：MCP 不支持下载功能，请使用 Web 界面或 API 下载小说。"
                )
            return format_error(error_msg)
        
        # 2. 获取任务状态
        tasks_data = self.client.get("/api/tasks/list")
        tasks = tasks_data.get("tasks", []) if "error" not in tasks_data else []
        
        # 查找该小说的所有任务
        novel_tasks = [t for t in tasks if str(t.get("novel_id")) == str(novel_id)]
        
        # 3. 构建增强的下载状态信息（确保数值字段不会是None）
        chapters_in_db = novel_data.get("chapters_in_db") or 0
        total_chapters = novel_data.get("total_chapters_source") or 0
        
        download_status = {
            "is_downloaded": chapters_in_db > 0,
            "chapters_downloaded": chapters_in_db,
            "total_chapters": total_chapters,
            "download_progress": round((chapters_in_db / total_chapters * 100) if total_chapters > 0 else 0, 2),
            "is_complete": chapters_in_db >= total_chapters if total_chapters > 0 else False,
            "last_crawled_at": novel_data.get("last_crawled_at"),
        }
        
        # 4. 添加任务历史
        if novel_tasks:
            # 按创建时间排序
            novel_tasks.sort(key=lambda t: t.get("created_at") or "", reverse=True)
            
            # 最新任务
            latest_task = novel_tasks[0]
            download_status["current_task"] = {
                "id": latest_task.get("id"),
                "status": latest_task.get("status"),
                "progress": latest_task.get("progress") or 0,
                "message": latest_task.get("message"),
                "created_at": latest_task.get("created_at"),
                "updated_at": latest_task.get("updated_at"),
            }
            
            # 是否有活跃任务
            active_statuses = ["PENDING", "DOWNLOADING", "PROCESSING"]
            download_status["is_downloading"] = latest_task.get("status") in active_statuses
            
            # 历史任务统计
            download_status["task_history"] = {
                "total_tasks": len(novel_tasks),
                "completed_tasks": len([t for t in novel_tasks if t.get("status") == "COMPLETED"]),
                "failed_tasks": len([t for t in novel_tasks if t.get("status") in ["FAILED", "TERMINATED"]]),
            }
        else:
            download_status["current_task"] = None
            download_status["is_downloading"] = False
            download_status["task_history"] = {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
            }
        
        # 5. 添加可读性提示
        if download_status["is_downloading"]:
            download_status["user_message"] = "小说正在下载中，请稍候..."
        elif download_status["is_complete"]:
            download_status["user_message"] = f"小说已完整下载（{chapters_in_db}章），可以直接阅读"
        elif download_status["is_downloaded"]:
            download_status["user_message"] = f"小说部分下载（{chapters_in_db}/{total_chapters}章）"
        else:
            download_status["user_message"] = "小说未下载，MCP 不支持下载功能，请使用 Web 界面或 API 下载"
        
        # 6. 将下载状态添加到返回数据
        novel_data["download_status"] = download_status
        
        return format_success(novel_data)
    
    async def _get_novel_outline(self, args: Dict) -> str:
        """获取小说章节大纲"""
        novel_id = args.get("novel_id")
        
        if not novel_id:
            return format_error(
                "缺少必需参数 'novel_id'。\n"
                "用法：get_fanqie_novel_chapters_outline(novel_id='小说ID')\n"
                "示例：get_fanqie_novel_chapters_outline(novel_id='7208454824847739938')\n"
                "提示：可以先使用 list_fanqie_novels 或 search_fanqie_novels 获取小说ID"
            )
        
        try:
            # 获取所有章节
            chapters = get_all_chapters(self.client, novel_id)
            
            # 只返回序号和标题（大纲）
            outline = [
                {
                    "index": ch.get("index"),
                    "title": ch.get("title")
                }
                for ch in chapters
            ]
            
            # 按序号排序
            outline.sort(key=lambda x: x["index"])
            
            return format_success({
                "novel_id": novel_id,
                "total_chapters": len(outline),
                "chapters": outline
            })
        
        except RuntimeError as e:
            return format_error(str(e))
    
    async def _read_chapters(self, args: Dict) -> str:
        """读取章节内容（仅读取已下载的小说，不触发下载）"""
        novel_id = args.get("novel_id")
        start_index = args.get("start_index")
        end_index = args.get("end_index")
        
        # 参数验证
        if not novel_id:
            return format_error(
                "缺少必需参数 'novel_id'。\n"
                "用法：read_fanqie_chapters(novel_id='小说ID', start_index=起始章节, end_index=结束章节)\n"
                "示例：read_fanqie_chapters(novel_id='7208454824847739938', start_index=1, end_index=10)\n"
                "提示：可以先使用 list_fanqie_novels 或 search_fanqie_novels 获取小说ID"
            )
        if start_index is None:
            return format_error(
                "缺少必需参数 'start_index'（起始章节序号）。\n"
                "用法：read_fanqie_chapters(novel_id='小说ID', start_index=起始章节, end_index=结束章节)\n"
                "示例：read_fanqie_chapters(novel_id='7208454824847739938', start_index=1, end_index=10)\n"
                "说明：章节序号从1开始，读取单章时 start_index = end_index"
            )
        if end_index is None:
            return format_error(
                "缺少必需参数 'end_index'（结束章节序号）。\n"
                "用法：read_fanqie_chapters(novel_id='小说ID', start_index=起始章节, end_index=结束章节)\n"
                "示例：read_fanqie_chapters(novel_id='7208454824847739938', start_index=1, end_index=10)\n"
                "说明：章节序号从1开始，读取单章时 start_index = end_index"
            )
        if start_index < 1:
            return format_error(
                f"参数 'start_index' 的值 {start_index} 无效，必须 >= 1。\n"
                "说明：章节序号从1开始计数"
            )
        if end_index < start_index:
            return format_error(
                f"参数 'end_index' ({end_index}) 不能小于 'start_index' ({start_index})。\n"
                "说明：end_index 应该 >= start_index。读取单章时设置为相同值即可"
            )
        
        try:
            # 1. 获取章节列表（映射序号→ID）
            try:
                chapters = get_all_chapters(self.client, novel_id)
            except (RuntimeError, ValueError, KeyError) as e:
                # 小说还未下载，返回错误
                return format_error(
                    f"小说 {novel_id} 尚未下载。"
                    f"\n错误详情: {str(e)}"
                    f"\n提示：MCP 不支持下载功能，请使用 Web 界面或 API 下载小说。"
                )
            
            # 2. 筛选目标章节
            target_chapters = [
                ch for ch in chapters
                if start_index <= ch.get("index", 0) <= end_index
            ]
            
            if not target_chapters:
                return format_error(
                    f"未找到章节序号 {start_index}-{end_index}，"
                    f"该小说共有 {len(chapters)} 章"
                )
            
            # 按序号排序
            target_chapters.sort(key=lambda x: x["index"])
            
            # 3. 尝试读取第一章内容（检测是否已下载）
            first_chapter = target_chapters[0]
            test_data = self.client.get(
                f"/api/novels/{novel_id}/chapters/{first_chapter['id']}"
            )
            
            if "error" in test_data:
                # 章节内容不存在
                return format_error(
                    f"小说 {novel_id} 的章节内容未下载。"
                    f"\n提示：MCP 不支持下载功能，请使用 Web 界面或 API 下载小说。"
                )
            
            # 4. 批量读取所有目标章节
            results = []
            for ch in target_chapters:
                try:
                    content_data = self.client.get(
                        f"/api/novels/{novel_id}/chapters/{ch['id']}"
                    )
                    
                    if "error" in content_data:
                        results.append({
                            "index": ch["index"],
                            "title": ch["title"],
                            "error": content_data["error"]
                        })
                    else:
                        results.append({
                            "index": ch["index"],
                            "title": ch["title"],
                            "content": content_data.get("content", "")
                        })
                except (KeyError, ValueError):
                    # 章节数据格式错误，跳过
                    continue
            
            return format_success({
                "novel_id": novel_id,
                "start_index": start_index,
                "end_index": end_index,
                "chapters": results
            })
        
        except (RuntimeError, ValueError, KeyError) as e:
            return format_error(f"读取章节失败: {str(e)}")
    
    async def run(self):
        """运行MCP服务器"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# ==================== 主函数 ====================

async def main():
    """主函数"""
    server = FanqieNovelMCPServer()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

