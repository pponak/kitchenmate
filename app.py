# 页面负责输入和校验，db_storage.py 的函数负责执行 SQL 和提交
##########################################
##########################################
##########################################


import streamlit as st
from db_storage import (
    connect_db,
    create_recipes_table,
    get_all_recipes,
    search_recipes_by_name,
    add_recipe,
    get_recipe_by_id,
    delete_recipe,
    update_recipe_name,
    update_recipe_favorite,
    update_recipe_content
    )

# 标题
st.title("欢迎来到菜谱应用")

# 连接数据库并创建菜谱表
connection = connect_db()
create_recipes_table(connection)

# 初始化session_state(相当于记事本，跨会话状态保存)中的食材行ID
## ingredient_row_ids:当前要显示哪些行
## next_ingredient_row_id:下一个要添加的行的ID，初始为1
## editing_recipe_id:当前正在编辑的菜谱ID，初始为None
if "ingredient_row_ids" not in st.session_state:
    st.session_state.ingredient_row_ids = [0]
if "next_ingredient_row_id" not in st.session_state:
    st.session_state.next_ingredient_row_id = 1
if "editing_recipe_id" not in st.session_state:
    st.session_state.editing_recipe_id = None


# 增加食材行
def add_ingredient_row():
    st.session_state.ingredient_row_ids.append(
        st.session_state.next_ingredient_row_id
    )
    st.session_state.next_ingredient_row_id += 1


# 修改时增加食材行
def add_edit_ingredient_row():
    st.session_state.edit_ingredient_row_ids.append(
        st.session_state.next_edit_ingredient_row_id
    )
    st.session_state.next_edit_ingredient_row_id += 1

# 删除食材行
def remove_ingredient_row(row_id):
    st.session_state.ingredient_row_ids.remove(row_id)


# 修改时删除食材行
def remove_edit_ingredient_row(row_id):
    st.session_state.edit_ingredient_row_ids.remove(row_id)


# 添加菜谱表单
with st.form("添加菜谱", enter_to_submit=False):
    recipe_name_text = st.text_input("菜谱名称")
    ## 分类
    category = st.selectbox("菜谱分类", 
                            ["主菜", "配菜", "汤羹", "主食", "甜点", "饮品", "其他"], 
                            index=6)
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
    ### 判断输入是否为空，如果为空，提示用户；校验通过，添加菜谱
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
                    "steps": steps,
                    "category": category
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


# 按名称，分类，收藏来筛选显示的菜谱
# 选择分类，筛选菜谱
selected_category = st.selectbox(
            "筛选菜谱分类", 
            ["全部", "主菜", "配菜", "汤羹", "主食", "甜点", "饮品", "其他"],
            index=0)

# 按名称搜索菜谱
keyword = st.text_input("搜索菜谱名称").strip()
# 勾选是否筛选收藏
favorite_only = st.checkbox("只看收藏")
## 如果搜索框不为空，按名称搜索菜谱，否则获取所有菜谱
if keyword:
    recipes = search_recipes_by_name(connection, keyword)
else:
    recipes = get_all_recipes(connection)
## 如果选择的分类不是全部，按分类筛选菜谱    
if selected_category != "全部":
    recipes = [recipe for recipe in recipes if recipe["category"] == selected_category]
## 筛选已收藏的菜谱
if favorite_only:
    recipes = [recipe for recipe in recipes if recipe["favorite"] == 1]
## 显示搜索结果
if not recipes:
    if favorite_only:
        st.write("没有符合当前条件的收藏菜谱")
    elif keyword:
        st.write("没有找到符合搜索条件的相关菜谱")
    elif selected_category == "全部":
        st.write("没有菜谱")
    else:
        st.write(f"{selected_category}分类下没有菜谱")
