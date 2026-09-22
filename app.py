import streamlit as st
from db_storage import connect_db, create_recipes_table, get_all_recipes, search_recipes_by_name, add_recipe

# 标题
st.title("欢迎来到菜谱应用")

# 连接数据库并创建菜谱表
connection = connect_db()
create_recipes_table(connection)

# 添加菜谱表单
with st.form("添加菜谱"):
    recipe_name_text = st.text_input("菜谱名称")
    ingredient_name_text = st.text_input("食材名称")
    ingredient_amount_text = st.text_input("食材数量")
    ingredient_unit_text = st.text_input("食材单位")
    step_text = st.text_input("步骤")
    submitted = st.form_submit_button("提交")
## 如果提交表单，重新运行脚本，submitted的值会变为True，进行添加菜谱操作
if submitted:
    recipe_name = recipe_name_text.strip()
    ingredient_name = ingredient_name_text.strip()
    ingredient_amount = ingredient_amount_text.strip()
    ingredient_unit = ingredient_unit_text.strip()
    steps = step_text.strip()
    ### 判断输入是否为空，如果为空，提示用户
    if recipe_name and ingredient_name and steps:
        recipe = {
                    "name": recipe_name,
                    "ingredients": [{"name": ingredient_name, "amount": ingredient_amount, "unit": ingredient_unit}],
                    "steps": [steps]
                }
        new_recipe_id = add_recipe(connection, recipe)
        st.write(f"菜谱添加成功，ID为{new_recipe_id}")
    else:
        if not recipe_name:
            st.write("菜谱名称不能为空！")
        elif not ingredient_name:
            st.write("食材名称不能为空！")
        elif not steps:
            st.write("步骤不能为空！")

# 按名称搜索菜谱
keyword = st.text_input("搜索菜谱名称").strip()
if keyword:
    recipes = search_recipes_by_name(connection, keyword)
else:
    recipes = get_all_recipes(connection)
    
connection.close()
## 显示搜索结果
if not recipes:
    if keyword:
        st.write("没有找到相关菜谱")
    else:
        st.write("没有菜谱")
else:
    if keyword:
        st.write(f"关于{keyword}的搜索结果：\n")
    else:
        st.write("所有菜谱：\n")
    for recipe in recipes:
        with st.expander(f"菜谱ID：{recipe['id']}，菜谱名称： {recipe['name']}"):
            st.write("食材：")
            for ingredient in recipe['ingredients']:
                st.write(f"{ingredient['name']}：{ingredient['amount']} {ingredient['unit']}")
            st.write("步骤：")
            for index, step in enumerate(recipe['steps'], start=1):
                st.write(f"步骤{index}：{step}")
