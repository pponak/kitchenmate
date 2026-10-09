# KitchenMate

KitchenMate 是一个个人菜谱管理练习项目。当前主版本使用 SQLite 保存菜谱，并通过 Streamlit 提供网页界面；早期的 JSON 命令行版本保留作学习记录。

## 当前功能

### Streamlit 页面（`app.py`）

- 显示菜谱的数据库 ID 和名称，展开查看食材与步骤；
- 按名称关键词搜索菜谱，搜索框为空时显示全部；
- 添加菜谱：可点击“添加食材”增加输入行，也可删除任意食材行；其他行已填的内容会保留。步骤在多行输入框中每行填写一条，空白行会跳过；
- 添加时可选择一个分类：主菜、配菜、汤羹、主食、甜点、饮品、其他，默认“其他”；有效提交时分类与菜谱一起保存。查询接口已返回分类，页面详情展示和分类筛选尚未接入；
- 提交菜谱时，名称、至少一种食材和至少一条步骤不能为空。全空的食材行会跳过；若一行填了数量或单位却没填食材名称，页面会提示补全。食材数量和单位可以留空；
- 按数据库 ID 删除菜谱，并处理空 ID、非数字 ID 和不存在的 ID；
- 按数据库 ID 修改菜谱名称，并处理空名称、空 ID、非数字 ID 和不存在的 ID。修改后会重新查询并显示菜谱列表。

添加或删除食材输入行只改变当前页面的表单；点击“提交”且输入有效时才保存新菜谱。删除菜谱按钮会立即删除找到的菜谱，目前没有二次确认。操作前请核对数据库 ID。

### SQLite 命令行（`sqlite_main.py`）

支持添加、查看、按名称搜索、按数据库 ID 删除，以及修改菜谱名称。命令行添加时可以输入多个食材和步骤。`db_storage.py` 为页面和命令行提供同一套 SQLite 数据操作。

命令行目前没有分类输入，新增菜谱由保存函数使用默认分类“其他”。

## 运行方式

已在 Windows、Python 3.14.3、Streamlit 1.64.0 下运行。进入 `kitchenmate` 项目目录后，在 cmd 中执行：

```cmd
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install streamlit==1.64.0
.\.venv\Scripts\streamlit.exe run app.py
```

每台电脑只需创建一次自己的 `.venv`。已有可用的 `.venv` 时，直接运行最后一行；若环境中没有 pip，可先运行 `.\.venv\Scripts\python.exe -m ensurepip --upgrade`。启动后在终端给出的本地地址打开页面，按 `Ctrl+C` 停止。

当前 `recipes` 表需要 `id`、`name`、`ingredients`、`steps`、`category` 五列。新数据库会按此结构创建；已有四列表不会被 `CREATE TABLE IF NOT EXISTS` 自动升级。换电脑或更新旧版本时，请先备份并检查本机表结构；旧表需要保留数据地新增 `category TEXT DEFAULT '其他'` 列后再运行。项目尚未提供自动迁移，拉取 Git 代码也不会更新本机数据库，不要为升级直接删除旧数据。

运行 SQLite 命令行版本：

```cmd
.\.venv\Scripts\python.exe sqlite_main.py
```

## 运行测试

在项目虚拟环境中安装 pytest 并运行页面与数据层测试：

```cmd
.\.venv\Scripts\python.exe -m pip install pytest==9.1.1
.\.venv\Scripts\python.exe -m pytest -q test_app.py test_db_storage.py
```

`test_db_storage.py` 包含三条数据层测试：添加后重新连接并读回菜谱、删除后重新连接并确认菜谱不存在、修改名称后重新连接并确认新名称已保存且食材与步骤不变。

`test_app.py` 使用 Streamlit `AppTest` 模拟页面输入与按钮操作，包含四条回归测试：

- 添加食材行后，原输入保留、新行出现，未提交时数据库仍为空；
- 删除指定食材行后，该行输入框消失，其他行输入保留，数据库仍为空；
- 提交包含两种食材的菜谱后，数据库只有一份菜谱，名称、食材名称/数量/单位和步骤均正确；
- 已有有效食材时，另一行只填数量却缺名称，页面提示“请补全食材名称！”，整份菜谱不写入数据库。

每条测试都通过 pytest 的 `tmp_path` 创建独立的 SQLite 数据库；页面测试在运行前用 `monkeypatch` 临时替换 `db_storage.DB_FILE`，测试结束后恢复。测试不会修改本机的 `kitchenmate.db`。2026-10-09 验证结果为 `7 passed`，仅代表上述场景通过。

2026-10-09 分类改动后再次运行现有七条测试，结果为 `7 passed`。另以独立内存数据库检查三个查询接口的分类读回、缺分类时的“其他”和无匹配结果；以临时 SQLite 数据库进行一次性 AppTest 验证默认分类、选择“主菜”后提交保存及三个查询接口读回。这些分类验证尚未加入永久测试文件，真实数据库未被测试修改。

## 数据与项目文件

一条菜谱包含 `id`、`name`、`ingredients`、`steps` 和 `category`。食材是字典列表，步骤是字符串列表；存入 SQLite 时，食材和步骤编码为 JSON 文本，读取时再还原为 Python 列表。分类是普通文本，直接保存和读取，不进行 JSON 编解码；保存函数在字典缺少 `category` 时使用“其他”。

```text
kitchenmate/
├── app.py          # 当前 Streamlit 页面
├── db_storage.py   # SQLite 连接、建表、查询、添加、修改和删除
├── sqlite_main.py  # SQLite 命令行入口
├── kitchenmate.db  # 本机数据，首次运行时创建，不经 Git 同步
├── db_practice.py  # 早期 SQLite CRUD 练习
├── test_db_storage.py  # 使用临时数据库验证添加、读取、删除和修改名称
├── test_app.py     # 使用 AppTest 和临时数据库验证四个页面交互场景
├── main.py         # 历史 JSON 命令行版本
├── storage.py      # 历史 JSON 读写
├── recipes.json    # 历史 JSON 示例数据
├── README.md
└── .gitignore
```

代码通过 Git/GitHub 同步。`kitchenmate.db` 被 `.gitignore` 排除，因此两台电脑的 SQLite 菜谱数据各自独立。`recipes.json` 虽写在 `.gitignore` 中，但已被 Git 跟踪，仍会随代码仓库同步；当前主版本不读取它。

## 当前限制与下一步

- 页面添加支持多种食材和多条步骤；已保存菜谱目前只能在页面修改名称，不能编辑食材和步骤；
- 页面删除没有二次确认；
- 分类已支持选择、保存和三个查询接口读回，尚未在菜谱详情显示，也不能按分类筛选；收藏未实现；
- 已有数据库尚无自动结构迁移；从新环境按 README 安装、运行测试及启动页面的验收仍待完成；
- 已有三条 SQLite 数据层测试和四条页面交互测试；页面搜索、按 ID 删除/改名及其余边界场景尚未全部纳入自动化测试。

下一步先在菜谱详情展示已保存的分类，再明确分类筛选与名称搜索的组合规则并实现，补充针对性分类测试。继续保留新环境运行说明验收；收藏与编辑已有食材、步骤按实际需求逐步推进。
