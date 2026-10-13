### 页面测试 ###
###############
from contextlib import closing

import pytest
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
    ## 保存筛选前的测试数据
    before_recipes = db_storage.get_all_recipes(connection)
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
    messages = []
    for element in at.markdown:
        messages.append(element.value)
    assert "菜谱分类：主菜" in messages
    
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
    
    ## 分类切换为全部，搜索词设置面包
    at.selectbox[1].select("全部")
    at.text_input[-1].input("面包")
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
    assert "没有找到符合搜索条件的相关菜谱" in messages
    
    ## 确认筛选后数据库中的数据没有变化
    connection = db_storage.connect_db()
    after_recipes = db_storage.get_all_recipes(connection)
    connection.close()
    assert before_recipes == after_recipes


# 以下测试保护收藏按钮、持久化及收藏/分类/名称组合筛选。
@pytest.fixture
def favorite_page_recipes(tmp_path, monkeypatch):
    """每项用例独立建库，准备三份收藏和一份未收藏菜谱。"""
    monkeypatch.setattr(db_storage, "DB_FILE", tmp_path / "favorites.db")
    with closing(db_storage.connect_db()) as connection:
        db_storage.create_recipes_table(connection)
        for name, category, favorite in [
            ("鸡蛋炒番茄", "主菜", 1),
            ("鸡蛋汤", "汤羹", 1),
            ("红烧排骨", "主菜", 1),
            ("鸡蛋沙拉", "主菜", 0),
        ]:
            recipe_id = db_storage.add_recipe(
                connection,
                {
                    "name": name,
                    "category": category,
                    "ingredients": [
                        {"name": "示例食材", "amount": "1", "unit": "份"}
                    ],
                    "steps": ["准备食材", "完成烹饪"],
                },
            )
            if favorite:
                db_storage.update_recipe_favorite(connection, recipe_id, favorite)
    return _read_page_recipes()


def _read_page_recipes():
    """重新连接临时库，读取持久保存的完整数据，并保证关闭连接。"""
    with closing(db_storage.connect_db()) as connection:
        return db_storage.get_all_recipes(connection)


def _assert_recipe_list(at, expected_recipes):
    """检查结果数量、ID/名称、顺序以及每份菜谱对应的星星。"""
    assert not at.exception
    assert len(at.expander) == len(expected_recipes)
    for expander, recipe in zip(at.expander, expected_recipes, strict=True):
        assert f"菜谱ID：{recipe['id']}，" in expander.label
        assert recipe["name"] in expander.label

    favorite_keys = [
        button.key
        for button in at.button
        if button.key is not None and button.key.startswith("favorite_")
    ]
    assert favorite_keys == [
        f"favorite_{recipe['id']}" for recipe in expected_recipes
    ]
    for recipe in expected_recipes:
        expected_star = "★" if recipe["favorite"] == 1 else "☆"
        assert at.button(key=f"favorite_{recipe['id']}").label == expected_star


def _page_messages(at):
    return [element.value.strip() for element in at.markdown]


def test_favorite_button_round_trip_is_persistent(favorite_page_recipes):
    """点击默认空星收藏，再取消；两次都重开页面并核对完整数据。"""
    before_recipes = favorite_page_recipes
    target_recipe = before_recipes[3]
    favorite_key = f"favorite_{target_recipe['id']}"
    at = AppTest.from_file("app.py").run()
    _assert_recipe_list(at, before_recipes)
    assert at.checkbox[0].label == "只看收藏"
    assert at.checkbox[0].value is False

    at.button(key=favorite_key).click().run()
    expected_recipes = [dict(recipe) for recipe in before_recipes]
    expected_recipes[3]["favorite"] = 1
    _assert_recipe_list(at, expected_recipes)
    # 比较完整列表，确保只改变目标收藏状态，其他字段和菜谱不变。
    assert _read_page_recipes() == expected_recipes

    # 普通重运行没有新点击，不应再次切换或重复添加菜谱。
    at.run()
    _assert_recipe_list(at, expected_recipes)
    assert _read_page_recipes() == expected_recipes

    reopened = AppTest.from_file("app.py").run()
    _assert_recipe_list(reopened, expected_recipes)
    reopened.button(key=favorite_key).click().run()
    _assert_recipe_list(reopened, before_recipes)
    assert _read_page_recipes() == before_recipes

    after_cancel = AppTest.from_file("app.py").run()
    _assert_recipe_list(after_cancel, before_recipes)
    assert _read_page_recipes() == before_recipes


