#!/usr/bin/env python3
"""
公共API文档自动生成器

扫描源代码，自动生成所有公共API的文档，包括：
- 类、函数、方法
- 参数和返回值
- 文档字符串
- 类型提示
"""

import ast
import inspect
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional
import importlib.util
import textwrap


class PublicAPIDocGenerator:
    """公共API文档生成器"""

    def __init__(self, source_dirs: List[str]):
        """初始化

        Args:
            source_dirs: 源代码目录列表
        """
        self.source_dirs = [Path(d) for d in source_dirs]
        self.visited_modules: Set[str] = set()
        self.api_registry: Dict[str, dict] = {}

    def scan_directory(self, directory: Path) -> List[Path]:
        """扫描目录中的Python文件

        Args:
            directory: 目录路径

        Returns:
            Python文件列表
        """
        python_files = []
        for root, _, files in os.walk(directory):
            # 跳过测试和私有目录
            if any(part in root for part in ["test", "tests", "__pycache__", ".git"]):
                continue

            for file in files:
                if file.endswith(".py") and not file.startswith("_"):
                    python_files.append(Path(root) / file)

        return python_files

    def parse_file(self, file_path: Path) -> Optional[ast.AST]:
        """解析Python文件

        Args:
            file_path: 文件路径

        Returns:
            AST对象
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            return ast.parse(content)

        except Exception as e:
            print(f"⚠️  解析文件失败 {file_path}: {e}")
            return None

    def get_node_docstring(self, node: ast.AST) -> Optional[str]:
        """获取节点文档字符串

        Args:
            node: AST节点

        Returns:
            文档字符串
        """
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                return node.body[0].value.value
        return None

    def get_function_info(self, node: ast.FunctionDef, module_path: str) -> Optional[dict]:
        """获取函数信息

        Args:
            node: 函数节点
            module_path: 模块路径

        Returns:
            函数信息字典
        """
        docstring = self.get_node_docstring(node)

        # 解析参数
        args = []
        for arg in node.args.args:
            args.append(arg.arg)

        # 解析返回类型注解
        returns = None
        if node.returns:
            if isinstance(node.returns, ast.Constant):
                returns = node.returns.value
            elif isinstance(node.returns, ast.Name):
                returns = node.returns.id

        return {
            "type": "function",
            "name": node.name,
            "module": module_path,
            "args": args,
            "returns": returns,
            "docstring": docstring,
            "line_number": node.lineno,
        }

    def get_class_info(self, node: ast.ClassDef, module_path: str) -> Optional[dict]:
        """获取类信息

        Args:
            node: 类节点
            module_path: 模块路径

        Returns:
            类信息字典
        """
        docstring = self.get_node_docstring(node)

        # 获取基类
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)

        # 获取方法
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not item.name.startswith("_"):  # 跳过私有方法
                    method_info = self.get_function_info(item, module_path)
                    if method_info:
                        methods.append(method_info)

        return {
            "type": "class",
            "name": node.name,
            "module": module_path,
            "bases": bases,
            "methods": methods,
            "docstring": docstring,
            "line_number": node.lineno,
        }

    def process_module(self, file_path: Path) -> None:
        """处理模块

        Args:
            file_path: 文件路径
        """
        # 转换为模块路径
        module_path = str(file_path.relative_to(Path.cwd()).with_suffix("")).replace(
            "/", "."
        )

        # 解析AST
        tree = self.parse_file(file_path)
        if not tree:
            return

        # 遍历节点
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if self.is_public_api(node, tree):
                    func_info = self.get_function_info(node, module_path)
                    if func_info:
                        self.api_registry[f"{module_path}.{node.name}"] = func_info

            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                if self.is_public_api(node, tree):
                    class_info = self.get_class_info(node, module_path)
                    if class_info:
                        self.api_registry[f"{module_path}.{node.name}"] = class_info

    def is_public_api(
        self, node: ast.FunctionDef, tree: ast.AST
    ) -> bool:
        """判断是否为公共API

        Args:
            node: 函数或类节点
            tree: 完整的AST树

        Returns:
            是否为公共API
        """
        # 私有成员以下划线开头
        if node.name.startswith("_"):
            return False

        # 检查__all__变量
        for item in ast.walk(tree):
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(item.value, ast.List):
                            # 检查是否在__all__中
                            for elt in item.value.elts:
                                if isinstance(elt, ast.Constant) and elt.value == node.name:
                                    return True
                            # 如果__all__存在但未包含，则为私有
                            return False

        return True

    def generate_markdown(self, output_path: Path):
        """生成Markdown文档

        Args:
            output_path: 输出文件路径
        """
        # 按模块分组
        modules = {}
        for api_name, api_info in self.api_registry.items():
            module_name = api_info["module"]
            if module_name not in modules:
                modules[module_name] = {"classes": [], "functions": []}

            if api_info["type"] == "class":
                modules[module_name]["classes"].append(api_info)
            else:
                modules[module_name]["functions"].append(api_info)

        # 生成Markdown
        markdown_lines = [
            "# 公共API参考\n",
            "本文档由自动工具生成，包含系统中所有公共API。\n",
            f"生成时间: {os.popen('date').read().strip()}\n",
            f"总计: {len(self.api_registry)} 个API\n",
            "---",
            "",
        ]

        # 生成目录
        markdown_lines.extend(["## 目录", ""])
        for module_name in sorted(modules.keys()):
            class_count = len(modules[module_name]["classes"])
            func_count = len(modules[module_name]["functions"])
            markdown_lines.append(
                f"- [{module_name}](#{module_name.replace('.', '-')}) "
                f"({class_count} 类, {func_count} 函数)"
            )
        markdown_lines.append("")

        # 生成详细文档
        for module_name in sorted(modules.keys()):
            markdown_lines.extend(
                [
                    f"## {module_name}",
                    "",
                ]
            )

            # 类文档
            if modules[module_name]["classes"]:
                markdown_lines.extend(["### 类", ""])
                for class_info in sorted(
                    modules[module_name]["classes"], key=lambda x: x["name"]
                ):
                    markdown_lines.extend(
                        [
                            f"#### {class_info['name']}",
                            "",
                        ]
                    )

                    if class_info["docstring"]:
                        markdown_lines.extend(
                            [
                                f"```",
                                textwrap.indent(class_info["docstring"], "    "),
                                f"```",
                                "",
                            ]
                        )

                    if class_info["bases"]:
                        markdown_lines.append(
                            f"**继承:** {', '.join(class_info['bases'])}"
                        )

                    if class_info["methods"]:
                        markdown_lines.append("\n**方法:**")
                        for method in class_info["methods"]:
                            args_str = ", ".join(method["args"])
                            return_str = f" -> {method['returns']}" if method["returns"] else ""
                            markdown_lines.append(
                                f"- `{method['name']}({args_str}){return_str}`"
                            )
                            if method["docstring"]:
                                markdown_lines.append(
                                    f"  - {method['docstring'][:100]}..."
                                )
                        markdown_lines.append("")

            # 函数文档
            if modules[module_name]["functions"]:
                markdown_lines.extend(["### 函数", ""])
                for func_info in sorted(
                    modules[module_name]["functions"], key=lambda x: x["name"]
                ):
                    markdown_lines.extend(
                        [
                            f"#### {func_info['name']}",
                            "",
                        ]
                    )

                    args_str = ", ".join(func_info["args"])
                    return_str = f" -> {func_info['returns']}" if func_info["returns"] else ""
                    markdown_lines.append(
                        f"```python\n{func_info['name']}({args_str}){return_str}\n```"
                    )

                    if func_info["docstring"]:
                        markdown_lines.extend(
                            [
                                "",
                                "```",
                                textwrap.indent(func_info["docstring"], "    "),
                                "```",
                                "",
                            ]
                        )

            markdown_lines.extend(["---", ""])

        # 保存文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(markdown_lines))

        print(f"✅ 公共API文档已保存到: {output_path}")

    def generate_rst(self, output_path: Path):
        """生成RST文档

        Args:
            output_path: 输出文件路径
        """
        # 类似Markdown，但使用reStructuredText格式
        # 这里简化实现
        self.generate_markdown(output_path.with_suffix(".md"))

    def run(self, output_dir: Path):
        """运行扫描

        Args:
            output_dir: 输出目录
        """
        print("\n" + "=" * 60)
        print("🔍 扫描公共API")
        print("=" * 60 + "\n")

        # 扫描所有源代码目录
        all_files = []
        for source_dir in self.source_dirs:
            if source_dir.exists():
                print(f"🔍 扫描目录: {source_dir}")
                files = self.scan_directory(source_dir)
                all_files.extend(files)
                print(f"   发现 {len(files)} 个Python文件")

        # 处理文件
        print(f"\n🔄 处理 {len(all_files)} 个文件...")
        for i, file_path in enumerate(all_files, 1):
            print(f"   [{i}/{len(all_files)}] {file_path}")
            self.process_module(file_path)

        print(f"\n✅ 扫描完成，发现 {len(self.api_registry)} 个公共API")

        # 生成文档
        print("\n📝 生成文档...")
        self.generate_markdown(output_dir / "public_apis.md")
        self.generate_rst(output_dir / "public_apis.rst")

        # 生成JSON格式
        json_path = output_dir / "public_apis.json"
        import json

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(
                self.api_registry,
                f,
                ensure_ascii=False,
                indent=2,
            )

        print(f"✅ JSON文档已保存到: {json_path}")


def main():
    """主函数"""
    import os

    # 添加项目根目录到路径
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # 定义源代码目录
    source_dirs = [
        str(project_root / "src"),
    ]

    # 输出目录
    output_dir = project_root / "docs" / "api" / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 创建生成器并运行
    generator = PublicAPIDocGenerator(source_dirs)
    generator.run(output_dir)

    print("\n" + "=" * 60)
    print("✅ 公共API文档生成完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
