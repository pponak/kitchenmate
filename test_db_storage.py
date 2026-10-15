"""使用独立临时数据库，验证 SQLite 数据层的实际行为。"""

from contextlib import closing
import sqlite3

import pytest

import db_storage
from db_storage import (
    add_recipe,
    create_recipes_table,
    delete_recipe,
    get_all_recipes,
    get_recipe_by_id,
    search_recipes_by_name,
    update_recipe_content,
    update_recipe_favorite,
    update_recipe_name,
)


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """每项测试使用自己的数据库，也让 connect_db 指向这个临时文件。"""
    path = tmp_path / "test.db"
    monkeypatch.setattr(db_storage, "DB_FILE", path)
    with closing(db_storage.connect_db()) as connection:
        create_recipes_table(connection)
    return path


def make_recipe(name="鸡蛋汤", category="汤羹"):
    """集中准备示例数据，每次调用都返回独立的字典和列表。"""
    return {
        "name": name,
        "category": category,
        "ingredients": [
            {"name": "鸡蛋", "amount": "2", "unit": "个"},
            {"name": "水", "amount": "300", "unit": "毫升"},
        ],
        "steps": ["打散鸡蛋", "水开后加入鸡蛋煮熟"],
    }


def expected_recipe(recipe_id, recipe, favorite=0):
    """查询结果包含数据库 ID 和收藏状态，新菜谱默认未收藏。"""
    return {"id": recipe_id, **recipe, "favorite": favorite}


def test_add_then_get_recipe(db_path):
    recipe = make_recipe()
    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)

    # 关闭再连接，确认完整菜谱已经持久保存。
    with closing(sqlite3.connect(db_path)) as connection:
        actual = get_recipe_by_id(connection, recipe_id)
        assert actual == expected_recipe(recipe_id, recipe)


def test_delete_recipe(db_path):
    recipe = make_recipe()
    other_recipe = make_recipe("番茄汤")
    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)
        other_id = add_recipe(connection, other_recipe)
        update_recipe_favorite(connection, other_id, 1)
        delete_recipe(connection, recipe_id)

    # 指定菜谱消失，其他菜谱的所有字段保持不变。
    with closing(sqlite3.connect(db_path)) as connection:
        assert get_recipe_by_id(connection, recipe_id) is None
        assert get_all_recipes(connection) == [expected_recipe(other_id, other_recipe, 1)]


def test_update_recipe_name(db_path):
    recipe = make_recipe()
    other_recipe = make_recipe("番茄汤")
    new_name = "妈妈的'鸡蛋汤"
    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)
        other_id = add_recipe(connection, other_recipe)
        update_recipe_favorite(connection, recipe_id, 1)
        update_recipe_name(connection, recipe_id, new_name)

    with closing(sqlite3.connect(db_path)) as connection:
        expected = expected_recipe(recipe_id, {**recipe, "name": new_name}, 1)
        # 只有目标菜谱的名称改变，分类、食材、步骤和另一份菜谱不变。
        assert get_recipe_by_id(connection, recipe_id) == expected
        assert get_all_recipes(connection) == [
            expected,
            expected_recipe(other_id, other_recipe),
        ]


@pytest.mark.parametrize(
    "include_category, expected_category",
    [(True, "汤羹"), (False, "其他")],
    ids=["selected-category", "missing-category-default"],
)
def test_saved_category_is_returned_by_queries(
    db_path, include_category, expected_category
):
    recipe = make_recipe()
    if not include_category:
        del recipe["category"]

    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)

    expected = expected_recipe(recipe_id, {**recipe, "category": expected_category})
    # 两种分类场景复用相同流程，并分别检查三个查询接口的完整结果。
    with closing(sqlite3.connect(db_path)) as connection:
        assert get_recipe_by_id(connection, recipe_id) == expected
        assert get_all_recipes(connection) == [expected]
        assert search_recipes_by_name(connection, "鸡蛋") == [expected]


def test_empty_database_returns_no_recipes(db_path):
    with closing(sqlite3.connect(db_path)) as connection:
        assert get_all_recipes(connection) == []
        assert get_recipe_by_id(connection, 1) is None
        assert search_recipes_by_name(connection, "鸡蛋") == []


def test_search_recipes_by_name(db_path):
    recipes = [
        make_recipe("番茄汤"),
        make_recipe("鸡蛋汤"),
        make_recipe("鸡蛋炒番茄", "主菜"),
    ]
    expected = []
    with closing(sqlite3.connect(db_path)) as connection:
        for recipe in recipes:
            recipe_id = add_recipe(connection, recipe)
            expected.append(expected_recipe(recipe_id, recipe))

    with closing(sqlite3.connect(db_path)) as connection:
        # 名称部分匹配，多个结果按 ID 升序，名称和分类等字段完整保留。
        assert search_recipes_by_name(connection, "鸡蛋") == expected[1:]
        assert search_recipes_by_name(connection, "面包") == []
        assert get_all_recipes(connection) == expected


def test_search_treats_quotes_as_text(db_path):
    recipe = make_recipe("妈妈的'鸡蛋汤")
    other_recipe = make_recipe("番茄汤")
    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)
        other_id = add_recipe(connection, other_recipe)

    with closing(sqlite3.connect(db_path)) as connection:
        expected = expected_recipe(recipe_id, recipe)
        assert search_recipes_by_name(connection, "'鸡蛋") == [expected]
        # 类似 SQL 的搜索文字也作为参数，不会扩大匹配范围或修改数据。
        assert search_recipes_by_name(connection, "' OR 1=1 --") == []
        assert get_all_recipes(connection) == [
            expected,
            expected_recipe(other_id, other_recipe),
        ]


