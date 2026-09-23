# KitchenMate

KitchenMate 是一个个人菜谱管理练习项目。当前主版本使用 SQLite 保存菜谱，并通过 Streamlit 提供网页界面；早期的 JSON 命令行版本保留作学习记录。

## 当前功能

### Streamlit 页面（`app.py`）

- 显示菜谱的数据库 ID 和名称，展开查看食材与步骤；
- 按名称关键词搜索菜谱，搜索框为空时显示全部；
- 添加菜谱：输入名称、一个食材和多条步骤；步骤在多行输入框中每行填写一条，空白行会跳过。名称、食材名称和至少一条步骤不能为空，食材数量和单位可以留空；
- 按数据库 ID 删除菜谱，并处理空 ID、非数字 ID 和不存在的 ID；
- 按数据库 ID 修改菜谱名称，并处理空名称、空 ID、非数字 ID 和不存在的 ID。修改后会重新查询并显示菜谱列表。

删除按钮会立即删除找到的菜谱，目前没有二次确认。操作前请核对数据库 ID。

### SQLite 命令行（`sqlite_main.py`）

支持添加、查看、按名称搜索、按数据库 ID 删除，以及修改菜谱名称。命令行添加时可以输入多个食材和步骤。`db_storage.py` 为页面和命令行提供同一套 SQLite 数据操作。

## 运行方式

已在 Windows、Python 3.14.3、Streamlit 1.64.0 下运行。进入 `kitchenmate` 项目目录后，在 cmd 中执行：

```cmd
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install streamlit==1.64.0
.\.venv\Scripts\streamlit.exe run app.py
```

每台电脑只需创建一次自己的 `.venv`。已有可用的 `.venv` 时，直接运行最后一行；若环境中没有 pip，可先运行 `.\.venv\Scripts\python.exe -m ensurepip --upgrade`。启动后在终端给出的本地地址打开页面，按 `Ctrl+C` 停止。

运行 SQLite 命令行版本：

```cmd
.\.venv\Scripts\python.exe sqlite_main.py
```

## 运行测试

在项目虚拟环境中安装 pytest 并运行数据层测试：

```cmd
.\.venv\Scripts\python.exe -m pip install pytest==9.1.1
.\.venv\Scripts\python.exe -m pytest -q test_db_storage.py
```

`test_db_storage.py` 包含三条测试：添加后重新连接并读回菜谱、删除后重新连接并确认菜谱不存在、修改名称后重新连接并确认新名称已保存且食材与步骤不变。每条测试都通过 pytest 的 `tmp_path` 创建独立的 SQLite 数据库，不会修改本机的 `kitchenmate.db`。

## 数据与项目文件

一条菜谱包含 `id`、`name`、`ingredients` 和 `steps`。食材是字典列表，步骤是字符串列表；存入 SQLite 时，后两项编码为 JSON 文本，读取时再还原为 Python 列表。

```text
kitchenmate/
├── app.py          # 当前 Streamlit 页面
├── db_storage.py   # SQLite 连接、建表、查询、添加、修改和删除
├── sqlite_main.py  # SQLite 命令行入口
├── kitchenmate.db  # 本机数据，首次运行时创建，不经 Git 同步
├── db_practice.py  # 早期 SQLite CRUD 练习
├── test_db_storage.py  # 使用临时数据库验证添加、读取、删除和修改名称
├── main.py         # 历史 JSON 命令行版本
├── storage.py      # 历史 JSON 读写
├── recipes.json    # 历史 JSON 示例数据
├── README.md
└── .gitignore
```

代码通过 Git/GitHub 同步。`kitchenmate.db` 被 `.gitignore` 排除，因此两台电脑的 SQLite 菜谱数据各自独立。`recipes.json` 虽写在 `.gitignore` 中，但已被 Git 跟踪，仍会随代码仓库同步；当前主版本不读取它。

## 当前限制与下一步

- 页面添加暂时只支持一个食材；步骤可以输入多条。页面修改功能目前只支持改名，不能编辑食材和步骤；
- 页面删除没有二次确认；
- 已有三条 SQLite 数据层自动化测试；页面交互仍以手动验收为主。

下一步让用户在添加页面动态增加或删除食材输入行，再按需要补充其他编辑能力、边界测试和可靠性检查；分类、收藏等需要新增字段的功能留到数据设计明确后再做。
