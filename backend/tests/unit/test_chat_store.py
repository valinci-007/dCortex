"""Persistent conversations: create, title, append, list order, exchanges, rename, delete."""

from crew_ops_advisor.chats import ChatStore, title_from


def test_title_from_first_question():
    assert title_from("Who's on reserve at BLR tomorrow?") == "Who's on reserve at BLR tomorrow?"
    long = "Captain C-1042 calls in sick at 05:00Z on 15 Sep for pairing P-2291 which flights are uncrewed"
    t = title_from(long)
    assert t.endswith("…") and len(t) <= 61 and not t[:-1].endswith(" ")
    assert title_from("   ") == "New chat"


def test_store_round_trip(tmp_path):
    store = ChatStore(tmp_path / "chats.db")
    chat = store.create(provider="offline")
    assert chat.title == "New chat" and chat.message_count == 0 and chat.session_id is None

    store.append(chat.id, "user", "Who is on reserve at BLR tomorrow?")
    store.append(
        chat.id, "assistant", "12 reserves …", answer={"answer": "12 reserves …", "mode": "offline"}
    )
    got = store.get(chat.id)
    assert got.title == "Who is on reserve at BLR tomorrow?" and got.message_count == 2

    msgs = store.messages(chat.id)
    assert [m.role for m in msgs] == ["user", "assistant"]
    assert msgs[1].answer["mode"] == "offline" and msgs[0].answer is None
    assert store.exchanges(chat.id) == [("Who is on reserve at BLR tomorrow?", "12 reserves …")]

    store.set_session(chat.id, "sess-42")
    assert store.get(chat.id).session_id == "sess-42"

    other = store.create(provider="offline")
    store.append(other.id, "user", "later question")
    assert [c.id for c in store.list()] == [other.id, chat.id]  # most recently updated first

    assert store.rename(chat.id, "Reserves").title == "Reserves"
    assert store.delete(chat.id) and store.get(chat.id) is None and store.messages(chat.id) == []
    assert not store.delete(chat.id)
    store.close()


def test_store_survives_reopen(tmp_path):
    path = tmp_path / "chats.db"
    s1 = ChatStore(path)
    chat = s1.create(provider="agent-sdk")
    s1.append(chat.id, "user", "q1")
    s1.append(chat.id, "assistant", "a1", answer={"answer": "a1"})
    s1.set_session(chat.id, "sess-1")
    s1.close()

    s2 = ChatStore(path)
    got = s2.get(chat.id)
    assert got is not None and got.session_id == "sess-1" and got.message_count == 2
    assert s2.exchanges(chat.id) == [("q1", "a1")]
    s2.close()