else:
    if favorite_only:
        st.write("符合当前搜索条件的收藏菜谱：\n")
    elif keyword:
        if selected_category == "全部":
            st.write(f"关于名称包含{keyword}的搜索结果：\n")
        else:
            st.write(f"关于分类为{selected_category}，名称包含{keyword}的搜索结果：\n")
    elif selected_category == "全部":
        st.write("所有菜谱：\n")
    else:
        st.write(f"所有分类为{selected_category}的菜谱：\n")
        
    for recipe in recipes:
        ### 显示收藏状态
        if recipe["favorite"] == 1:
            star_label = "★"
        else:
            star_label = "☆"
        
        favorite_clicked = st.button(star_label, key=f"favorite_{recipe['id']}")
        ### 如果点击收藏按钮，更新收藏状态，重新运行脚本
        if favorite_clicked:
            if recipe["favorite"] == 1:
                new_favorite = 0
            else:
                new_favorite = 1
            update_recipe_favorite(connection, recipe["id"], new_favorite)
            connection.close()
            st.rerun()
        
        with st.expander(f"菜谱ID：{recipe['id']}，菜谱名称： {recipe['name']}"):
            st.write(f"菜谱分类：{recipe['category']}")
            st.write("食材：")
            for ingredient in recipe['ingredients']:
                st.write(f"{ingredient['name']}：{ingredient['amount']} {ingredient['unit']}")
            st.write("步骤：")
            for index, step in enumerate(recipe['steps'], start=1):
                st.write(f"步骤{index}：{step}")
            ### 添加编辑按钮
            edit_clicked = st.button("编辑菜谱", key=f"edit_{recipe['id']}")
            #### 点击按钮：记录编辑状态
            if edit_clicked:
                ##### 在编辑时时，可以增删输入行
                ##### session_state记录当前显示行，下一条新行使用的id，并初始化
                ##### 判断避免重复点击同一份菜谱的按钮造成重置
                ##### 且在点击新的菜谱编辑按钮时，重新初始化row_id
                if st.session_state.editing_recipe_id != recipe["id"]:
                    st.session_state.edit_ingredient_row_ids = list(range(len(recipe["ingredients"])))
                    st.session_state.next_edit_ingredient_row_id = len(recipe["ingredients"])
                st.session_state.editing_recipe_id = recipe["id"]
            #### 控制显示：读取编辑状态
            if st.session_state.editing_recipe_id == recipe["id"]:
                with st.form(f"edit_recipe_{recipe['id']}", enter_to_submit=False):
                    ##### 编辑食材
                    edited_ingredient_inputs = []
                    ###### 按行id显示食材输入框
                    for row_id in st.session_state.edit_ingredient_row_ids:
                        ####### 如果行id小于食材数量，显示食材输入框，否则显示空输入框
                        if row_id < len(recipe["ingredients"]):
                            ingredient = recipe["ingredients"][row_id]
                        else:
                            ingredient = {
                                "name": "",
                                "amount": "",
                                "unit": ""
                                }
                        ###### 显示食材输入框
                        edited_name = st.text_input(
                            "食材名称",
                            value=ingredient["name"],
                            key=f"edit_ingredient_name_{recipe['id']}_{row_id}"
                        ).strip()
                        edited_amount = st.text_input(
                            "食材数量",
                            value=ingredient["amount"],
                            key=f"edit_ingredient_amount_{recipe['id']}_{row_id}"
                        ).strip()
                        edited_unit = st.text_input(
                            "食材单位",
                            value=ingredient["unit"],
                            key=f"edit_ingredient_unit_{recipe['id']}_{row_id}"
                        ).strip()
                        edited_ingredient_inputs.append({
                            "name": edited_name,
                            "amount": edited_amount,
                            "unit": edited_unit,
                        })
                        ###### 删除食材行按钮
                        st.form_submit_button(
                            "删除食材",
                            key=f"delete_edit_ingredient_{recipe['id']}_{row_id}",
                            on_click=remove_edit_ingredient_row,
                            args=(row_id,),
                        )
                    ###### 增加食材行按钮
                    st.form_submit_button(
                        "添加食材",
                        key=f"add_edit_ingredient_{recipe['id']}",
                        on_click=add_edit_ingredient_row,
                    )
                    ##### 编辑步骤
                    original_steps_text = "\n".join(recipe["steps"])
                    edited_steps_text = st.text_area("编辑步骤（每行一个步骤）", value=original_steps_text, key=f"edit_steps_{recipe['id']}")
                    save_clicked = st.form_submit_button("保存")
                #### 点击保存-》整理输入
                if save_clicked:
                    edited_ingredients = []
                    edited_missing_name = False
                    ##### 整理食材
                    for ingredient in edited_ingredient_inputs:
                        if ingredient["name"]:
                            edited_ingredients.append(ingredient)
                        elif ingredient["amount"] or ingredient["unit"]:
                            edited_missing_name = True
                    ##### 整理步骤
                    edited_steps = []
                    for step in edited_steps_text.splitlines():
                        step = step.strip()
                        if step:
                            edited_steps.append(step)
                    ##### 保存
                    if edited_missing_name:
                        st.error("请补全食材名称！")
                    elif not edited_ingredients:
                        st.error("至少要有一个食材！")
                    elif not edited_steps:
                        st.error("步骤不能为空！")
                    else:
                        update_recipe_content(
                            connection,
                            recipe["id"],
                            edited_ingredients,
                            edited_steps
                        )
                        ###### 退出编辑状态，关闭连接，重新运行脚本显示新内容
                        st.session_state.editing_recipe_id = None
                        connection.close()
                        st.rerun()
                            
connection.close()