def test_missing_id_does_not_change_existing_recipes(db_path):
    recipe = make_recipe()
    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)
        missing_id = recipe_id + 1
        assert get_recipe_by_id(connection, missing_id) is None
        update_recipe_name(connection, missing_id, "不存在的菜谱")
        update_recipe_content(connection, "其他", missing_id, [], [])
        update_recipe_favorite(connection, missing_id, 1)
        delete_recipe(connection, missing_id)

    with closing(sqlite3.connect(db_path)) as connection:
        assert get_all_recipes(connection) == [expected_recipe(recipe_id, recipe)]
        assert get_recipe_by_id(connection, missing_id) is None


def test_create_recipes_table_keeps_existing_data(db_path):
    recipe = make_recipe()
    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)
        create_recipes_table(connection)

    with closing(sqlite3.connect(db_path)) as connection:
        assert get_all_recipes(connection) == [expected_recipe(recipe_id, recipe)]


@pytest.mark.parametrize(
    "initial_favorite, target_favorite",
    [(0, 1), (1, 0)],
    ids=["favorite", "unfavorite"],
)
def test_update_recipe_favorite_is_persistent(
    db_path, initial_favorite, target_favorite
):
    recipe = make_recipe()
    other_recipe = make_recipe("番茄汤")
    with closing(sqlite3.connect(db_path)) as connection:
        recipe_id = add_recipe(connection, recipe)
        other_id = add_recipe(connection, other_recipe)
        if initial_favorite:
            update_recipe_favorite(connection, recipe_id, initial_favorite)

    with closing(sqlite3.connect(db_path)) as connection:
        # 先确认初始状态，再执行收藏或取消收藏。
        assert get_recipe_by_id(connection, recipe_id) == expected_recipe(
            recipe_id, recipe, initial_favorite
        )
        update_recipe_favorite(connection, recipe_id, target_favorite)

    # 关闭重连后，三个接口都能读到目标状态，其他菜谱及字段不变。
    with closing(sqlite3.connect(db_path)) as connection:
        expected = expected_recipe(recipe_id, recipe, target_favorite)
        assert get_recipe_by_id(connection, recipe_id) == expected
        assert get_all_recipes(connection) == [
            expected,
            expected_recipe(other_id, other_recipe),
        ]
        assert search_recipes_by_name(connection, "鸡蛋") == [expected]


@pytest.mark.parametrize(
    "new_ingredients, new_steps",
    [
        (
            [
                {"name": "鸡蛋", "amount": "3", "unit": "个"},
                {"name": "水", "amount": "400", "unit": "毫升"},
                {"name": "盐", "amount": "", "unit": ""},
            ],
            ["打散鸡蛋，加入'盐'", "水开后倒入鸡蛋", "煮熟后盛出"],
        ),
        (
            [{"name": "鸭蛋", "amount": "1", "unit": "个"}],
            ["煮熟鸭蛋"],
        ),
    ],
    ids=["more-ingredients-and-steps", "fewer-ingredients-and-steps"],
)
def test_update_recipe_content_is_persistent(db_path, new_ingredients, new_steps):
    """增减食材和步骤后重连，三个查询接口都返回新内容及原其他字段。"""
    other_recipe = make_recipe("番茄汤")
    target_recipe = make_recipe()
    with closing(sqlite3.connect(db_path)) as connection:
        other_id = add_recipe(connection, other_recipe)
        target_id = add_recipe(connection, target_recipe)
        update_recipe_favorite(connection, target_id, 1)
        update_recipe_content(
            connection,
            target_recipe["category"],
            target_id,
            new_ingredients,
            new_steps,
        )

    expected = expected_recipe(
        target_id,
        {**target_recipe, "ingredients": new_ingredients, "steps": new_steps},
        favorite=1,
    )
    with closing(sqlite3.connect(db_path)) as connection:
        assert get_recipe_by_id(connection, target_id) == expected
        assert get_all_recipes(connection) == [
            expected_recipe(other_id, other_recipe),
            expected,
        ]
        assert search_recipes_by_name(connection, "鸡蛋") == [expected]


@pytest.mark.parametrize("new_category", ["主菜", "其他"])
def test_update_recipe_category_is_persistent(db_path, new_category):
    """只改分类后重连，三个查询接口返回新分类，其他数据完整保留。"""
    other_recipe = make_recipe("番茄汤")
    target_recipe = make_recipe()
    with closing(sqlite3.connect(db_path)) as connection:
        other_id = add_recipe(connection, other_recipe)
        target_id = add_recipe(connection, target_recipe)
        update_recipe_favorite(connection, target_id, 1)
        update_recipe_content(
            connection,
            new_category,
            target_id,
            target_recipe["ingredients"],
            target_recipe["steps"],
        )

    expected = expected_recipe(
        target_id, {**target_recipe, "category": new_category}, favorite=1
    )
    with closing(sqlite3.connect(db_path)) as connection:
        assert get_recipe_by_id(connection, target_id) == expected
        assert get_all_recipes(connection) == [
            expected_recipe(other_id, other_recipe),
            expected,
        ]
        assert search_recipes_by_name(connection, "鸡蛋") == [expected]
