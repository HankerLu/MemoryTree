import requests
import json
import os
import webbrowser
from pathlib import Path

class SVGAPITester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.output_dir = "tests/svgtest/output"
        
        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
    
    def generate_svg(self, number: str, title: str, content: str = None, is_chapter: bool = False):
        """调用SVG生成API"""
        url = f"{self.base_url}/generate/svg"
        
        # 准备请求数据
        data = {
            "number": number,
            "title": title,
            "content": content,
            "is_chapter": is_chapter
        }
        
        try:
            # 发送POST请求
            response = requests.post(url, json=data)
            response.raise_for_status()  # 检查响应状态
            
            # 解析响应
            result = response.json()
            print(f"生成了 {result['page_count']} 页SVG")
            
            # 保存并显示SVG
            self._save_and_view_svgs(result['pages'])
            
        except requests.exceptions.RequestException as e:
            print(f"API请求失败: {e}")
            if hasattr(e.response, 'text'):
                print(f"错误详情: {e.response.text}")
        except Exception as e:
            print(f"发生错误: {e}")
    
    def _save_and_view_svgs(self, svg_contents: list):
        """保存并在浏览器中查看SVG文件"""
        for i, svg_content in enumerate(svg_contents):
            # 保存SVG文件
            filename = f"page_{i+1}.svg"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            print(f"SVG已保存到: {filepath}")
            
            # 在浏览器中打开SVG
            # webbrowser.open(f'file://{os.path.abspath(filepath)}')

def main():
    # 创建测试器实例
    tester = SVGAPITester()
    
    # 测试章节页面
    print("\n测试生成章节页面:")
    tester.generate_svg(
        number="Chapter 6",
        title="篮球",
        is_chapter=True
    )
    
    # 测试小节页面
    print("\n测试生成小节页面:")
    content = """从小，我就对篮球充满了热情。无论是在学校的操场上，还是在社区的篮球场，我都乐此不疲地挥洒汗水。每当我面对高年级的队伍时，心中既紧张又兴奋。那些比赛让我体验到了胜利的喜悦和失败的失落。每一次的胜利都让我感到无比自豪，而每一次的失败则让我更加坚定地追求进步。

篮球不仅仅是一项运动，它更是一种团队协作的艺术。在训练中，我不仅提升了自己的球技，还学会了与队友默契配合的重要性。我们在场上相互信任、彼此支持，这种感觉让我倍感温暖。每次热身比赛都是一次宝贵的机会，我们通过不断的练习，逐渐形成了默契的配合。回想起那些时光，我总能感受到那种团结的力量。

在这些年里，我经历了许多起伏。记得有一次，我们在决赛中输给了对手，心中的失落无以言表。然而，正是这次失败让我明白了坚持的重要性。篮球教会了我，人生的每一步都需要勇气和努力。即使在面对挫折时，我也会想起在球场上学到的那些珍贵经验，激励自己坚持不懈地追求目标。

从小，我就对篮球充满了热情。无论是在学校的操场上，还是在社区的篮球场，我都乐此不疲地挥洒汗水。每当我面对高年级的队伍时，心中既紧张又兴奋。那些比赛让我体验到了胜利的喜悦和失败的失落。每一次的胜利都让我感到无比自豪，而每一次的失败则让我更加坚定地追求进步。

篮球不仅仅是一项运动，它更是一种团队协作的艺术。在训练中，我不仅提升了自己的球技，还学会了与队友默契配合的重要性。我们在场上相互信任、彼此支持，这种感觉让我倍感温暖。每次热身比赛都是一次宝贵的机会，我们通过不断的练习，逐渐形成了默契的配合。回想起那些时光，我总能感受到那种团结的力量。

在这些年里，我经历了许多起伏。记得有一次，我们在决赛中输给了对手，心中的失落无以言表。然而，正是这次失败让我明白了坚持的重要性。篮球教会了我，人生的每一步都需要勇气和努力。即使在面对挫折时，我也会想起在球场上学到的那些珍贵经验，激励自己坚持不懈地追求目标。"""

    tester.generate_svg(
        number="第3节",
        title="家里祭拜",
        content=content,
        is_chapter=False
    )

if __name__ == "__main__":
    # 确保API服务器正在运行
    print("请确保已经启动了SVG API服务器 (svg_api_server.py)")
    input("按Enter键继续...")
    main() 