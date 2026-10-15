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
    assert "**菜谱分类：主菜**" in messages
    
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

# 以下测试保护已保存菜谱的编辑、动态食材行、校验和持久保存。
@pytest.fixture
def edit_page_recipes(tmp_path, monkeypatch):
    """目标菜谱不是第一份，并已收藏，便于检查是否误改其他记录。"""
    monkeypatch.setattr(db_storage, "DB_FILE", tmp_path / "editing.db")
    recipes = [
        {
            "name": "蔬菜汤",
            "category": "汤羹",
            "ingredients": [{"name": "水", "amount": "300", "unit": "毫升"}],
            "steps": ["烧开水"],
        },
        {
            "name": "鸡蛋炒番茄",
            "category": "主菜",
            "ingredients": [
                {"name": "鸡蛋", "amount": "2", "unit": "个"},
                {"name": "番茄", "amount": "1", "unit": "个"},
            ],
            "steps": ["打散鸡蛋", "先炒鸡蛋，再炒番茄"],
        },
    ]
    with closing(db_storage.connect_db()) as connection:
        db_storage.create_recipes_table(connection)
        for recipe in recipes:
            recipe_id = db_storage.add_recipe(connection, recipe)
        db_storage.update_recipe_favorite(connection, recipe_id, 1)
    return _read_page_recipes()


def _open_recipe_editor(at, recipe_id):
    """通过页面按钮进入编辑，不直接修改应用的会话状态。"""
    assert not at.exception
    at.button(key=f"edit_{recipe_id}").click().run()
    assert not at.exception
    assert at.session_state["editing_recipe_id"] == recipe_id


def _set_edit_ingredient(at, recipe_id, row_id, ingredient):
    for field in ("name", "amount", "unit"):
        at.text_input(key=f"edit_ingredient_{field}_{recipe_id}_{row_id}").input(
            ingredient[field]
        )


def _assert_edit_ingredient(at, recipe_id, row_id, ingredient):
    for field in ("name", "amount", "unit"):
        assert at.text_input(
            key=f"edit_ingredient_{field}_{recipe_id}_{row_id}"
        ).value == ingredient[field]


def _submit_recipe_edit(at):
    save_buttons = [button for button in at.button if button.label == "保存"]
    assert len(save_buttons) == 1
    save_buttons[0].click().run()
    assert not at.exception


@pytest.mark.parametrize("target_index", [0, 1], ids=["soup", "main-dish"])
def test_edit_prefills_saved_recipe(edit_page_recipes, target_index):
    """编辑框取当前菜谱的原分类、食材和步骤，进入编辑本身不写库。"""
    target = edit_page_recipes[target_index]
    at = AppTest.from_file("app.py").run()
    assert not at.exception
    assert f"edit_steps_{target['id']}" not in [widget.key for widget in at.text_area]

    _open_recipe_editor(at, target["id"])
    category = at.selectbox(key=f"edit_category_{target['id']}")
    assert category.value == target["category"]
    assert category.options == [
        "主菜", "配菜", "汤羹", "主食", "甜点", "饮品", "其他"
    ]
    for row_id, ingredient in enumerate(target["ingredients"]):
        _assert_edit_ingredient(at, target["id"], row_id, ingredient)
    assert at.text_area(key=f"edit_steps_{target['id']}").value == "\n".join(
        target["steps"]
    )
    assert _read_page_recipes() == edit_page_recipes


