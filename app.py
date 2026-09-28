import streamlit as st
from db_storage import (
    connect_db,
    create_recipes_table,
    get_all_recipes,
    search_recipes_by_name,
    add_recipe,
    get_recipe_by_id,
    delete_recipe,
    update_recipe_name
    )

# 标题
st.title("欢迎来到菜谱应用")

# 连接数据库并创建菜谱表
connection = connect_db()
create_recipes_table(connection)

# 初始化session_state(相当于记事本，跨会话状态保存)中的食材行ID
## ingredient_row_ids:当前要显示哪些行
## next_ingredient_row_id:下一个要添加的行的ID，初始为1
if "ingredient_row_ids" not in st.session_state:
    st.session_state.ingredient_row_ids = [0]
if "next_ingredient_row_id" not in st.session_state:
    st.session_state.next_ingredient_row_id = 1
    
# 增加食材行
def add_ingredient_row():
    st.session_state.ingredient_row_ids.append(
        st.session_state.next_ingredient_row_id
    )
    st.session_state.next_ingredient_row_id += 1
    
# 删除食材行
def remove_ingredient_row(row_id):
    st.session_state.ingredient_row_ids.remove(row_id)

# 添加菜谱表单
with st.form("添加菜谱", enter_to_submit=False):
    recipe_name_text = st.text_input("菜谱名称")
    ## key: 1.区分同时显示的输入框 2.增行或删除行后认出原来的输入框
    ## 什么时候用key：循环生成或会增删重排的组件；单个/固定/易区分的不用
    ingredient_inputs = []
    for row_id in st.session_state.ingredient_row_ids:
        ingredient_name = st.text_input("食材名称", key=f"ingredient_name_{row_id}").strip()
        ingredient_amount = st.text_input("食材数量", key=f"ingredient_amount_{row_id}").strip()
        ingredient_unit = st.text_input("食材单位", key=f"ingredient_unit_{row_id}").strip()
        ingredient_inputs.append({    
                                "name": ingredient_name,
                                "amount": ingredient_amount,
                                "unit": ingredient_unit
                                })
        ### 按钮删除食材行，key帮助st按ID识别按钮
        st.form_submit_button("删除食材",
                            key=f"delete_ingredient_{row_id}",
                            on_click=remove_ingredient_row, 
                            args=(row_id,))
    ## 多行步骤，按行分割
    steps_text = st.text_area("步骤（按行分步骤）")
    submitted = st.form_submit_button("提交")
    ## on_click:点击后立即添加食材行，再重新运行脚本
    st.form_submit_button("添加食材", on_click=add_ingredient_row)
## 如果提交表单，重新运行脚本，submitted的值会变为True，进行添加菜谱操作
if submitted:
    recipe_name = recipe_name_text.strip()
    ingredients = []
    missing_name = False
    ### 判断食材名称/食材数量/单位是否为空，不为空添加进列表
    ### 三项为空跳过，只有名称为空提示用户
    for ingredient in ingredient_inputs:
        if ingredient["name"]:
            ingredients.append(ingredient)
        elif ingredient["amount"] or ingredient["unit"]:
            missing_name = True
    ### 多行步骤，按行分割
    steps = []
    for line in steps_text.splitlines():
        cleaned_line = line.strip()
        if cleaned_line:
            steps.append(cleaned_line)
    ### 判断输入是否为空，如果为空，提示用户
    if not recipe_name:
        st.write("菜谱名称不能为空！")
    elif missing_name:
        st.write("请补全食材名称！")
    elif not ingredients:
        st.write("至少要有一个食材！")
    elif not steps:
        st.write("步骤不能为空！")
    else:
        recipe = {
                    "name": recipe_name,
                    "ingredients": ingredients,
                    "steps": steps
                }
        new_recipe_id = add_recipe(connection, recipe)
        st.write(f"菜谱添加成功，ID为{new_recipe_id}")

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

# 修改菜谱名称
update_id_text = st.text_input("要修改的菜谱ID")
update_newname_text = st.text_input("要修改的菜谱名称")
update_clicked = st.button("修改菜谱名称")
## 如果点击修改按钮，检查输入是否为空-》检查ID是否为数字-》检查ID是否存在-》修改菜谱名称-》显示修改结果
if update_clicked:
    update_newname = update_newname_text.strip()
    if not update_newname:
        st.write("菜谱名称不能为空")
    elif not update_id_text.strip():
        st.write("菜谱ID不能为空")
    else:
        try:
            update_id = int(update_id_text.strip())
        except ValueError:
            st.write("请输入数字ID")
        else:
            target_recipe = get_recipe_by_id(connection, update_id)
            if target_recipe is None:
                st.write(f"没有找到ID为{update_id}的菜谱")
            else:
                update_recipe_name(connection, update_id, update_newname)
                st.write(f"已修改菜谱：{target_recipe['id']}. {target_recipe['name']} -> {update_newname}")

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
