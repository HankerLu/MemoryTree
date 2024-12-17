class Tag:
    def __init__(self, name, parent=None):
        self.name = name
        self.parent = parent
        self.children = []
        self.content = []  # 存储该标签下的回忆内容片段
        
    def add_child(self, child):
        self.children.append(child)
        child.parent = self
        
    def add_content(self, memory_fragment):
        self.content.append(memory_fragment)
        
    def get_path(self):
        """获取从根节点到当前节点的完整路径"""
        if self.parent is None:
            return [self.name]
        return self.parent.get_path() + [self.name] 