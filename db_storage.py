import json
import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "kitchenmate.db"

# 连接数据库，返回一个连接对象
def connect_db():
    connection = sqlite3.connect(DB_FILE)
    return connection

# 创建recipes表
def create_recipes_table(connection):
    cursor = connection.cursor()
    
    cursor.execute(
    """
    CREATE TABLE IF NOT EXISTS recipes(
        id INTEGER PRIMARY KEY,
        name TEXT,
        ingredients TEXT,
        steps TEXT
    )
    """
    )
    
    connection.commit()
    
# 添加菜谱
def add_recipe(connection, recipe):
    ## 将食材和步骤由python列表转换为JSON字符串
    ingredients_text = json.dumps(
        recipe['ingredients'],
        ensure_ascii=False
    )
    
    steps_text = json.dumps(
        recipe['steps'],
        ensure_ascii=False
    )

    cursor = connection.cursor()
    
    cursor.execute(
    """
    INSERT INTO recipes (name, ingredients, steps)
    VALUES (?, ?, ?)
    """,
    (
        recipe['name'],
        ingredients_text,
        steps_text
    )
    )
    
    connection.commit()
    
    return cursor.lastrowid

# 获取所有菜谱，返回一个列表
def get_all_recipes(connection):
    cursor = connection.cursor()
    
    cursor.execute(
    """
    SELECT id, name, ingredients, steps
    FROM recipes
    ORDER BY id
    """
    )
    
    rows = cursor.fetchall()
    recipes = []
    
    for row in rows:
        recipe = {
            "id": row[0],
            "name": row[1],
            "ingredients": json.loads(row[2]),
            "steps": json.loads(row[3])
        }
        recipes.append(recipe)
        
    return recipes
    
    

# 根据id获取菜谱
def get_recipe_by_id(connection, recipe_id):
    cursor = connection.cursor()
    
    cursor.execute(
    """
    SELECT id, name, ingredients, steps
    FROM recipes
    WHERE id = ?
    """,
    (recipe_id,)
    )
    
    row = cursor.fetchone()
    
    if row is None:
        return None
    
    recipe = {
        "id": row[0],
        "name": row[1],
        "ingredients": json.loads(row[2]),
        "steps": json.loads(row[3])
    }
    
    return recipe

# 修改菜谱名称
def update_recipe_name(connection, recipe_id, new_name):
    cursor = connection.cursor()
    
    cursor.execute(
    """
    UPDATE recipes
    SET name = ?
    WHERE id = ?
    """,
    (new_name, recipe_id)
    )
    
    connection.commit()

# 删除菜谱
def delete_recipe(connection, recipe_id):
    cursor = connection.cursor()
    
    cursor.execute(
    """
    DELETE FROM recipes
    WHERE id = ?
    """,
    (recipe_id,)
    )
    
    connection.commit()