def test_edit_add_ingredient_row_keeps_input(edit_page_recipes):
    """增行保留分类、食材和步骤；再次增行或点击编辑不重置草稿。"""
    target = edit_page_recipes[1]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    _open_recipe_editor(at, recipe_id)
    at.selectbox(key=f"edit_category_{recipe_id}").select("汤羹")
    at.text_input(key=f"edit_ingredient_amount_{recipe_id}_0").input("3")
    at.text_area(key=f"edit_steps_{recipe_id}").input("打散鸡蛋\n炒熟后加盐")
    at.button(key=f"add_edit_ingredient_{recipe_id}").click().run()
    assert not at.exception
    assert at.selectbox(key=f"edit_category_{recipe_id}").value == "汤羹"
    _assert_edit_ingredient(
        at, recipe_id, 0, {"name": "鸡蛋", "amount": "3", "unit": "个"}
    )
    _assert_edit_ingredient(at, recipe_id, 1, target["ingredients"][1])
    _assert_edit_ingredient(
        at, recipe_id, 2, {"name": "", "amount": "", "unit": ""}
    )
    assert at.text_area(key=f"edit_steps_{recipe_id}").value == "打散鸡蛋\n炒熟后加盐"

    new_ingredient = {"name": "盐", "amount": "1", "unit": "克"}
    _set_edit_ingredient(at, recipe_id, 2, new_ingredient)
    at.button(key=f"add_edit_ingredient_{recipe_id}").click().run()
    assert not at.exception
    _assert_edit_ingredient(at, recipe_id, 2, new_ingredient)
    _assert_edit_ingredient(
        at, recipe_id, 3, {"name": "", "amount": "", "unit": ""}
    )
    _open_recipe_editor(at, recipe_id)
    assert at.selectbox(key=f"edit_category_{recipe_id}").value == "汤羹"
    _assert_edit_ingredient(at, recipe_id, 2, new_ingredient)
    assert at.session_state["edit_ingredient_row_ids"] == [0, 1, 2, 3]
    assert at.session_state["ingredient_row_ids"] == [0]
    assert _read_page_recipes() == edit_page_recipes


def test_edit_remove_ingredient_row_keeps_other_input(edit_page_recipes):
    """删除中间行后保留其他输入，再增行使用尚未用过的 ID。"""
    target = edit_page_recipes[1]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    _open_recipe_editor(at, recipe_id)
    at.text_input(key=f"edit_ingredient_amount_{recipe_id}_0").input("3")
    at.text_area(key=f"edit_steps_{recipe_id}").input("炒熟后加盐")
    at.button(key=f"add_edit_ingredient_{recipe_id}").click().run()
    assert not at.exception
    new_ingredient = {"name": "盐", "amount": "1", "unit": "克"}
    _set_edit_ingredient(at, recipe_id, 2, new_ingredient)
    at.button(key=f"delete_edit_ingredient_{recipe_id}_1").click().run()
    assert not at.exception
    assert f"edit_ingredient_name_{recipe_id}_1" not in [
        widget.key for widget in at.text_input
    ]
    _assert_edit_ingredient(
        at, recipe_id, 0, {"name": "鸡蛋", "amount": "3", "unit": "个"}
    )
    _assert_edit_ingredient(at, recipe_id, 2, new_ingredient)
    assert at.text_area(key=f"edit_steps_{recipe_id}").value == "炒熟后加盐"

    at.button(key=f"add_edit_ingredient_{recipe_id}").click().run()
    assert not at.exception
    assert at.session_state["edit_ingredient_row_ids"] == [0, 2, 3]
    _assert_edit_ingredient(at, recipe_id, 2, new_ingredient)
    _assert_edit_ingredient(
        at, recipe_id, 3, {"name": "", "amount": "", "unit": ""}
    )
    assert _read_page_recipes() == edit_page_recipes

    _submit_recipe_edit(at)
    expected = [
        edit_page_recipes[0],
        {
            **target,
            "ingredients": [
                {"name": "鸡蛋", "amount": "3", "unit": "个"},
                new_ingredient,
            ],
            "steps": ["炒熟后加盐"],
        },
    ]
    assert _read_page_recipes() == expected
    assert at.session_state["editing_recipe_id"] is None


