# TableScope 设计文档

## 上下文

大型多系统项目中，数据库表之间外键缺失，关联关系仅靠字段名约定来推断。需要一个轻量工具来快速发现和浏览这些隐式关联。

- **数据库**: 达梦 8（部分达梦 7），多实例
- **规模**: 单库 300-1000+ 张表，按天分表持续增长
- **用户**: 个人使用

## 架构

前端 SPA (Vue3 + Ant Design Vue + AntV G6) → JSON 缓存 → Python Agent (按需启动)

- 无常驻后端，Python 是 CLI agent，跑完即退出
- 缓存即 JSON 文件，前端 Vite 直接 serve
- 日常浏览仅需 `npm run dev`
- 前端通过 Vite 插件 spawn Python 进程，WebSocket 接收实时进度

## 关联发现规则

1. 规则 A (exact_name): 两表字段名完全相同
2. 规则 B (keyword): 字段名包含目标表关键字
3. 规则 C (id_pattern): 字段名指向目标表的 ID

每条候选关联经数据重合度采样验证，低于阈值则丢弃。

## 技术栈

- 前端: Vue3 + Vite + Ant Design Vue 4 + AntV G6 5 + TypeScript
- 后端: Python 3.9.6 + dmPython + websockets
- 缓存: JSON 文件
