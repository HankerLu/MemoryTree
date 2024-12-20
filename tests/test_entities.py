from datetime import datetime
from entities.dialogue import Dialogue
from entities.narrative import Narrative
from entities.paragraph import Paragraph
from entities.tag import Tag

def test_dialogue_creation(db_session):
    """测试对话记录的创建"""
    dialogue = Dialogue(
        session_id="test_session",
        role="user",
        content="测试内容",
        sequence_number=1
    )
    db_session.add(dialogue)
    db_session.commit()

    saved_dialogue = db_session.query(Dialogue).first()
    assert saved_dialogue.session_id == "test_session"
    assert saved_dialogue.role == "user"
    assert saved_dialogue.content == "测试内容"
    assert saved_dialogue.sequence_number == 1

def test_narrative_with_paragraphs(db_session):
    """测试叙事体和段落的关联关系"""
    narrative = Narrative(
        session_id="test_session",
        content="测试叙事体"
    )
    
    paragraph1 = Paragraph(
        content="第一段",
        sequence_number=1,
        paragraph_type="事实描述"
    )
    
    paragraph2 = Paragraph(
        content="第二段",
        sequence_number=2,
        paragraph_type="情感表达"
    )
    
    narrative.paragraphs.extend([paragraph1, paragraph2])
    db_session.add(narrative)
    db_session.commit()

    saved_narrative = db_session.query(Narrative).first()
    assert len(saved_narrative.paragraphs) == 2
    assert saved_narrative.paragraphs[0].content == "第一段"
    assert saved_narrative.paragraphs[1].paragraph_type == "情感表达"

def test_paragraph_tags(db_session):
    """测试段落和标签的多对多关系"""
    # 先创建叙事体
    narrative = Narrative(
        session_id="test_session",
        content="测试叙事体"
    )
    db_session.add(narrative)
    db_session.flush()  # 获取narrative.id
    
    # 创建段落
    paragraph = Paragraph(
        narrative_id=narrative.id,  # 使用刚创建的叙事体ID
        content="测试段落",
        sequence_number=1,
        paragraph_type="事实描述"
    )
    
    # 创建标签
    tag1 = Tag(dimension="时间维度", tag_value="2024年")
    tag2 = Tag(dimension="情感维度", tag_value="开心")
    
    # 建立关联
    paragraph.tags.extend([tag1, tag2])
    db_session.add(paragraph)
    db_session.add_all([tag1, tag2])
    db_session.commit()

    # 验证
    saved_paragraph = db_session.query(Paragraph).first()
    assert len(saved_paragraph.tags) == 2
    assert saved_paragraph.tags[0].dimension == "时间维度"
    assert saved_paragraph.tags[1].tag_value == "开心" 