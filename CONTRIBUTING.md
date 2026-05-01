# 贡献指南

感谢你对 FOR-BAZI 项目的关注！本文档将帮助你了解如何参与贡献。

---

## 开发流程

### 1. Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/FOR-BAZI.git
cd FOR-BAZI
git remote add upstream https://github.com/ORIGINAL_OWNER/FOR-BAZI.git
```

### 2. 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 3. 开发

- 遵循现有代码风格
- 添加必要的注释（仅在逻辑不明显时）
- 确保 TypeScript 类型安全（`npx tsc --noEmit` 无错误）
- 确保 Python 代码通过基本测试

### 4. 提交

```bash
git add .
git commit -m "feat: add your feature description"
```

提交信息格式：
- `feat:` 新功能
- `fix:` Bug 修复
- `docs:` 文档更新
- `style:` 代码格式调整
- `refactor:` 重构
- `test:` 测试相关
- `chore:` 构建/工具相关

### 5. 推送 & PR

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

---

## 代码规范

### 前端（TypeScript/React）

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 状态管理使用 Zustand
- 样式使用 Tailwind CSS
- 组件文件使用 PascalCase
- 工具函数文件使用 kebab-case

### 后端（Python）

- 遵循 PEP 8
- 使用 type hints
- 函数/变量使用 snake_case
- 类名使用 PascalCase
- 文档字符串使用 Google 风格

### 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| React 组件 | PascalCase | `PillarCard.tsx` |
| 页面组件 | PascalCase | `ChartVisualization.tsx` |
| Hook | camelCase, `use` 前缀 | `useChatSSE.ts` |
| Store | camelCase, `use` 前缀 | `useBaziStore.ts` |
| 工具函数 | camelCase | `adaptChartResponse()` |
| Python 函数 | snake_case | `calculate_chart()` |
| Python 类 | PascalCase | `BaziChartData` |

---

## 测试

### 前端测试

```bash
cd frontend

# 类型检查
npx tsc --noEmit

# 构建验证
npm run build
```

### 后端测试

```bash
# 运行测试
python -m pytest tests/ -v

# 测试特定文件
python -m pytest tests/test_adapter.py -v
```

### 集成测试

```bash
# 启动后端
python -m uvicorn backend.main:app --reload &

# 启动前端
cd frontend && npm run dev &

# 手动测试流程
# 1. 打开 http://localhost:5173
# 2. 输入出生信息
# 3. 验证各页面功能
```

---

## 问题报告

使用 GitHub Issues 报告问题，请包含：

1. **问题描述**: 清晰描述问题
2. **复现步骤**: 详细的操作步骤
3. **期望行为**: 你期望发生什么
4. **实际行为**: 实际发生了什么
5. **环境信息**: 操作系统、浏览器、Node/Python 版本
6. **截图/日志**: 如有，附上相关截图或错误日志

---

## 功能建议

欢迎提出新功能建议！请在 Issue 中说明：

1. **功能描述**: 你想要什么功能
2. **使用场景**: 为什么需要这个功能
3. **实现建议**: 如果有想法，可以提出实现方案

---

## 许可证

贡献的代码将使用与项目相同的 MIT 许可证。
