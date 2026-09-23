import streamlit as st
from db_storage import (
    connect_db,
    create_recipes_table,
    get_all_recipes,
    search_recipes_by_name,
    add_recipe,
    get_recipe_by_id,
    delete_recipe
    )

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

# 删除菜谱:输入要删除菜谱的ID-》检查输入是否为空-》检查ID是否为数字-》检查ID是否存在-》删除菜谱
delete_id_text = st.text_input("要删除的菜谱ID")
check_clicked = st.button("删除菜谱")

if check_clicked:
    delete_id = delete_id_text.strip()
    if not delete_id:
        st.write("菜谱ID不能为空")
    else:
        try:
            delete_id = int(delete_id)
        except ValueError:
            st.write("请输入数字ID")
        else:
            target_recipe = get_recipe_by_id(connection, delete_id)
            if target_recipe is None:
                st.write(f"没有找到ID为{delete_id}的菜谱")
            else:
                delete_recipe(connection, delete_id)
                st.write(f"已删除菜谱：{target_recipe['id']}. {target_recipe['name']}")


# 按名称搜索菜谱
keyword = st.text_input("搜索菜谱名称").strip()
## 如果搜索框不为空，按名称搜索菜谱，否则获取所有菜谱
if keyword:
    recipes = search_recipes_by_name(connection, keyword)
else:
    recipes = get_all_recipes(connection)
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

connection.close()