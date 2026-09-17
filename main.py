from storage import load_recipes ,save_recipes 
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

recipes = load_recipes()
add_recipe(recipes)
