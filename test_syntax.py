import ast

def check_syntax(file_path):
    with open(file_path, "r") as f:
        source = f.read()
    try:
        ast.parse(source)
        print(f"{file_path} syntax is OK.")
    except SyntaxError as e:
        print(f"Syntax error in {file_path}: {e}")

check_syntax("backend/server.py")
