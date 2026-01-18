# JSON 导入错误修复

## 问题描述

在添加 LLM 调用日志时，出现以下错误：

```
ERROR - Error in intent_recognition: cannot access local variable 'json' where it is not associated with a value
```

## 根本原因

在代码中存在局部的 `import json` 语句，导致作用域冲突：

### backend/app/agent/nodes.py

```python
if previous_intent:
    import json  # ❌ 局部导入
    previous_intent_json = json.dumps(previous_intent, ...)
```

问题：
- 局部 `import json` 只在 `if` 块内执行
- 后续代码可能在 `if` 块外使用 `json`，导致访问错误

### backend/app/core/session.py

```python
# ❌ 文件顶部缺少 json 导入
logger.info(json.dumps(latest_intent, ...))  # 报错：json 未定义
```

## 修复方案

### 1. backend/app/agent/nodes.py (Line 45)

**修复前**:
```python
if previous_intent:
    import json  # ❌ 局部导入
    previous_intent_json = json.dumps(previous_intent, ensure_ascii=False, indent=2)
```

**修复后**:
```python
if previous_intent:
    # 使用文件顶部的全局导入 ✅
    previous_intent_json = json.dumps(previous_intent, ensure_ascii=False, indent=2)
```

### 2. backend/app/core/session.py (Line 2-3, 209)

**修复前**:
```python
# 文件顶部
import uuid
import logging  # ❌ 缺少 json 导入
from datetime import datetime

# ...

# Line 209
import json  # ❌ 局部导入
logger.info(json.dumps(latest_intent, ensure_ascii=False, indent=2))
```

**修复后**:
```python
# 文件顶部
import uuid
import json  # ✅ 添加全局导入
import logging
from datetime import datetime

# ...

# Line 209
# 使用文件顶部的全局导入 ✅
logger.info(json.dumps(latest_intent, ensure_ascii=False, indent=2))
```

## 修复的文件

1. **backend/app/agent/nodes.py** (Line 45)
   - 删除了局部的 `import json`
   - 使用文件顶部的全局导入（Line 2）

2. **backend/app/core/session.py** (Line 3, 209)
   - 在文件顶部添加了 `import json`
   - 删除了局部的 `import json`

## 测试验证

重启后端后，错误应该消失：

```bash
cd backend
# 停止当前运行 (Ctrl+C)
python main.py
```

测试对话：
```
我想为春季新款手袋策划营销活动，2000人以内，提升转化率
```

**应该看到**:
```
✅ Intent recognition 成功完成
✅ 不再有 "cannot access local variable 'json'" 错误
```

## 最佳实践

### ✅ 正确做法

```python
# 文件顶部导入所有需要的模块
import json
import logging

def my_function():
    # 直接使用全局导入的模块
    data = json.dumps({"key": "value"})
```

### ❌ 错误做法

```python
# 文件顶部
import logging

def my_function():
    # ❌ 避免局部导入标准库
    import json
    data = json.dumps({"key": "value"})
```

**原因**:
1. 局部导入会创建局部变量，可能导致作用域问题
2. 标准库模块应该在文件顶部导入，符合 PEP 8 规范
3. 全局导入更高效，避免重复导入

## 成功标志

修复后，后端日志应该正常显示：

```
================================================================================
🤖 LLM CALL - Intent Recognition Node
================================================================================
Multi-turn mode: False
--------------------------------------------------------------------------------
📝 PROMPT TO LLM:
...
--------------------------------------------------------------------------------
📥 LLM RESPONSE:
{
  "business_goal": "提升春季新款手袋上市的下单转化率",
  ...
}
================================================================================
✅ Intent recognition 成功完成
```

不应该看到：
```
❌ ERROR - Error in intent_recognition: cannot access local variable 'json'
```
