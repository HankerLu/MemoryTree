import pytest
from services.dialogue_service import DialogueService
from services.narrative_service import NarrativeService
from entities.dialogue import Dialogue
from entities.narrative import Narrative
from entities.paragraph import Paragraph
from entities.tag import Tag

@pytest.fixture
def dialogue_service(db_session):
    """创建对话服务，并注入会话"""
    service = DialogueService()
    service._session = db_session  # 注入会话
    return service

@pytest.fixture
def narrative_service(db_session):
    """创建叙事体服务，并注入会话"""
    service = NarrativeService()
    service._session = db_session  # 注入会话
    return service

def test_dialogue_service_crud(dialogue_service, db_session):
    """测试对话服务的CRUD操作"""
    with db_session.begin():
        # 创建
        dialogue = Dialogue(
            session_id="test_session",
            role="user",
            content="测试内容",
            sequence_number=1
        )
        
        db_session.add(dialogue)
        db_session.flush()  # 确保获取ID
        created = dialogue_service.create(dialogue)
        assert created.id is not None
        
        # 读取
        retrieved = db_session.get(Dialogue, created.id)
        assert retrieved is not None
        assert retrieved.content == "测试内容"

        # 更新
        retrieved.content = "更新的内容"
        updated = dialogue_service.update(retrieved)
        assert updated.content == "更新的内容"

        # 删除
        assert dialogue_service.delete(created.id) is True

def test_narrative_service_with_paragraphs(narrative_service, db_session):
    """测试叙事体服务的复杂操作"""
    with db_session.begin():
        # 创建叙事体和段落
        narrative = Narrative(
            session_id="test_session",
            content="测试叙事体"
        )
        
        db_session.add(narrative)
        created = narrative_service.create(narrative)

        # 添加段落
        paragraph = Paragraph(
            content="测试段落",
            sequence_number=1,
            paragraph_type="事实描述"
        )
        created.paragraphs.append(paragraph)
        
        # 更新
        updated = narrative_service.update(created)

        # 验证
        retrieved = db_session.get(Narrative, created.id)
        assert len(retrieved.paragraphs) == 1
        assert retrieved.paragraphs[0].content == "测试段落" 