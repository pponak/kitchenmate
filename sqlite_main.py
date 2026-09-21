from db_storage import (
    connect_db,
    create_recipes_table,
    add_recipe,
    get_all_recipes,
    get_recipe_by_id,
    update_recipe_name,
    delete_recipe
)

# 显示所有菜谱id和名称
def show_recipes(connection):
    all_recipes = get_all_recipes(connection)
    
    if not all_recipes:
        print("暂无菜谱")
        return
    
    print("所有菜谱列表：")
    for recipe in all_recipes:
        print(f"菜谱ID: {recipe['id']}, 菜谱名称：{recipe['name']}")

# 添加菜谱
def input_recipe():
    ingredients = []
    steps = []
    
    # 添加名称
    while True:
        recipe_name = input("请输入菜谱名称：").strip()
        
        if recipe_name:
            break
        
        print("菜谱名称不能为空，请重新输入。")
        
    # 添加食材
    while True:
        choice = input("是否添加食材？(y/n)").strip().lower()
        
        if choice == "n":
            break
        elif choice != "y":
            print("请输入 y 或 n。")
            continue
        
        ingredient_name = input("食材名称：").strip()
        
        if not ingredient_name:
            print("食材不能为空，请重新输入。")
            continue
        
        amount = input("数量：").strip()
        unit = input("单位：").strip()
        
        ingredient = {
            "name": ingredient_name,
            "amount": amount,
            "unit": unit
        }
        
        ingredients.append(ingredient)
        
    # 添加步骤
    while True:
        choice = input("是否添加步骤？(y/n)").strip().lower()
        
        if choice == "n":
            break
        elif choice != "y":
            print("请输入 y 或 n。")
            continue
        
        step = input("步骤内容：").strip()
        
        if not step:
            print("步骤不能为空，请重新输入。")
            continue
        
        steps.append(step)
            
    return {
        "name": recipe_name,
        "ingredients": ingredients,
        "steps": steps
    }

# 根据id，删除菜谱
def delete_recipe_interactive(connection):
    ## 查看是否有无菜谱
    all_recipes = get_all_recipes(connection)
    
    if not all_recipes:
        print("暂无菜谱")
        return
    
    ## 展示所有菜谱id和名称
    show_recipes(connection)
    
    ## 输入要删除的菜谱ID
    try:
        recipe_id = int(input("请输入要删除的菜谱ID："))
    except ValueError:
        print("请输入数字ID。")
        return
    
    ## 查找要删除的菜谱信息
    recipe = get_recipe_by_id(connection, recipe_id)
    
    if recipe is None:
        print("没有找到这个菜谱ID。")
        return
    
    ## 删除菜谱
    delete_recipe(connection, recipe_id)
    
    ## 显示删除结果
    print(f"已删除菜谱：{recipe['id']}. {recipe['name']}")
        

def main():
    connection = connect_db()
    create_recipes_table(connection)
    
    while True:
        print("=====菜谱管理系统=====")
        print("1. 添加菜谱")
        print("2. 查看菜谱")
        print("3. 删除菜谱")
        print("4. 搜索菜谱")
        print("5. 修改菜谱名称")
        print("0. 退出")
        try:
            choice = int(input("请选择操作："))
        except ValueError:
            print("请输入数字！！！")
            print()
            continue
        
        if choice == 1:
            recipe = input_recipe()
            recipe_id = add_recipe(connection, recipe)
            print(f"菜谱添加成功, id是：{recipe_id}")
        elif choice == 2:
            show_recipes(connection)
        elif choice == 3:
            delete_recipe_interactive(connection)
        elif choice == 0:
            break
        else:
            print("无效的编号，请输入正确编号的！！！")
        
        print()
    
    connection.close()

if __name__ == "__main__":
    main()
