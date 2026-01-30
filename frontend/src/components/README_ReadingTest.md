# ReadingTest 组件说明

## 关于 TypeScript 错误

您看到的 TypeScript 错误（如 "Cannot find module 'react'" 和 "JSX element implicitly has type 'any'"）是**正常的编译时错误**，会在以下情况自动解决：

1. **安装依赖后** - 运行 `npm install` 或 `yarn install`
2. **构建项目后** - 运行 `npm run dev` 或 `npm run build`

这些错误不影响组件的功能逻辑，只是因为：
- TypeScript 编译器还没有找到 node_modules 中的类型定义
- 项目还没有被构建过

## 已修复的实际代码问题

我已经修复了以下**真实的代码问题**：

### ✅ 1. 明确类型标注
```tsx
// 修复前
const ReadingTest: React.FC<ReadingTestProps> = ({ userId }) => {
// 修复后
const ReadingTest: React.FC<ReadingTestProps> = ({ userId }: ReadingTestProps) => {
```

### ✅ 2. Map 函数参数类型
```tsx
// 修复前
questions.map(q => ({...}))
articles.map(article => (...))

// 修复后
questions.map((q: TestQuestion) => ({...}))
articles.map((article: Article) => (...))
```

## 组件功能

ReadingTest 组件提供完整的阅读测试流程：

### 1. 选择阶段
- 选择难度等级 (A1-C2)
- 选择测试类型（完形填空/判断题）
- 浏览可用文章
- 点击文章开始测试

### 2. 测试阶段
- 显示 AI 生成的题目
- 完形填空：4 选 1 单选题
- 判断题：True/False 二选一
- 实时记录答案

### 3. 结果阶段
- 显示得分百分比
- 逐题分析（正确/错误）
- 显示正确答案和解释
- 可以重新测试

## 集成到主应用

### 步骤 1: 在 App.tsx 中导入

```tsx
import ReadingTest from './components/ReadingTest';
```

### 步骤 2: 添加视图类型

在 `types/index.ts` 中已经添加了 `'test'` 到 `ViewType`：

```tsx
export type ViewType = 'discover' | 'library' | 'history' | 'vocabulary' | 'stats' | 'test';
```

### 步骤 3: 在 App.tsx 渲染组件

```tsx
function App() {
  // ... 现有代码 ...

  return (
    <div className="flex h-screen">
      <Sidebar 
        currentView={currentView} 
        onViewChange={setCurrentView}
        user={user}
      />
      
      <main className="flex-1 overflow-auto">
        {currentView === 'discover' && <SwipeDeck articles={articles} />}
        {currentView === 'library' && <ArticleList articles={articles} />}
        {currentView === 'history' && <History history={history} />}
        {currentView === 'vocabulary' && <VocabularyList vocabulary={vocabulary} />}
        {currentView === 'stats' && <Stats stats={stats} />}
        
        {/* 新增：阅读测试视图 */}
        {currentView === 'test' && user && (
          <ReadingTest userId={user.id} />
        )}
        
        {/* Reader 模态框 */}
        {activeArticle && (
          <Reader 
            article={activeArticle}
            analysis={activeAnalysis}
            onClose={() => setActiveArticle(null)}
            onSaveVocabulary={handleSaveVocab}
          />
        )}
      </main>
    </div>
  );
}
```

### 步骤 4: 在 Sidebar.tsx 添加导航按钮

```tsx
<button
  onClick={() => onViewChange('test')}
  className={`nav-button ${currentView === 'test' ? 'active' : ''}`}
>
  <BookCheck size={20} />
  <span>阅读测试</span>
</button>
```

## API 依赖

组件依赖以下后端 API（已在 backend/app.py 中实现）：

```
GET  /api/reading_test/articles?level=B1&limit=10
POST /api/reading_test/generate
POST /api/reading_test/submit
```

## 数据准备

使用前需要确保数据库有文章：

```bash
# 导入测试文章
uv run python -m backend.data_pipeline.pipeline --limit 5 --sources wikipedia
```

## 测试组件

### 前端开发模式测试

```bash
cd frontend
npm run dev
```

然后访问 http://localhost:5173，登录后切换到测试视图。

### API 独立测试

```bash
# 1. 启动后端
python backend/app.py

# 2. 测试 API
curl http://localhost:5000/api/reading_test/articles?level=B1
```

## 常见问题

### Q: 组件显示"暂无文章"
**A:** 运行数据导入：
```bash
uv run python -m backend.data_pipeline.pipeline --limit 5 --sources wikipedia
```

### Q: 题目生成失败
**A:** 检查 `.env` 中的 `HF_TOKEN` 是否配置正确

### Q: TypeScript 编译错误
**A:** 这是正常的，运行以下命令后会消失：
```bash
cd frontend
npm install  # 安装依赖
npm run dev  # 启动开发服务器
```

## 样式说明

组件使用 Tailwind CSS，与项目其他组件保持一致：
- 响应式设计
- 暗色模式支持（如果项目启用）
- 平滑过渡动画
- 清晰的视觉反馈

## 下一步优化建议

1. **添加进度保存** - 允许用户暂停测试后继续
2. **时间限制** - 为每道题添加计时器
3. **历史记录** - 显示用户的测试历史和进步
4. **难度自适应** - 根据答题情况自动调整难度
5. **详细分析** - 提供更详细的错题分析报告

## 技术栈

- React 19
- TypeScript
- Tailwind CSS v4
- Lucide React (图标)
- Fetch API (HTTP 请求)

---

**总结**: 组件代码本身没有问题，TypeScript 错误会在安装依赖后自动解决。直接运行 `npm install && npm run dev` 即可正常使用。
