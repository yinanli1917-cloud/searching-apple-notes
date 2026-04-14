/**
 * Apple Notes MCP Server for Cloudflare Workers
 *
 * Compatible with Poke AI and other MCP clients
 * Uses Cloudflare Agents SDK (McpAgent)
 * Connects to local Python API for semantic search
 */

import { McpAgent } from 'agents/mcp';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { z } from 'zod';

// Cloudflare Workers 环境变量类型
interface Env {
  MCP_OBJECT: DurableObjectNamespace;
  ENVIRONMENT: string;
  LOCAL_API_URL: string;
}

// 全局变量存储 API URL（workaround for McpAgent env access）
let GLOBAL_API_URL = 'https://survival-stan-capture-photographs.trycloudflare.com';

// 笔记搜索结果类型
interface SearchResult {
  title: string;
  content: string;
  updated: string;
  score: number;
}

// API 响应类型
interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

interface StatsResponse {
  indexed_notes: number;
  model: string;
  dimensions: number;
  status: string;
}

// 创建 Apple Notes MCP Agent
export class AppleNotesMcpAgent extends McpAgent<Env> {
  server = new McpServer({
    name: 'apple-notes-search',
    version: '1.0.1',  // Bumped version to force cache clear
  });

  async init() {
    // search_notes 工具
    this.server.tool(
      'search_notes',
      'Search Apple Notes using semantic search powered by BGE-M3 AI embeddings',
      {
        query: z.string().describe('Search query (supports natural language, e.g., "funny jokes", "work notes", "recipes")'),
        limit: z.number().default(5).describe('Maximum number of results to return (default: 5, max: 20)'),
      },
      async ({ query, limit }) => {
        try {
          // 优先使用 this.env，fallback 到全局变量
          const apiUrl = this.env?.LOCAL_API_URL || GLOBAL_API_URL;

          console.log('[DEBUG] this.env?.LOCAL_API_URL:', this.env?.LOCAL_API_URL);
          console.log('[DEBUG] GLOBAL_API_URL:', GLOBAL_API_URL);
          console.log('[DEBUG] Using apiUrl:', apiUrl);

          // 调用本地搜索 API
          const response = await fetch(`${apiUrl}/search`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, limit }),
          });

          if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
          }

          const data: SearchResponse = await response.json();

          if (data.total === 0) {
            return {
              content: [
                {
                  type: 'text',
                  text: `🔍 搜索: "${query}"\n\n没有找到相关的备忘录。\n\n提示：尝试使用不同的关键词或更一般的描述。`,
                },
              ],
            };
          }

          // 格式化搜索结果
          let resultText = `🔍 搜索: "${query}"\n\n找到 ${data.total} 个相关结果：\n\n`;

          data.results.forEach((result, index) => {
            const title = result.title || '(无标题)';
            const date = result.updated.split('T')[0]; // 只显示日期
            const preview = result.content.slice(0, 200).replace(/\n+/g, ' ').trim();
            const scorePercent = (result.score * 100).toFixed(0);

            resultText += `${index + 1}. **${title}** (${scorePercent}% 匹配)\n`;
            resultText += `   📅 ${date}\n`;
            resultText += `   ${preview}${result.content.length > 200 ? '...' : ''}\n\n`;
          });

          resultText += `\n💡 提示：可以在 Mac 的备忘录应用中查看完整内容`;

          return {
            content: [
              {
                type: 'text',
                text: resultText,
              },
            ],
          };
        } catch (error) {
          console.error('Search error:', error);
          return {
            content: [
              {
                type: 'text',
                text: `❌ 搜索失败: ${error instanceof Error ? error.message : '未知错误'}\n\n可能的原因：\n- 本地 API 服务器未运行\n- 网络连接问题\n\n请确保 Python API 服务器在 http://10.0.0.189:8001 运行。`,
              },
            ],
          };
        }
      }
    );

    // get_stats 工具
    this.server.tool(
      'get_stats',
      'Get statistics about indexed Apple Notes',
      {},
      async () => {
        try {
          const apiUrl = this.env?.LOCAL_API_URL || GLOBAL_API_URL;

          const response = await fetch(`${apiUrl}/stats`);

          if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
          }

          const data: StatsResponse = await response.json();

          return {
            content: [
              {
                type: 'text',
                text: `📊 Apple Notes 统计信息\n\n✅ 已索引笔记: ${data.indexed_notes} 条\n✅ 嵌入模型: ${data.model}\n✅ 向量维度: ${data.dimensions}\n✅ 状态: ${data.status === 'ready' ? '就绪' : data.status}\n\n🎯 系统信息:\n- MCP 协议: 官方 SDK\n- 传输方式: SSE (Server-Sent Events)\n- 部署平台: Cloudflare Workers\n- 本地搜索: 局域网 API (BGE-M3)`,
              },
            ],
          };
        } catch (error) {
          console.error('Stats error:', error);
          return {
            content: [
              {
                type: 'text',
                text: `📊 Apple Notes 统计信息\n\n⚠️ 无法连接到本地 API 服务器\n\n请确保 Python API 服务器在 http://10.0.0.189:8001 运行。`,
              },
            ],
          };
        }
      }
    );
  }
}

// 健康检查端点
function healthCheck(): Response {
  return new Response(
    JSON.stringify({
      name: 'Apple Notes MCP Server',
      version: '1.0.0',
      status: 'running',
      sdk: 'Cloudflare Agents (McpAgent)',
      protocol: 'MCP (Model Context Protocol)',
      transport: 'SSE (Server-Sent Events)',
      compatible_with: ['Poke AI', 'Claude Desktop', 'MCP Clients'],
      endpoints: {
        sse: '/sse',
        mcp: '/mcp',
        health: '/health',
      },
      features: {
        semantic_search: true,
        local_api: true,
        model: 'BGE-M3',
      },
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    }
  );
}

// Cloudflare Workers 入口点
export default {
  async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // 设置全局 API URL（从环境变量）
    GLOBAL_API_URL = env.LOCAL_API_URL || 'http://10.0.0.189:8001';
    console.log('[WORKER] Setting GLOBAL_API_URL to:', GLOBAL_API_URL);

    // 健康检查端点
    if (url.pathname === '/' || url.pathname === '/health') {
      return healthCheck();
    }

    // SSE 端点（Poke AI 使用 - 旧版传输方式）
    if (url.pathname.startsWith('/sse')) {
      return AppleNotesMcpAgent.serveSSE('/sse').fetch(request, env, ctx);
    }

    // Streamable HTTP 端点（新版传输方式）
    if (url.pathname.startsWith('/mcp')) {
      return AppleNotesMcpAgent.serve('/mcp').fetch(request, env, ctx);
    }

    // 404 - 未找到
    return new Response('Not Found', { status: 404 });
  },
};
