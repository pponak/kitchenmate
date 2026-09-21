from db_storage import (
    connect_db,
    create_recipes_table,
    add_recipe,
    get_all_recipes,
    get_recipe_by_id,
    update_recipe_name,
    delete_recipe
)
    
# 主程序
def main():
    connection = connect_db()
    create_recipes_table(connection)
    
    test_recipe = {
        "name": "数据库测试菜谱",
        "ingredients": [
            {
                "name": "测试食材",
                "amount": "1",
                "unit": "份"
            }
        ],
        "steps": [
            "准备食材",
            "完成测试"
        ]
    }
    
    # 测试添加
    recipe_id = add_recipe(connection, test_recipe)
    print(f"菜谱添加成功，id是：{recipe_id}")
    
    # 测试查询
    all_recipes = get_all_recipes(connection)
    print("当前所有菜谱：")
    for recipe in all_recipes:
        print(recipe)
    
    found_recipe = get_recipe_by_id(connection, recipe_id)
    print("查询结果：")
    print(found_recipe)

    # 测试修改
    update_recipe_name(connection, recipe_id, "数据库测试菜谱（已修改）")
    
    update_recipe = get_recipe_by_id(connection, recipe_id)
    print("修改后的菜谱：")
    print(update_recipe)
    
    # 测试删除
    delete_recipe(connection, recipe_id)
    
    deleted_recipe = get_recipe_by_id(connection, recipe_id)
    print("删除后再次查询：")
    print(deleted_recipe)
    
    connection.close()
    
if __name__ == "__main__":
    main()
    


# # 连接到数据库，如果不存在则创建
# ## connection代表数据库连接对象
# ## cusor代表游标对象，用于执行SQL语句
# connection = sqlite3.connect(DB_FILE)
# cursor = connection.cursor()

# # 创建表（如果不存在）
# cursor.execute("""
#     CREATE TABLE IF NOT EXISTS recipes(
#         id INTEGER PRIMARY KEY,
#         name TEXT,
#         ingredients TEXT,
#         steps TEXT
#         )
# """)

# # 定义菜谱数据
# recipe = {
#     "name": "番茄炒蛋",
#     "ingredients": [
#         {
#             "name": "鸡蛋",
#             "amount": "2",
#             "unit": "个"
#         },
#         {
#             "name": "番茄",
#             "amount": "2",
#             "unit": "个"
#         }
#     ],
#     "steps": [
#         "打散鸡蛋",
#         "炒熟鸡蛋",
#         "加入番茄翻炒"
#     ]
# }

# # 将数据转换为JSON字符串
# ingredients_text = json.dumps(recipe['ingredients'], ensure_ascii=False)
# steps_text = json.dumps(recipe['steps'], ensure_ascii=False)

# # # 插入数据到表中
# # cursor.execute(
# #     """
# #         INSERT INTO recipes (name, ingredients, steps)
# #         VALUES (?, ?, ?)    
# #     """,
# #     (
# #         recipe['name'],
# #         ingredients_text,
# #         steps_text
# #     )
# #     )




# ## 修改菜谱名称
# # recipe_id = 2
# # new_name = "番茄炒蛋（少油版）"

# # cursor.execute(
# #     """
# #     UPDATE recipes
# #     SET name = ?
# #     WHERE id = ?
# #     """,
# #     (new_name, recipe_id)
# # )

# # 删除菜谱
# recipe_id = 4
# cursor.execute(
#     """
#     DELETE FROM recipes
#     WHERE id = ?
#     """,
#     (recipe_id,)
# )

# connection.commit()
# print("菜谱删除完成")

# # 查询剩余菜谱，显示名称
# cursor.execute(
#     """
#     SELECT id, name
#     FROM recipes
#     ORDER BY id
#     """
# )

# remaining_recipes = cursor.fetchall()
# print("剩余菜谱：", remaining_recipes)

# # 查询数据
# cursor.execute(
#     """
#     SELECT id, name, ingredients, steps
#     FROM recipes
#     WHERE id = ?
#     """,
#     (recipe_id,)
# )

# # 获取所有数据
# rows = cursor.fetchall()

# # 打印数据,并解析JSON字符串
# for row in rows:
#     recipe = {
#         "id": row[0],
#         "name": row[1],
#         "ingredients": json.loads(row[2]),
#         "steps": json.loads(row[3])
#     }
    
#     print(recipe)

# connection.close()

# print("数据库和 recipes 表创建完成")