@pytest.mark.parametrize(
    "category, keyword, favorite_only, expected_indexes",
    [
        ("全部", "", True, [0, 1, 2]),
        ("主菜", "", True, [0, 2]),
        ("全部", "鸡蛋", True, [0, 1]),
        ("主菜", "鸡蛋", True, [0]),
        ("主菜", "鸡蛋", False, [0, 3]),
        ("全部", "鸡蛋", False, [0, 1, 3]),
        ("全部", "", False, [0, 1, 2, 3]),
    ],
    ids=[
        "favorites-only",
        "favorites-category",
        "favorites-name",
        "all-three-filters",
        "category-name-without-favorites",
        "name-without-favorites",
        "no-filters",
    ],
)
def test_favorite_filters_work_with_category_and_name(
    favorite_page_recipes, category, keyword, favorite_only, expected_indexes
):
    at = AppTest.from_file("app.py").run()
    _assert_recipe_list(at, favorite_page_recipes)
    assert at.selectbox[1].label == "筛选菜谱分类"
    assert at.text_input[-1].label == "搜索菜谱名称"
    assert at.checkbox[0].label == "只看收藏"
    at.selectbox[1].select(category)
    at.text_input[-1].input(keyword)
    at.checkbox[0].set_value(favorite_only)
    at.run()

    expected = [favorite_page_recipes[index] for index in expected_indexes]
    _assert_recipe_list(at, expected)
    if favorite_only:
        assert "符合当前搜索条件的收藏菜谱：" in _page_messages(at)
    # 纯筛选不能改变任何已保存的字段。
    assert _read_page_recipes() == favorite_page_recipes


@pytest.mark.parametrize(
    "category, keyword",
    [("全部", "面包"), ("甜点", ""), ("甜点", "面包")],
    ids=["name-no-match", "category-no-match", "both-no-match"],
)
def test_empty_favorite_filters_show_favorite_message(
    favorite_page_recipes, category, keyword
):
    at = AppTest.from_file("app.py").run()
    assert not at.exception
    at.selectbox[1].select(category)
    at.text_input[-1].input(keyword)
    at.checkbox[0].check().run()

    _assert_recipe_list(at, [])
    messages = _page_messages(at)
    assert "没有符合当前条件的收藏菜谱" in messages
    assert "没有找到符合搜索条件的相关菜谱" not in messages
    assert "甜点分类下没有菜谱" not in messages
    assert "没有菜谱" not in messages
    assert _read_page_recipes() == favorite_page_recipes


def test_no_favorites_keeps_saved_recipes_when_filter_is_cleared(
    favorite_page_recipes,
):
    """有菜谱但无人收藏时提示准确，取消勾选后恢复全部菜谱。"""
    with closing(db_storage.connect_db()) as connection:
        for recipe in favorite_page_recipes:
            db_storage.update_recipe_favorite(connection, recipe["id"], 0)
    before_recipes = _read_page_recipes()
    at = AppTest.from_file("app.py").run()
    _assert_recipe_list(at, before_recipes)
    at.checkbox[0].check().run()

    _assert_recipe_list(at, [])
    messages = _page_messages(at)
    assert "没有符合当前条件的收藏菜谱" in messages
    assert "没有菜谱" not in messages
    assert _read_page_recipes() == before_recipes

    at.checkbox[0].uncheck().run()
    _assert_recipe_list(at, before_recipes)
    assert "所有菜谱：" in _page_messages(at)
    assert _read_page_recipes() == before_recipes


def test_unfavorite_in_filtered_list_preserves_other_filters(
    favorite_page_recipes,
):
    """筛选后的第一项仍按数据库 ID 更新，取消收藏后立即移出列表。"""
    target_recipe = favorite_page_recipes[2]
    at = AppTest.from_file("app.py").run()
    assert not at.exception
    at.selectbox[1].select("主菜")
    at.text_input[-1].input("排骨")
    at.checkbox[0].check().run()
    _assert_recipe_list(at, [target_recipe])

    at.button(key=f"favorite_{target_recipe['id']}").click().run()
    _assert_recipe_list(at, [])
    assert at.checkbox[0].value is True
    assert at.selectbox[1].value == "主菜"
    assert at.text_input[-1].value == "排骨"
    assert "没有符合当前条件的收藏菜谱" in _page_messages(at)
    expected_recipes = [dict(recipe) for recipe in favorite_page_recipes]
    expected_recipes[2]["favorite"] = 0
    assert _read_page_recipes() == expected_recipes

    # 取消收藏筛选后，名称和分类条件保留，目标以空星重新出现。
    at.checkbox[0].uncheck().run()
    _assert_recipe_list(at, [expected_recipes[2]])
    assert at.selectbox[1].value == "主菜"
    assert at.text_input[-1].value == "排骨"
    assert _read_page_recipes() == expected_recipes