def test_edit_save_content_is_persistent(edit_page_recipes):
    """保存清理后的输入，刷新详情并退出编辑；筛选和其他字段保持。"""
    target = edit_page_recipes[1]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    assert not at.exception
    at.selectbox[1].select("主菜")
    search = [widget for widget in at.text_input if widget.label == "搜索菜谱名称"][0]
    search.input("鸡蛋")
    at.checkbox[0].check().run()
    _assert_recipe_list(at, [target])
    _open_recipe_editor(at, recipe_id)
    _set_edit_ingredient(
        at, recipe_id, 0, {"name": " 鸡蛋 ", "amount": " 3 ", "unit": " 个 "}
    )
    at.text_area(key=f"edit_steps_{recipe_id}").input(
        "  打散鸡蛋  \n\n  将鸡蛋与番茄炒熟  \n  "
    )
    # 新增的全空行应被忽略，不应阻止保存或成为空食材。
    at.button(key=f"add_edit_ingredient_{recipe_id}").click().run()
    assert not at.exception
    _submit_recipe_edit(at)
    expected_target = {
        **target,
        "ingredients": [
            {"name": "鸡蛋", "amount": "3", "unit": "个"},
            target["ingredients"][1],
        ],
        "steps": ["打散鸡蛋", "将鸡蛋与番茄炒熟"],
    }
    expected = [edit_page_recipes[0], expected_target]
    assert _read_page_recipes() == expected
    assert at.session_state["editing_recipe_id"] is None
    assert f"edit_steps_{recipe_id}" not in [widget.key for widget in at.text_area]
    _assert_recipe_list(at, [expected_target])
    assert at.selectbox[1].value == "主菜"
    assert at.checkbox[0].value is True
    assert [widget for widget in at.text_input if widget.label == "搜索菜谱名称"][
        0
    ].value == "鸡蛋"
    messages = _page_messages(at)
    assert "鸡蛋：3 个" in messages
    assert "**步骤2**：将鸡蛋与番茄炒熟" in messages

    at.run()
    assert not at.exception
    assert _read_page_recipes() == expected
    reopened = AppTest.from_file("app.py").run()
    _assert_recipe_list(reopened, expected)
    _open_recipe_editor(reopened, recipe_id)
    for row_id, ingredient in enumerate(expected_target["ingredients"]):
        _assert_edit_ingredient(reopened, recipe_id, row_id, ingredient)
    assert reopened.text_area(key=f"edit_steps_{recipe_id}").value == "\n".join(
        expected_target["steps"]
    )


@pytest.mark.parametrize(
    "case, expected_error",
    [
        ("amount-without-name", "请补全食材名称！"),
        ("unit-without-name", "请补全食材名称！"),
        ("all-ingredients-empty", "至少要有一个食材！"),
        ("steps-empty", "步骤不能为空！"),
        ("multiple-errors", "请补全食材名称！"),
    ],
    ids=["missing-name-amount", "missing-name-unit", "no-ingredients", "no-steps", "error-priority"],
)
def test_edit_invalid_input_is_rejected(edit_page_recipes, case, expected_error):
    """错误输入阻止包括分类在内的整份保存，保留编辑状态和草稿。"""
    recipe_id = edit_page_recipes[1]["id"]
    at = AppTest.from_file("app.py").run()
    _open_recipe_editor(at, recipe_id)
    at.selectbox(key=f"edit_category_{recipe_id}").select("汤羹")
    if case == "amount-without-name":
        changes = [(0, {"name": "   ", "amount": "2", "unit": ""})]
    elif case == "unit-without-name":
        changes = [(0, {"name": "", "amount": "", "unit": "个"})]
    elif case in ("all-ingredients-empty", "multiple-errors"):
        changes = [
            (0, {"name": "   ", "amount": "   ", "unit": "   "}),
            (1, {"name": "", "amount": "", "unit": ""}),
        ]
        if case == "multiple-errors":
            changes[0] = (0, {"name": "", "amount": "2", "unit": ""})
    else:
        changes = []
    for row_id, ingredient in changes:
        _set_edit_ingredient(at, recipe_id, row_id, ingredient)
    if case in ("steps-empty", "multiple-errors"):
        at.text_area(key=f"edit_steps_{recipe_id}").input("  \n  ")
    _submit_recipe_edit(at)
    assert [element.value for element in at.error] == [expected_error]
    assert at.session_state["editing_recipe_id"] == recipe_id
    assert at.selectbox(key=f"edit_category_{recipe_id}").value == "汤羹"
    assert f"edit_steps_{recipe_id}" in [widget.key for widget in at.text_area]
    for row_id, ingredient in changes:
        _assert_edit_ingredient(at, recipe_id, row_id, ingredient)
    assert _read_page_recipes() == edit_page_recipes


