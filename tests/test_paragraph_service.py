import pytest
from services.paragraph_service import ParagraphService
from services.narrative_service import NarrativeService
from entities.narrative import Narrative
from entities.paragraph import Paragraph
from entities.tag import Tag

@pytest.fixture
def paragraph_service(db_session):
    """创建段落服务，并注入会话"""
    service = ParagraphService()
    service._session = db_session
    return service

@pytest.fixture
def narrative_with_session(db_session):
    """创建一个测试用的叙事体"""
    narrative = Narrative(
        session_id="test_session",
        content="测试叙事体"
    )
    db_session.add(narrative)
    db_session.flush()
    return narrative

def test_paragraph_crud(paragraph_service, narrative_with_session, db_session):
    """测试段落的CRUD操作"""
    # 创建段落
    paragraph = Paragraph(
        narrative_id=narrative_with_session.id,
        content="测试段落",
        sequence_number=1,
        paragraph_type="事实描述"
    )
    
    # 直接使用 service 创建
    created = paragraph_service.create(paragraph)
    assert created.id is not None
    
    # 读取
    retrieved = db_session.get(Paragraph, created.id)
    assert retrieved is not None
    assert retrieved.content == "测试段落"
    assert retrieved.paragraph_type == "事实描述"
    
    # 更新
    retrieved.content = "更新后的段落"
    updated = paragraph_service.update(retrieved)
    assert updated.content == "更新后的段落"
    
    # 删除
    assert paragraph_service.delete(created.id) is True

def test_get_paragraphs_by_narrative(paragraph_service, narrative_with_session, db_session):
    """测试获取叙事体的所有段落"""
    # 创建多个段落
    paragraphs = [
        Paragraph(
            narrative_id=narrative_with_session.id,
            content=f"段落{i}",
            sequence_number=i,
            paragraph_type="事实描述"
        )
        for i in range(1, 4)
    ]
    
    # 直接使用 service 创建
    for p in paragraphs:
        paragraph_service.create(p)
    
    # 获取所有段落
    retrieved = paragraph_service.get_by_narrative(narrative_with_session.id)
    assert len(retrieved) == 3
    assert retrieved[0].sequence_number == 1
    assert retrieved[2].content == "段落3"

def test_get_paragraphs_by_type(paragraph_service, narrative_with_session, db_session):
    """测试按类型获取段落"""
    # 创建不同类型的段落
    paragraphs = [
        Paragraph(
            narrative_id=narrative_with_session.id,
            content="事实段落",
            sequence_number=1,
            paragraph_type="事实描述"
        ),
        Paragraph(
            narrative_id=narrative_with_session.id,
            content="情感段落",
            sequence_number=2,
            paragraph_type="情感表达"
        )
    ]
    
    for p in paragraphs:
        db_session.add(p)
    db_session.flush()
    
    # 按类型查询
    fact_paragraphs = paragraph_service.get_by_type("事实描述")
    emotion_paragraphs = paragraph_service.get_by_type("情感表达")
    
    assert len(fact_paragraphs) == 1
    assert len(emotion_paragraphs) == 1
    assert fact_paragraphs[0].content == "事实段落"
    assert emotion_paragraphs[0].content == "情感段落" 