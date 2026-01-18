# 营销活动工作台 - 测试指南

## 完成情况 ✅

所有前端UI连接已完成，后端接口已就绪。

## 已实现的功能

### 1. 数据流
```
用户输入 → Agent分析 → 生成SegmentationProposal →
点击"应用" → 调用计算接口 → 返回SegmentationResult →
更新Dashboard显示真实数据
```

### 2. 前端组件修改

- **ChatInterface.tsx** ✅
  - 添加`pendingProposal`状态
  - 实现`handleApply()`函数调用计算接口
  - "应用"按钮显示状态（有方案时显示✓并变为primary）
  - 应用成功后显示确认消息

- **Dashboard.tsx** ✅
  - 接收`pendingProposal`和`segmentationResult` props
  - 使用真实数据更新metrics
  - Header显示营销目标

- **InsightCard.tsx** ✅
  - 接收`targetTraits`和`constraints` props
  - 动态渲染特征规则卡片
  - 根据category自动选择图标
  - 无数据时显示占位符

- **App.tsx** ✅
  - 管理`pendingProposal`和`segmentationResult`状态
  - 传递数据到子组件

### 3. 后端接口

- **POST /api/v1/segmentation/calculate** ✅
  - 接收SegmentationProposal
  - 根据特征规则筛选用户
  - 动态计算转化率、收入、ROI
  - 返回SegmentationResult

- **final_analysis_node** ✅
  - 输出结构化的segmentationProposal
  - 自动分类特征（消费门槛、品类兴趣等）

## 测试步骤

### 1. 启动应用

**后端**:
```bash
cd backend
python main.py
```

**前端**:
```bash
cd frontend
npm run dev
```

### 2. 测试完整流程

#### 步骤1: 输入需求
1. 在左侧Chat输入框输入需求，例如：
   ```
   我要提升VIP客户的转化率
   ```
2. 点击"开始分析"
3. 等待Agent分析完成

#### 步骤2: 检查结构化方案
1. 打开浏览器控制台（F12）
2. 查看是否有日志：`收到结构化方案:`
3. 检查日志中是否包含：
   - `marketing_goal`
   - `target_traits`
   - `constraints`
   - `kpi`

#### 步骤3: 应用方案
1. 查看"应用"按钮是否变为蓝色并显示"应用 ✓"
2. 点击"应用"按钮
3. 检查控制台日志：
   - `正在应用方案:`
   - `收到计算结果:`
4. 检查后端日志是否显示：
   ```
   INFO: Calculating segmentation for proposal: ...
   INFO: Segmentation calculated: ... users, CVR: ..., Revenue: ...
   ```

#### 步骤4: 验证Dashboard更新
1. 右侧Dashboard应该显示真实数据
2. 检查：
   - **营销活动工作台**标题下方显示营销目标
   - **人群圈选逻辑详解**卡片显示特征规则
   - **效果预估**显示真实的人数、转化率、收入

### 3. 多轮对话测试

1. 输入第一个需求："提升VIP客户转化率"
2. 点击"应用"
3. 输入补充信息："不要最近购买过的"
4. 再次点击"应用"
5. 验证Dashboard数据更新

### 4. 清空功能测试

1. 完成分析后
2. 点击"清空"按钮
3. 验证：
   - 消息历史清空
   - "应用"按钮变灰并显示"应用"
   - pendingProposal被清空

## 调试提示

### 如果"应用"按钮不可点击
- 检查控制台是否有"收到结构化方案"日志
- 检查后端日志是否成功生成segmentationProposal

### 如果后端没有收到请求
- 打开浏览器Network标签
- 点击"应用"按钮
- 查看是否有`POST /api/v1/segmentation/calculate`请求
- 检查请求payload是否包含完整的proposal数据

### 如果Dashboard不更新
- 检查控制台是否有"收到计算结果"日志
- 检查`onApplyProposal`回调是否被调用
- 检查App.tsx的状态是否正确更新

## 预期结果

1. **Chat界面**:
   - 分析完成后显示Agent回复
   - "应用"按钮变蓝并显示✓
   - 点击后显示成功消息

2. **Dashboard界面**:
   - Header显示营销目标
   - InsightCard显示特征规则（按category分组）
   - PredictionWidget显示真实metrics
   - 约束条件显示在红色卡片中

3. **控制台日志**:
   - 前端：收到结构化方案、正在应用方案、收到计算结果
   - 后端：Calculating segmentation、Segmentation calculated

## 已知问题和解决方案

### 问题1: segmentationProposal为null
**原因**: Agent没有成功生成结构化方案
**解决**: 检查backend/app/agent/nodes.py的final_analysis_node是否正确返回segmentation_proposal

### 问题2: 计算接口返回错误
**原因**: proposal格式不正确
**解决**: 检查frontend发送的数据格式是否符合SegmentationProposal定义

### 问题3: Dashboard不显示数据
**原因**: props传递问题
**解决**: 检查App.tsx → Dashboard的props传递链

## 成功标志

✅ Chat分析完成后，"应用"按钮变蓝
✅ 点击"应用"后，后端收到请求日志
✅ Dashboard显示真实的营销目标
✅ InsightCard显示动态生成的特征规则
✅ Metrics显示计算后的数据
✅ 多轮对话正常工作
✅ 清空功能正常工作