def test_edit_empty_ingredient_row_is_skipped(edit_page_recipes):
    """清空一整行后保存，只移除该食材，剩余食材重新编辑时正确预填。"""
    target = edit_page_recipes[1]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    _open_recipe_editor(at, recipe_id)
    _set_edit_ingredient(at, recipe_id, 0, {"name": " ", "amount": " ", "unit": " "})
    _submit_recipe_edit(at)
    expected_target = {**target, "ingredients": [target["ingredients"][1]]}
    assert _read_page_recipes() == [edit_page_recipes[0], expected_target]
    assert at.session_state["editing_recipe_id"] is None
    _open_recipe_editor(at, recipe_id)
    _assert_edit_ingredient(at, recipe_id, 0, target["ingredients"][1])
    assert f"edit_ingredient_name_{recipe_id}_1" not in [
        widget.key for widget in at.text_input
    ]


def test_edit_remove_all_rows_then_add_can_recover(edit_page_recipes):
    """删完所有行时拒绝保存；仍能增加新行，填好后正常保存。"""
    target = edit_page_recipes[1]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    _open_recipe_editor(at, recipe_id)
    for row_id in (0, 1):
        at.button(key=f"delete_edit_ingredient_{recipe_id}_{row_id}").click().run()
        assert not at.exception
    _submit_recipe_edit(at)
    assert [element.value for element in at.error] == ["至少要有一个食材！"]
    assert at.session_state["editing_recipe_id"] == recipe_id
    assert _read_page_recipes() == edit_page_recipes

    at.button(key=f"add_edit_ingredient_{recipe_id}").click().run()
    assert not at.exception
    assert at.session_state["edit_ingredient_row_ids"] == [2]
    _assert_edit_ingredient(
        at, recipe_id, 2, {"name": "", "amount": "", "unit": ""}
    )
    ingredient = {"name": "豆腐", "amount": "200", "unit": "克"}
    _set_edit_ingredient(at, recipe_id, 2, ingredient)
    _submit_recipe_edit(at)
    expected_target = {**target, "ingredients": [ingredient]}
    assert _read_page_recipes() == [edit_page_recipes[0], expected_target]
    assert at.session_state["editing_recipe_id"] is None
    _open_recipe_editor(at, recipe_id)
    _assert_edit_ingredient(at, recipe_id, 0, ingredient)


@pytest.mark.parametrize("invalid_draft", [False, True], ids=["valid-draft", "invalid-draft"])
def test_cancel_edit_discards_draft(edit_page_recipes, invalid_draft):
    """取消有效或无效草稿都不写库，保留筛选，再次编辑恢复已保存内容。"""
    target = edit_page_recipes[1]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    at.selectbox[1].select("主菜")
    search = [widget for widget in at.text_input if widget.label == "搜索菜谱名称"][0]
    search.input("鸡蛋")
    at.checkbox[0].check().run()
    _open_recipe_editor(at, recipe_id)
    at.selectbox(key=f"edit_category_{recipe_id}").select("汤羹")
    at.text_input(key=f"edit_ingredient_amount_{recipe_id}_0").input("99")
    at.text_area(key=f"edit_steps_{recipe_id}").input("未保存的步骤")
    at.button(key=f"add_edit_ingredient_{recipe_id}").click().run()
    assert not at.exception
    _set_edit_ingredient(at, recipe_id, 2, {"name": "盐", "amount": "1", "unit": "克"})
    at.button(key=f"delete_edit_ingredient_{recipe_id}_1").click().run()
    assert not at.exception
    if invalid_draft:
        for row_id in (0, 2):
            _set_edit_ingredient(
                at, recipe_id, row_id, {"name": "", "amount": "", "unit": ""}
            )
        at.text_area(key=f"edit_steps_{recipe_id}").input("  \n  ")
    assert _read_page_recipes() == edit_page_recipes

    cancel_buttons = [button for button in at.button if button.label == "取消编辑"]
    assert len(cancel_buttons) == 1
    cancel_buttons[0].click().run()
    assert not at.exception
    assert not at.error
    assert at.session_state["editing_recipe_id"] is None
    assert f"edit_steps_{recipe_id}" not in [widget.key for widget in at.text_area]
    assert f"edit_category_{recipe_id}" not in [widget.key for widget in at.selectbox]
    assert _read_page_recipes() == edit_page_recipes
    _assert_recipe_list(at, [target])
    assert at.selectbox[1].value == "主菜"
    assert at.checkbox[0].value is True
    assert [widget for widget in at.text_input if widget.label == "搜索菜谱名称"][
        0
    ].value == "鸡蛋"

    _open_recipe_editor(at, recipe_id)
    assert at.selectbox(key=f"edit_category_{recipe_id}").value == target["category"]
    assert at.session_state["edit_ingredient_row_ids"] == [0, 1]
    for row_id, ingredient in enumerate(target["ingredients"]):
        _assert_edit_ingredient(at, recipe_id, row_id, ingredient)
    assert f"edit_ingredient_name_{recipe_id}_2" not in [
        widget.key for widget in at.text_input
    ]
    assert at.text_area(key=f"edit_steps_{recipe_id}").value == "\n".join(target["steps"])
    assert _read_page_recipes() == edit_page_recipes


