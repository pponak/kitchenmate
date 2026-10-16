# KitchenMate 启动流程
#
# 本文件可以承担两种角色，由启动参数决定：
# 1. 没有 --server：执行 main()，负责协调启动和显示窗口。
# 2. 带有 --server：执行 run_server()，只运行 Streamlit 服务。
#
# 普通启动的执行顺序：
# 进程 A 执行 main()
# → 检查端口是否已有服务
# → 用 Popen 启动带 --server 的进程 B
# → B 执行 run_server()，运行 app.py 服务
# → A 等待服务就绪，再打开 pywebview 窗口
# → 用户关闭窗口，webview.start() 返回
# → A 在 finally 中停止 B、等待 B 退出，然后结束
#
# 源码阶段：使用当前 Python 执行本文件，并附带 --server。
# 打包之后：运行自己的 exe，并附带 --server。


import webview
import subprocess
import sys
import time
import socket
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError
# 取得 Streamlit 的命令入口
from streamlit.web import cli as stcli

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8502
SERVER_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
HEALTH_URL = f"{SERVER_URL}/_stcore/health"


# 根据入口文件的位置，找到同目录的菜谱页面
app_file = Path(__file__).resolve().parent / "app.py"

#
def run_server():
    # 准备要交给 Streamlit 的启动要求
    server_args = [
        "run",
        str(app_file),
        f"--server.address={SERVER_HOST}",
        f"--server.port={SERVER_PORT}",
        "--server.headless=true",
        "--global.developmentMode=false",
    ]

    # 按上面的要求启动服务
    stcli.main(args=server_args, prog_name="streamlit")


# 检查页面服务是否已准备好接收连接
def is_server_ready(url):
    try:
        ## 访问传入的地址。对当前 HTTP 地址，
        ## 请求成功取得响应后，它返回一个响应对象，里面包含状态码、响应头等信息
        with urlopen(url, timeout=1) as response:
            return response.status == 200
    except (URLError, TimeoutError):
        return False

# socket:检查端口是否被占用
# 连接成功返回 True；连接被拒绝返回 False；其他异常向外抛出
def is_port_in_use(host, port):
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except ConnectionRefusedError:
        return False

def main():
    # 如果端口已被占用，说明可能已经打开了 KitchenMate，直接结束本次启动
    if is_port_in_use(SERVER_HOST, SERVER_PORT):
        raise SystemExit(f"{SERVER_PORT}端口已被使用，请检查是否已经打开了 KitchenMate，本次启动结束")


    # 使用当前 Python 解释器启动 KitchenMate 页面服务
    # 保存进程对象，方便后续检查状态，以及关闭窗口时结束服务
    # Popen 启动子进程后，主程序继续往下执行；此时服务不一定已经准备好
    # getattr(对象， 属性名， 默认值)，取不到时返回默认值
    # sys.frozen会在PyInstaller打包后设置为True
    ## 如果不是打包后的程序，就使用当前 Python 解释器启动入口文件
    if getattr(sys, "frozen", False):
        server_command = [
            sys.executable,
            "--server",
        ]
    else:
        server_command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--server",
        ]

    server_process = subprocess.Popen(server_command)

    # 检查进程是否退出
    #  ↓ 仍在运行
    # 检查服务是否就绪
    #  ↓ 尚未就绪
    # 暂停半秒，再进入下一轮
    # try 内的操作正常结束，或者抛出异常退出时，都执行这里的收尾代码
    try:
        ready = False
        ## 最多请求20次，让页面服务完成启动
        for _ in range(20):
        ### 等待过程中，本入口启动的服务进程已经退出，就停止等待
        ### poll() 返回进程退出码，进程仍在运行时返回 None
            exit_code = server_process.poll()
            if exit_code is not None:
                print(f"页面服务进程已退出，退出码：{exit_code}")
                break
            ### 检查页面服务是否已准备好接收连接
            ready = is_server_ready(HEALTH_URL)
            if ready == True:
                break
            time.sleep(0.5)
    ## 如果服务已准备好，就创建窗口并启动
        if ready:
            webview.create_window("KitchenMate", url=SERVER_URL)
            webview.start()
        else:
            print("页面服务未在规定检查次数内就绪，启动结束。")
    finally:
        # 窗口结束后，停止本入口启动的页面服务
        if server_process.poll() is None:
            server_process.terminate()
        # 等待服务进程退出，再退出入口程序
        server_process.wait()

if __name__ == "__main__":
    if "--server" in sys.argv:
        run_server()
    else:
        main()
