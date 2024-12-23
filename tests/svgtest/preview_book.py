import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = str(Path(__file__).parent.parent.parent)
sys.path.insert(0, project_root)

from services.book_svg_service import BookSVGService, ContentType

def save_svg(svg_content: str, filename: str, output_dir: str = "tests/svgtest/output"):
    """保存SVG文件"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(svg_content)
    print(f"已生成: {filepath}")

def main():
    service = BookSVGService()
    
    # 生成章节页（如图3）
    chapter_svgs = service.generate_svg(
        number="Chapter 6",
        title="篮球",
        is_chapter=True
    )
    save_svg(chapter_svgs[0], "chapter.svg")
    
    # 生成小节页面（如图1和图2）
    content = """从小，我就对篮球充满了热情。无论是在学校的操场上，还是在社区的篮球场，我都乐此不疲地挥洒汗水。每当我面对高年级的队伍时，心中既紧张又兴奋。那些比赛让我体验到了胜利的喜悦和失败的失落。每一次的胜利都让我感到无比自豪，而每一次的失败则让我更加坚定地追求进步。

篮球不仅仅是一项运动，它更是一种团队协作的艺术。在训练中，我不仅提升了自己的球技，还学会了与队友默契配合的重要性。我们在场上相互信任、彼此支持，这种感觉让我倍感温暖。每次热身比赛都是一次宝贵的机会，我们通过不断的练习，逐渐形成了默契的配合。回想起那些时光，我总能感受到那种团结的力量。

在这些年里，我经历了许多起伏。记得有一次，我们在决赛中输给了对手，心中的失落无以言表。然而，正是这次失败让我明白了坚持的重要性。篮球教会了我，人生的每一步都需要勇气和努力。即使在面对挫折时，我也会想起在球场上学到的那些珍贵经验，激励自己坚持不懈地追求目标。

从小，我就对篮球充满了热情。无论是在学校的操场上，还是在社区的篮球场，我都乐此不疲地挥洒汗水。每当我面对高年级的队伍时，心中既紧张又兴奋。那些比赛让我体验到了胜利的喜悦和失败的失落。每一次的胜利都让我感到无比自豪，而每一次的失败则让我更加坚定地追求进步。

篮球不仅仅是一项运动，它更是一种团队协作的艺术。在训练中，我不仅提升了自己的球技，还学会了与队友默契配合的重要性。我们在场上相互信任、彼此支持，这种感觉让我倍感温暖。每次热身比赛都是一次宝贵的机会，我们通过不断的练习，逐渐形成了默契的配合。回想起那些时光，我总能感受到那种团结的力量。

在这些年里，我经历了许多起伏。记得有一次，我们在决赛中输给了对手，心中的失落无以言表。然而，正是这次失败让我明白了坚持的重要性。篮球教会了我，人生的每一步都需要勇气和努力。即使在面对挫折时，我也会想起在球场上学到的那些珍贵经验，激励自己坚持不懈地追求目标。
"""

    section_svgs = service.generate_svg(
        number="第3节",
        title="家里祭拜",
        content=content
    )
    
    for i, svg in enumerate(section_svgs):
        save_svg(svg, f"section_page_{i+1}.svg")

if __name__ == "__main__":
    main() 