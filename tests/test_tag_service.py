import pytest
from services.tag_service import TagService
from services.paragraph_service import ParagraphService
from entities.tag import Tag
from entities.paragraph import Paragraph
from entities.narrative import Narrative

@pytest.fixture
def tag_service(db_session):
    """创建标签服务，并注入会话"""
    service = TagService()
    service._session = db_session
    return service

@pytest.fixture
def paragraph_service(db_session):
    """创建段落服务，并注入会话"""
    service = ParagraphService()
    service._session = db_session
    return service

def test_tag_crud(tag_service, db_session):
    """测试标签的CRUD操作"""
    # 创建
    tag = Tag(
        dimension="时间维度",
        tag_value="2024年"
    )
    
    # 直接使用 service 创建
    created = tag_service.create(tag)
    assert created.id is not None
    
    # 读取
    retrieved = db_session.get(Tag, created.id)
    assert retrieved is not None
    assert retrieved.dimension == "时间维度"
    assert retrieved.tag_value == "2024年"
    
    # 更新
    retrieved.tag_value = "2025年"
    updated = tag_service.update(retrieved)
    assert updated.tag_value == "2025年"
    
    # 删除
    assert tag_service.delete(created.id) is True

def test_get_tags_by_dimension(tag_service, db_session):
    """测试按维度获取标签"""
    # 创建不同维度的标签
    tags = [
        Tag(dimension="时间维度", tag_value="2024年"),
        Tag(dimension="时间维度", tag_value="2025年"),
        Tag(dimension="情感维度", tag_value="开心")
    ]
    
    # 直接使用 service 创建
    for t in tags:
        tag_service.create(t)
    
    # 按维度查询
    time_tags = tag_service.get_by_dimension("时间维度")
    emotion_tags = tag_service.get_by_dimension("情感维度")
    
    assert len(time_tags) == 2
    assert len(emotion_tags) == 1
    assert time_tags[0].tag_value == "2024年"
    assert emotion_tags[0].tag_value == "开心"

def test_paragraph_tag_relationship(tag_service, paragraph_service, db_session):
    """测试段落和标签的多对多关系"""
    # 创建叙事体
    narrative = Narrative(
        session_id="test_session",
        content="测试叙事体"
    )
    db_session.add(narrative)
    db_session.flush()
    
    # 创建段落
    paragraph = Paragraph(
        narrative_id=narrative.id,
        content="测试段落",
        sequence_number=1,
        paragraph_type="事实描述"
    )
    db_session.add(paragraph)
    db_session.flush()
    
    # 创建标签
    tags = [
        Tag(dimension="时间维度", tag_value="2024年"),
        Tag(dimension="情感维度", tag_value="开心"),
        Tag(dimension="场景维度", tag_value="家里")
    ]
    
    # 使用 service 创建标签
    created_tags = [tag_service.create(t) for t in tags]
    
    # 建立关联
    paragraph.tags.extend(created_tags)
    db_session.flush()
    
    # 验证关联关系
    retrieved_paragraph = db_session.get(Paragraph, paragraph.id)
    assert len(retrieved_paragraph.tags) == 3
    
    # 通过段落获取标签
    paragraph_tags = tag_service.get_by_paragraph(paragraph.id)
    assert len(paragraph_tags) == 3
    assert any(t.tag_value == "2024年" for t in paragraph_tags)
    assert any(t.dimension == "情感维度" for t in paragraph_tags)
    
    # 测试删除标签
    tag_service.delete(created_tags[0].id)  # 使用 service 删除
    db_session.flush()
    db_session.refresh(retrieved_paragraph)  # 刷新对象状态
    
    # 验证关联关系更新
    assert len(retrieved_paragraph.tags) == 2