@pytest.mark.parametrize(
    "target_index, new_category",
    [(0, "主菜"), (1, "汤羹"), (1, "其他")],
    ids=["soup-to-main", "main-to-soup", "main-to-other"],
)
def test_edit_category_is_persistent(edit_page_recipes, target_index, new_category):
    """只改分类后刷新详情并退出，重开仍保留，其他字段和菜谱不变。"""
    target = edit_page_recipes[target_index]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    _open_recipe_editor(at, recipe_id)
    at.selectbox(key=f"edit_category_{recipe_id}").select(new_category)
    _submit_recipe_edit(at)
    expected_target = {**target, "category": new_category}
    expected = list(edit_page_recipes)
    expected[target_index] = expected_target
    assert _read_page_recipes() == expected
    assert at.session_state["editing_recipe_id"] is None
    assert f"edit_category_{recipe_id}" not in [widget.key for widget in at.selectbox]
    _assert_recipe_list(at, expected)
    assert f"**菜谱分类：{new_category}**" in _page_messages(at)

    at.run()
    assert not at.exception
    assert _read_page_recipes() == expected
    reopened = AppTest.from_file("app.py").run()
    _assert_recipe_list(reopened, expected)
    _open_recipe_editor(reopened, recipe_id)
    assert reopened.selectbox(key=f"edit_category_{recipe_id}").value == new_category
    for row_id, ingredient in enumerate(target["ingredients"]):
        _assert_edit_ingredient(reopened, recipe_id, row_id, ingredient)
    assert reopened.text_area(key=f"edit_steps_{recipe_id}").value == "\n".join(
        target["steps"]
    )


def test_edit_category_and_content_preserve_filters(edit_page_recipes):
    """同时改分类和内容后按新条件显示，保留名称及收藏筛选和其他记录。"""
    target = edit_page_recipes[1]
    recipe_id = target["id"]
    at = AppTest.from_file("app.py").run()
    at.selectbox[1].select("主菜")
    search = [widget for widget in at.text_input if widget.label == "搜索菜谱名称"][0]
    search.input("鸡蛋")
    at.checkbox[0].check().run()
    _open_recipe_editor(at, recipe_id)
    at.selectbox(key=f"edit_category_{recipe_id}").select("汤羹")
    ingredient = {"name": "鸡蛋", "amount": "3", "unit": "个"}
    _set_edit_ingredient(at, recipe_id, 0, ingredient)
    at.text_area(key=f"edit_steps_{recipe_id}").input("打散鸡蛋\n炒熟后加盐")
    _submit_recipe_edit(at)
    expected_target = {
        **target,
        "category": "汤羹",
        "ingredients": [ingredient, target["ingredients"][1]],
        "steps": ["打散鸡蛋", "炒熟后加盐"],
    }
    expected = [edit_page_recipes[0], expected_target]
    assert _read_page_recipes() == expected
    assert at.session_state["editing_recipe_id"] is None
    _assert_recipe_list(at, [])
    assert "没有符合当前条件的收藏菜谱" in _page_messages(at)
    assert at.selectbox[1].value == "主菜"
    assert at.checkbox[0].value is True
    assert [widget for widget in at.text_input if widget.label == "搜索菜谱名称"][
        0
    ].value == "鸡蛋"

    # 只切换分类，名称和收藏仍同时约束结果，目标按新分类重新出现。
    at.selectbox[1].select("汤羹").run()
    _assert_recipe_list(at, [expected_target])
    assert "**菜谱分类：汤羹**" in _page_messages(at)
    assert "鸡蛋：3 个" in _page_messages(at)
    assert "**步骤2**：炒熟后加盐" in _page_messages(at)
    assert _read_page_recipes() == expected
