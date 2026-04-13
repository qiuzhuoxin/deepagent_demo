---
name: validate-sql
description: 数据库执行报错时使用
---

# validate-sql
你需要确认是否使用了不存在的字段，或者错误的语法(不符合达梦数据库的语法)

## 工作流程
1. 结合"错误信息"和"错误的SQL"，判断错误点
2. 结合"表结构信息（DDL）"，对错误点进行修改或删除，确保每个字段都用在了正确的DDL上
3. 生成 SQL，并在生成后检查：所有字段是否都在 DDL 中存在？表名是否正确？

**当需要验证或修正 SQL 时，按以下步骤执行：**

### 步骤 1: 获取相关表结构
首先，调用以下工具获取 SQL 中涉及表的 DDL 信息：

```
调用工具: _get_ddl_table_info(ddl_names)
输入: SQL中涉及的所有表名，逗号分隔
示例: ["DB_QDK.GM_RD_QUESTION,DB_QDK.GM_RD_QUESTION_MEASURE"]
```

### 步骤 2: 根据数据库执行失败的错误信息，进行字段-表对应关系校验【最高优先级】
这是最容易出错的点！必须确保每个字段都用在了正确的表上！

### 步骤 3: 语法规范校验

#### 🚫 严禁使用双引号包裹字符串值 (致命错误防范)
- **铁律**：所有字符串值、字符常量、日期字符串**必须**使用**单引号 `'`** 包裹
- **禁止**：绝对**禁止**使用双引号 `"` 来包裹字符串值
- ❌ 错误：`WHERE name = "张三"` (达梦会将其解析为列名)
- ✅ 正确：`WHERE name = '张三'`
- **双引号的唯一用途**：仅当表名或字段名包含特殊字符、小写字母或关键字时，才用双引号包裹**标识符**

#### 空字符串与 NULL 的处理
- 达梦默认模式下，空字符串 `''` **不等于** `NULL`
- 判断空值请用 `IS NULL` / `IS NOT NULL`
- 判断空字符串请用 `= ''` 或 `<> ''`

#### 分页与自增
- **分页**：优先使用 `OFFSET ... FETCH NEXT ... ROWS ONLY`
- **自增主键**：建表时使用 `IDENTITY(1,1)`，禁止使用 `AUTO_INCREMENT`

#### 函数与操作符
- **字符串连接**：使用 `||` 或 `CONCAT()`
- **当前时间**：使用 `SYSDATE` 或 `GETDATE()`
- **空值替换**：优先使用 `COALESCE()`，也可用 `NVL()`
- **日期格式化**：`TO_CHAR()` / `TO_DATE()`，格式如 `'YYYY-MM-DD'`

#### 日期查询特别规则
- 当用户询问"某一天"的数据时，严禁使用 = 直接比较 TO_DATE
- 必须生成范围查询：`字段 >= TO_DATE('当天', 'YYYY-MM-DD') AND 字段 < TO_DATE('次日', 'YYYY-MM-DD')`

## Few-Shot Examples

**示例 1: 字符串值修正**
用户输入：查询名字叫 "广东电网" 且删除标记为 "2" 的记录数
❌ 错误输出 (绝对禁止):
```sql
SELECT COUNT(*) FROM DB_WTZG.GM_RD_QUESTION WHERE SUPERVISE_OBJ_NAME = "广东电网" AND DEL_FLAG = "2";
```
✅ 正确输出:
```sql
SELECT COUNT(*) FROM DB_WTZG.GM_RD_QUESTION WHERE SUPERVISE_OBJ_NAME = '广东电网' AND DEL_FLAG = '2';
```

**示例 2: 字段表对应关系校验**
用户输入：查询问题的整改措施和整改状态
❌ 错误输出:
```sql
SELECT q.QUESTION_ID, m.CURRENT_CORRECT_TYPE
FROM GM_RD_QUESTION q
JOIN GM_RD_QUESTION_MEASURE m ON m.QUESTION_ID = q.ID
-- 错误：CURRENT_CORRECT_TYPE 属于 GM_RD_QUESTION，不属于 GM_RD_QUESTION_MEASURE
```
✅ 正确输出:
```sql
SELECT q.QUESTION_ID, q.CURRENT_CORRECT_TYPE
FROM GM_RD_QUESTION q
JOIN GM_RD_QUESTION_MEASURE m ON m.QUESTION_ID = q.ID
```

**示例 3: 日期范围查询**
用户输入：查询 2026年3月31日 创建的问题
❌ 错误输出:
```sql
SELECT * FROM GM_RD_QUESTION WHERE CREATE_TIME = TO_DATE('2026-03-31', 'YYYY-MM-DD')
```
✅ 正确输出:
```sql
SELECT * FROM GM_RD_QUESTION
WHERE CREATE_TIME >= TO_DATE('2026-03-31', 'YYYY-MM-DD')
AND CREATE_TIME < TO_DATE('2026-04-01', 'YYYY-MM-DD')
```

