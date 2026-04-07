---
name: skill-doctor
description: |
  Agent Skill 健康扫描器。借鉴 Routa Harness 思想，通过声明式 YAML 规则对 skill 目录进行结构、内容、链接三维健康检查，生成带评分和 Mermaid 治理图的 Markdown 报告。
---



# Skill Doctor
## 使用说明
```bash
python doctor.py <path-to-skill-directory>
```
```bash
python doctor.py --all
```
## 核心心智模型
### 模型1：声明式规则即契约
### 模型2：三维扫描面
- **结构完整性**：SKILL.md、frontmatter、references 等文件/目录是否存在
- **内容质量**：必要章节（角色扮演规则、诚实边界、心智模型）是否完整
- **链接健康**：Obsidian `[[...]]` 和 Markdown `[text](path)` 链接是否可解析
### 模型3：治理可视化
## 诚实边界
- 只检查本地文件系统，不访问网络
- `references/` 和引用规范是可选项，不会强制扣分
- 章节匹配基于正则，可能误判非常规标题写法
