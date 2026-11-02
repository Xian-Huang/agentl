

from agentl.session.SessionStore import Session,SessionStore
import datetime


def test_session_creation():
    session = Session()
    assert session.id is not None
    assert isinstance(session.created_at, datetime.datetime)
    assert isinstance(session.updated_at, datetime.datetime)
    assert session.messages == []
    
    

def test_sessionstroe():
    store = SessionStore()
    session = Session()
    store.save(session)
    
    loaded_session = store.load(session.id)
    assert loaded_session.id == session.id
    assert loaded_session.created_at == session.created_at
    assert loaded_session.updated_at == session.updated_at
    assert loaded_session.messages == session.messages
    
    # Clean up
    store.delete(session)