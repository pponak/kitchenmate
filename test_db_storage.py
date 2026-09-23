import sqlite3
from db_storage import (
    create_recipes_table,
    add_recipe,
    get_recipe_by_id,
    delete_recipe,
    update_recipe_name
)

# 添加菜谱测试
def test_add_then_get_recipe(tmp_path):
    db_path = tmp_path / "test.db"
    ## 创建测试数据库连接并建表
    connection = sqlite3.connect(db_path)
    create_recipes_table(connection)

    test_recipe = {
                    "name": "测试用菜谱1",
                    "ingredients": [
                    {
                    "name": "dsf",
                    "amount": "1",
                    "unit": "g"
                    }],
                    "steps": ["清洗食材"]
                }

    test_recipe_id = add_recipe(connection, test_recipe)
    connection.close()
    ## 重新连接数据库，验证菜谱已经持久保存
    connection = sqlite3.connect(db_path)
    find_recipe = get_recipe_by_id(connection, test_recipe_id)
    ## 断言菜谱存在，且内容一致
    assert find_recipe is not None
    assert find_recipe['id'] == test_recipe_id
    assert find_recipe['name'] == test_recipe['name']
    assert find_recipe['ingredients'] == test_recipe['ingredients']
    assert find_recipe['steps'] == test_recipe['steps']

    connection.close()


# 删除菜谱测试
def test_delete_recipe(tmp_path):
    db_path = tmp_path / "test.db"
    connection = sqlite3.connect(db_path)
    create_recipes_table(connection)

    test_recipe = {
                "name": "测试用菜谱1",
                "ingredients": [
                {
                "name": "dsf",
                "amount": "1",
                "unit": "g"
                }],
                "steps": ["清洗食材"]
            }
    ## 添加菜谱到测试数据库并获取id
    test_recipe_id = add_recipe(connection, test_recipe)
    find_recipe = get_recipe_by_id(connection, test_recipe_id)
    ## 确认菜谱存在
    assert find_recipe is not None
    ## 删除菜谱
    delete_recipe(connection, test_recipe_id)
    connection.close()
    ## 重新连接数据库
    connection = sqlite3.connect(db_path)
    find_deleted_recipe = get_recipe_by_id(connection, test_recipe_id)
    ## 确认菜谱已被删除
    assert find_deleted_recipe is None

    connection.close()

# 修改菜谱名称测试
def test_update_recipe_name(tmp_path):
    db_path = tmp_path / "test.db"
    connection = sqlite3.connect(db_path)
    create_recipes_table(connection)

    test_recipe = {
                "name": "测试用菜谱1",
                "ingredients": [
                {
                "name": "dsf",
                "amount": "1",
                "unit": "g"
                }],
                "steps": ["清洗食材"]
            }
    ## 添加菜谱到测试数据库并获取id
    test_recipe_id = add_recipe(connection, test_recipe)
    new_name = "已经改名的菜谱"
    update_recipe_name(connection, test_recipe_id, new_name)
    connection.close()

    ## 重新连接数据库
    connection = sqlite3.connect(db_path)
    find_recipe = get_recipe_by_id(connection, test_recipe_id)
    ## 确认菜谱名称已被修改,且其他内容不变
    assert find_recipe is not None
    assert find_recipe['name'] == new_name
    assert find_recipe['ingredients'] == test_recipe['ingredients']
    assert find_recipe['steps'] == test_recipe['steps']
    connection.close()
