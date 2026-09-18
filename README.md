# KitchenMate

KitchenMate 是一个用于学习 Python 应用开发的个人菜谱管理命令行程序。

当前项目重点练习：需求拆解、函数设计、JSON 持久化、异常处理、模块划分和 Git 版本管理。

## 当前功能

- 添加菜谱；
- 查看菜谱名称列表；
- 删除菜谱；
- 按菜谱名称关键词搜索；
- 修改菜谱名称；
- 使用 JSON 保存和读取菜谱数据；
- 处理空输入、无效编号和非数字菜单输入。

## 菜单

```text
1. 添加菜谱
2. 查看菜谱
3. 删除菜谱
4. 搜索菜谱
5. 修改菜谱名称
0. 退出
```

搜索支持按菜谱名称进行不区分大小写的部分匹配。例如，搜索“排骨”可以匹配“糖醋排骨”。搜索结果会显示连续编号和完整菜谱字典。

## 项目结构

```text
kitchenmate/
├── main.py       # 菜单、用户交互和菜谱业务功能
├── storage.py    # recipes.json 的读取和保存
├── recipes.json  # 当前菜谱数据
├── README.md     # 项目说明
└── .gitignore    # 忽略本地环境和 Python 缓存
```

## 菜谱数据结构

当前每个菜谱使用一个字典表示，多个菜谱使用列表保存：

```json
{
  "name": "糖醋排骨",
  "ingredients": [
    {
      "name": "排骨",
      "amount": "500",
      "unit": "g"
    }
  ],
  "steps": [
    "排骨焯水",
    "加热炖煮"
  ]
}
```

## 运行方式

项目目前只使用 Python 标准库，不需要额外安装第三方依赖。

在项目目录中运行：

```cmd
.venv\Scripts\activate.bat
python main.py
```

如果使用 PowerShell，可以运行：

```powershell
.\.venv\Scripts\Activate.ps1
python main.py
```

## 当前限制

- 修改功能目前只修改菜谱名称，尚未修改食材和步骤；
- 搜索结果目前直接显示原始菜谱字典，尚未格式化为更适合阅读的详情；
- 数据暂时保存在 JSON 文件中，尚未迁移到 SQLite；
- 尚未编写 pytest 自动化测试；
- 尚未制作图形界面、日志和配置系统。

## 下一步计划

在 JSON 版本稳定后，学习使用 Python 自带的 `sqlite3`，将菜谱数据迁移到 SQLite 数据库，并练习数据库 CRUD 操作。
