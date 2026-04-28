---
name: daily-github-trending-report
description: 每天上午10点抓取 GitHub 昨日最热门 Top 10 项目，通过 WebSearch 获取项目信息并生成深度总结报告
---

## 任务目标

生成 GitHub 昨日最热门 Top 10 项目的深度中文日报。

## 数据源

数据来自自建爬虫仓库 `dongminchris-dot/github-trending-data`，每日自动抓取 GitHub Trending 原始数据，存储在 `data/{日期}.json`。

## 执行步骤

### 第一步：获取昨天的日期

使用 bash 命令：`date -d "yesterday" "+%Y-%m-%d"`

### 第二步：获取昨日 Trending 原始数据

使用 WebSearch 搜索：`site:github.com dongminchris-dot/github-trending-data data/{昨天日期}`

目标是从搜索结果中找到 `data/{日期}.json` 文件的内容。该 JSON 结构为：
```json
{
  "date": "2026-04-27",
  "repositories": [
    {
      "owner": "...",
      "name": "...",
      "description": "...",
      "language": "...",
      "stars": 12345,
      "stars_today": 567,
      "forks": 890
    }
  ]
}
```

从结果中提取完整的 repositories 列表（通常 25 个），取 Top 10（按 stars_today 降序）。

如果搜索不到 JSON 内容（搜索引擎可能尚未索引），尝试搜索更宽泛的关键词：`dongminchris-dot/github-trending-data trending {昨天日期}`。如果仍然搜不到，使用 WebSearch 搜索 `github trending repositories {昨天日期}` 作为兜底方案。

### 第三步：获取每个项目的 README 内容

对 Top 10 中的每个项目，使用 WebSearch 搜索：
- `{owner}/{repo} README overview features usage`
- 从搜索结果中提取项目的功能说明、使用方式、痛点等信息

⚠️ 不要使用 WebFetch/bash curl 访问 github.com 或 raw.githubusercontent.com。

### 第四步：生成结构化报告

对每个项目输出：

```
【N】【项目名】owner/repo ⭐ xxx stars（+xxx 今日新增）
【语言】xxx
【一句话】官方简介

▍痛点分析
该项目解决了哪些具体问题？目标用户是谁？现有方案有哪些不足？

▍使用场景
适合在什么情况下使用？列举 2-3 个典型场景。

▍场景明确度评估
明确 / 较明确 / 模糊 —— 说明理由

▍技术亮点（可选）
如有独特技术实现或架构思路，简要说明。
```

### 第五步：汇总输出

```
📅 GitHub 昨日热门项目日报 —— {昨天日期}
════════════════════════════════

🔥 Top 10 最热门项目总结

[按排名逐一列出 10 个项目的结构化总结]

════════════════════════════════
📊 今日观察
- 热门语言分布：xxx
- 主要技术方向：xxx
- 值得重点关注的项目：xxx（理由）
```

## 注意事项

- 报告语言：中文
- 所有内容直接输出到对话中（不需要创建文件）
- 昨天日期通过 bash 获取
