from storage import load_recipes ,save_recipes 

# 获取用户输入的菜谱编号，判断是否合规，并转换为菜谱列表索引
def get_recipe_index(recipes, action):
    try:
        recipe_number = int(input(f"请输入要{action}的菜谱编号："))
    ## 判断输入是否为数字
    except ValueError:
        print("请输入菜谱的数字编号！！！")
        return None
    ## 判断编号是否超出范围
    if recipe_number < 1 or recipe_number > len(recipes):
        print("菜谱编号无效")
        return None
    
    return recipe_number - 1

# 函数：输入食材字典列表
def input_ingredients():
    ingredients = []

    while True:
        choice = input("是否添加食材?(y/n)").strip().lower()

        if choice == "n":
            break
        elif choice != "y":
            print("请输入 y 或 n。")
            continue

        name = input("食材名称：").strip()

        if not name:
            print("食材名称不能为空。")
            continue

        amount = input("数量：").strip()
        unit = input("单位：").strip()

        ingredient = {
            "name": name,
            "amount": amount,
            "unit": unit
        }

        ingredients.append(ingredient)

    return ingredients

# 函数：输入步骤列表
def input_steps():
    steps = []

    while True:
        choice = input("是否添加步骤?(y/n)").strip().lower()

        if choice == "n":
            break
        elif choice != "y":
            print("请输入 y 或 n。")
            continue

        step = input("步骤内容：").strip()

        if not step:
            print("步骤内容不能为空。")
            continue

        steps.append(step)

    return steps

# 函数：创建菜谱
def create_recipe():
    while True:
        name = input("菜谱名称：").strip()

        if name:
            break

        print("菜谱名称不能为空。")

    ingredients = input_ingredients()
    steps = input_steps()

    recipe = {
        "name": name,
        "ingredients": ingredients,
        "steps": steps
    }

    return recipe

# 函数：添加菜谱到菜谱列表
def add_recipe(recipes):
    recipe = create_recipe()
    recipes.append(recipe)
    save_recipes(recipes)
    print("菜谱已添加。")

# 函数：显示菜谱列表
def show_recipes(recipes):
    if not recipes:
        print("暂无菜谱")
        return
    ## enumerate返回索引和值
    for index, recipe in enumerate(recipes, start=1):
        print(f"{index}. {recipe['name']}")
    
# 函数：删除菜谱
def delete_recipe(recipes):
    if not recipes:
        print("暂无菜谱")
        return
    
    ## 显示菜谱列表
    show_recipes(recipes)
    
    ## 获取索引，删除菜谱
    recipe_index = get_recipe_index(recipes, "删除")
    if recipe_index is None:
        return
    deleted_recipe = recipes.pop(recipe_index)
    ### 删除后保存菜谱列表到JSON文件
    save_recipes(recipes)
    
    print(f"已删除菜谱：{deleted_recipe['name']}")


def search_recipes(recipes):
    # 菜谱列表为空
    if not recipes:
        print("暂无菜谱，无法搜索")
        return
    
    # 获取用户输入的关键词，为空则返回
    keyword = input("请输入要搜索的菜谱关键词：").strip().lower()
    if not keyword:
        print("搜索关键词不能为空！！！")
        return
    
    # 遍历菜谱列表，查找包含关键词的菜谱
    found_recipes = []
    for recipe in recipes:
        if keyword in recipe["name"].lower():
            found_recipes.append(recipe)
        
    if found_recipes:
        print(f"找到{len(found_recipes)}个菜谱：")
        for index, recipe in enumerate(found_recipes, start=1):
            print(f"{index}. {recipe}")
    else:
        print("没有找到相关菜谱。")

def update_recipe_name(recipes):
    if not recipes:
        print("暂无菜谱")
        return
    ## 显示菜谱列表
    print("请选择要修改的菜谱，以下是菜谱列表：")
    show_recipes(recipes)
    ## 获取并验证用户输入的菜谱编号
    recipe_index = get_recipe_index(recipes, "修改")
    if recipe_index is None:
        return
    ## 修改菜谱名称
    new_name = input("请输入新的菜谱名称：").strip()
    if not new_name:
        print("菜谱名称不能为空")
        return
    old_name = recipes[recipe_index]['name']
    recipes[recipe_index]['name'] = new_name
    save_recipes(recipes)
    print(f"菜谱名称已从 {old_name} 修改为 {new_name}。")
    

# 主函数：程序入口，调用其他函数
def main():
    recipes = load_recipes()
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
            add_recipe(recipes)
        elif choice == 2:
            show_recipes(recipes)
        elif choice == 3:
            delete_recipe(recipes)
        elif choice == 4:
            search_recipes(recipes)
        elif choice == 5:
            update_recipe_name(recipes)
        elif choice == 0:
            break
        else:
            print("无效的编号，请输入正确编号的！！！")
        
        print()

if __name__ == "__main__":
    main()

        