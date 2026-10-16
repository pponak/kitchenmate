import subprocess
import sys

process = subprocess.Popen(
    [sys.executable, "-c", "print('子程序：你好')"]
)

process.wait()
print("主程序：子程序已经结束")