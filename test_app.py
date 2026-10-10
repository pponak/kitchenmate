### 页面测试 ###
###############
from streamlit.testing.v1 import AppTest
import db_storage
# 测试：添加食材行，保留原输入内容，且不存入测试数据库中
def test_add_ingredient_row_keeps_input(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_db.db"
    ## monkeypatch.setattr(模块, "变量名", 新值)
    ## 将db_storage模块中的DB_FILE变量暂时替换为test_db_path
    monkeypatch.setattr(db_storage, "DB_FILE", test_db_path)
    ## 指定要模拟的 Streamlit 页面，此时还没有执行页面代码
    at = AppTest.from_file("app.py")
    ## 运行页面一次
    at.run()
    ## 确认页面运行时没有出现异常
    assert not at.exception
    ## 在第一个食材名称输入框中输入“鸡蛋”
    at.text_input(key="ingredient_name_0").input("鸡蛋")
    ## 确认按钮的标签是“添加食材”
    assert at.button[2].label == "添加食材"
    ## 点击“添加食材”按钮，并运行页面
    at.button[2].click().run()
    assert not at.exception
    ## 确认第一输入框保留内容，第二输入框已刷新
    assert at.text_input(key="ingredient_name_0").value == "鸡蛋"
    assert at.text_input(key="ingredient_name_1").label == "食材名称"
    ## 确认测试数据库中无新增菜谱
    connection = db_storage.connect_db()
    recipes = db_storage.get_all_recipes(connection)
    connection.close()
    assert recipes == []
    
# 测试：删除指定行，保留其他行的输入
def test_remove_ingredient_row_keeps_other_input(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_db.db"
    
    monkeypatch.setattr(db_storage, "DB_FILE", test_db_path)
    at = AppTest.from_file("app.py")
    
    at.run()
    
    assert not at.exception
    
    at.text_input(key="ingredient_name_0").input("鸡蛋")
    
    assert at.button[2].label == "添加食材"
    at.button[2].click().run()
    
    at.text_input(key="ingredient_name_1").input("番茄")
    
    assert at.button(key="delete_ingredient_1").label == "删除食材"
    at.button(key="delete_ingredient_1").click().run()
    
    assert not at.exception
    assert at.text_input(key="ingredient_name_0").value == "鸡蛋"
    
    ## 测试第一行(番茄行)确实被删除了
    input_keys = []
    for widget in at.text_input:
        input_keys.append(widget.key)
    
    assert "ingredient_name_1" not in input_keys 
    
    ## 确认测试数据库中无新增菜谱
    connection = db_storage.connect_db()
    recipes = db_storage.get_all_recipes(connection)
    connection.close()
    assert recipes == []
    
# 测试：菜谱正常保存到数据库
def test_save_recipe_to_db(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_db.db"
    monkeypatch.setattr(db_storage, "DB_FILE", test_db_path)
    
    at = AppTest.from_file("app.py")
    at.run()
    
    assert not at.exception
    
    at.text_input[0].input("番茄炒蛋")
    
    at.text_input(key="ingredient_name_0").input("鸡蛋")
    at.text_input(key="ingredient_amount_0").input("2")
    at.text_input(key="ingredient_unit_0").input("个")
    
    assert at.button[2].label == "添加食材"
    at.button[2].click().run()
    assert not at.exception
    
    at.text_input(key="ingredient_name_1").input("番茄")
    at.text_input(key="ingredient_amount_1").input("1")
    at.text_input(key="ingredient_unit_1").input("个")
    at.text_area[0].input("先炒鸡蛋，再炒番茄")
    
    assert at.button[2].label == "提交"
    at.button[2].click().run()
    assert not at.exception
    
    ## 查询数据库中有菜谱
    connection = db_storage.connect_db()
    recipes = db_storage.get_all_recipes(connection)
    connection.close()
    assert len(recipes) == 1
    assert recipes[0]["name"] == "番茄炒蛋"
    assert recipes[0]["ingredients"] == [        
        {"name": "鸡蛋", "amount": "2", "unit": "个"},
        {"name": "番茄", "amount": "1", "unit": "个"}
    ]
    assert recipes[0]["steps"] == ["先炒鸡蛋，再炒番茄"]
    
# 测试：半填行缺名称时拒绝保存
def test_submit_with_missing_ingredient_name_is_rejected(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_db.db"
    monkeypatch.setattr(db_storage, "DB_FILE", test_db_path)
    
    at = AppTest.from_file("app.py")
    at.run()
    
    assert not at.exception
    
    at.text_input[0].input("番茄炒蛋")
    at.text_input(key="ingredient_name_0").input("鸡蛋")
    at.text_input(key="ingredient_amount_0").input("2")
    at.text_input(key="ingredient_unit_0").input("个")
    
    assert at.button[2].label == "添加食材"
    at.button[2].click().run()
    assert not at.exception
    
    at.text_input(key="ingredient_name_1").input("")
    at.text_input(key="ingredient_amount_1").input("1")
    
    at.text_area[0].input("先炒鸡蛋，再炒番茄")
    
    assert at.button[2].label == "提交"
    at.button[2].click().run()
    assert not at.exception
    
    ## 查询测试数据库中没有菜谱
    connection = db_storage.connect_db()
    recipes = db_storage.get_all_recipes(connection)
    connection.close()
    assert recipes == []
    
    ## 确认页面有错误提示
    messages = []
    for element in at.markdown:
        messages.append(element.value)
    assert "请补全食材名称！" in messages
    
# 测试：分类筛选和名称搜索同时生效
def test_category_and_name_filters_work_together(tmp_path, monkeypatch):
    test_db_path = tmp_path / "test_db.db"
    monkeypatch.setattr(db_storage, "DB_FILE", test_db_path)
    ## 在测试数据库中插入三条菜谱
    connection = db_storage.connect_db()
    db_storage.create_recipes_table(connection)
    test_recipes = [
        {
        "name": "鸡蛋炒番茄",
        "category": "主菜",
        "ingredients": [
            {"name": "鸡蛋", "amount": "2", "unit": "个"},
            {"name": "番茄", "amount": "1", "unit": "个"},
        ],
        "steps": ["炒熟鸡蛋和番茄"],
        },
        {
        "name": "鸡蛋汤",
        "category": "汤羹",
        "ingredients": [
            {"name": "鸡蛋", "amount": "1", "unit": "个"},
        ],
        "steps": ["水开后加入鸡蛋煮熟"],
        },
        {
        "name": "红烧排骨",
        "category": "主菜",
        "ingredients": [
            {"name": "排骨", "amount": "500", "unit": "克"},
        ],
        "steps": ["将排骨炖熟"],
        },
    ]

    for recipe in test_recipes:
        db_storage.add_recipe(connection, recipe)

    connection.close()
    ## 运行页面
    at = AppTest.from_file("app.py")
    at.run()
    assert not at.exception
    
    ## 选择分类“主菜”，输入搜索词“鸡蛋”
    assert at.selectbox[1].label == "筛选菜谱分类"
    at.selectbox[1].select("主菜")
    assert at.text_input[-1].label == "搜索菜谱名称"
    at.text_input[-1].input("鸡蛋")
    at.run()
    assert not at.exception
    ## 确认页面只显示“鸡蛋炒番茄”
    ## expander.label 是包含菜谱ID、名称的字符串
    ## recipe_labels 是字符串列表
    recipe_labels = []
    for expander in at.expander:
        recipe_labels.append(expander.label)
    assert len(recipe_labels) == 1
    assert "鸡蛋炒番茄" in recipe_labels[0]
    assert "鸡蛋汤" not in recipe_labels[0]
    assert "红烧排骨" not in recipe_labels[0]
    
    ## 筛选分类改为"全部"，搜索词不变
    at.selectbox[1].select("全部")
    at.run()
    assert not at.exception
    ## 确认页面只显示“鸡蛋炒番茄”和“鸡蛋汤”
    recipe_labels = []
    for expander in at.expander:
        recipe_labels.append(expander.label)
    assert len(recipe_labels) == 2
    assert "鸡蛋炒番茄" in recipe_labels[0]
    assert "鸡蛋汤" in recipe_labels[1]
    
    ## 只筛选分类，不搜索
    at.text_input[-1].input("")
    at.selectbox[1].select("主菜")
    at.run()
    assert not at.exception
    ## 确认页面只显示“鸡蛋炒番茄”和“红烧排骨”
    recipe_labels = []
    for expander in at.expander:
        recipe_labels.append(expander.label)
    assert len(recipe_labels) == 2
    assert "鸡蛋炒番茄" in recipe_labels[0]
    assert "红烧排骨" in recipe_labels[1]
    
    ## 不筛选分类，不搜索
    at.selectbox[1].select("全部")
    at.run()
    assert not at.exception
    ## 确认页面显示所有菜谱
    recipe_labels = []
    for expander in at.expander:
        recipe_labels.append(expander.label)
    assert len(recipe_labels) == 3
    assert "鸡蛋炒番茄" in recipe_labels[0]
    assert "鸡蛋汤" in recipe_labels[1]
    assert "红烧排骨" in recipe_labels[2]
    
    ## 空结果
    at.selectbox[1].select("甜点")
    at.run()
    assert not at.exception
    ## 确认页面没有菜谱
    recipe_labels = []
    for expander in at.expander:
        recipe_labels.append(expander.label)
    assert len(recipe_labels) == 0
    ## 确认页面有提示
    messages = []
    for element in at.markdown:
        messages.append(element.value)
    assert "甜点分类下没有菜谱" in messages