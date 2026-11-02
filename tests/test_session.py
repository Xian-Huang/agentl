from agentl.session.SessionStore import Session, SessionStore
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


def test_sessionstro_list():
    store = SessionStore()
    session1 = Session()
    session2 = Session()
    store.save(session1)
    store.save(session2)

    sessions = store.list()
    print(store.list())
    assert any(s.id == session1.id for s in sessions)
    assert any(s.id == session2.id for s in sessions)

    # Clean up
    store.delete(session1)
    store.delete(session2)
