import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import longmemeval_pipeline as P  # noqa: E402

LLM = "llm@rev"


def entry(opening: bool) -> dict:
    """One question, one evidence session; with `opening` the session starts with an assistant turn."""
    sess = [{"role": "user", "content": "user one has_answer", "has_answer": True},
            {"role": "assistant", "content": "assistant reply one"},
            {"role": "user", "content": "user two", "has_answer": False},
            {"role": "assistant", "content": "assistant reply two"}]
    if opening:
        sess = [{"role": "assistant", "content": "opening assistant turn", "has_answer": False}] + sess
    filler = [{"role": "user", "content": "filler user", "has_answer": False},
              {"role": "assistant", "content": "filler reply"}]
    return {"question_id": "q0", "question_type": "multi-session", "question": "what?", "answer": "x",
            "question_date": "2023/06/01 (Thu) 09:00", "haystack_session_ids": ["answer_s1", "sharegpt_s2"],
            "haystack_dates": ["2023/05/10 (Wed) 09:00", "2023/05/11 (Thu) 09:00"],
            "haystack_sessions": [sess, filler], "answer_session_ids": ["answer_s1"]}


def load(e: dict) -> P.Question:
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "data.json"
        f.write_text(json.dumps([e]))
        return P.load(f)[0]


class OpeningUnit(unittest.TestCase):
    def test_opening_assistant_turn_is_its_own_unit_with_its_own_content(self):
        s = load(entry(opening=True)).sessions[0]
        self.assertEqual(s.opening_tid, "noans_s1_1")  # the opening turn has no answer, so it carries noans
        self.assertEqual(s.turns[0], ("noans_s1_1", "", "opening assistant turn"))
        self.assertEqual([t[0] for t in s.turns], ["noans_s1_1", "answer_s1_2", "noans_s1_4"])
        keys = {(k, tid): text for k, text, tid, _ in P.build_keys(load(entry(True)), ["turn", "turn_exp", "round"], {}, LLM)}
        self.assertEqual(keys[("turn", "noans_s1_1")], "opening assistant turn")
        self.assertEqual(keys[("turn_exp", "noans_s1_1")], "opening assistant turn")
        self.assertEqual(keys[("round", "noans_s1_1")], "assistant: opening assistant turn")
        self.assertEqual(keys[("turn", "answer_s1_2")], "user one has_answer")

    def test_opening_unit_with_the_answer_keeps_the_answer_marker(self):
        e = entry(opening=True)
        e["haystack_sessions"][0][0]["has_answer"] = True
        q = load(e)
        self.assertEqual(q.sessions[0].opening_tid, "answer_s1_1")
        self.assertTrue(q.scored)

    def test_session_text_and_fact_input_ignore_the_opening_unit(self):
        with_open, without = load(entry(True)).sessions[0], load(entry(False)).sessions[0]
        self.assertEqual(with_open.user_text, without.user_text)
        self.assertEqual(with_open.fact_input(), without.fact_input())
        self.assertEqual(P.fact_key(with_open, LLM), P.fact_key(without, LLM))
        self.assertEqual(with_open.user_turns, [t for t in with_open.turns if t[1]])

    def test_fact_turn_numbers_map_to_user_turns_past_the_opening_unit(self):
        s = load(entry(True)).sessions[0]
        facts = {P.fact_key(s, LLM): {"facts": [{"turn": 1, "fact": "first"}, {"turn": 2, "fact": "second"},
                                                {"turn": 3, "fact": "out of range"}]}}
        self.assertEqual(P.session_facts(s, facts, LLM), [(1, "first"), (2, "second"), (-1, "out of range")])
        keys = {(k, tid): text for k, text, tid, _ in P.build_keys(load(entry(True)), ["turn_exp"], facts, LLM)}
        self.assertEqual(keys[("turn_exp", "answer_s1_2")], "first user one has_answer")
        self.assertEqual(keys[("turn_exp", "noans_s1_1")], "opening assistant turn")

    def test_exported_id_resolves_in_the_official_round_rule(self):
        e = entry(opening=True)
        q = load(e)
        exported = P.export_rankings({"q0": [q.sessions[0].opening_tid]})["q0"]
        self.assertEqual(exported, ["answer_s1_1"])
        sessions = dict(zip(e["haystack_session_ids"], e["haystack_sessions"]))
        sid, _, num = exported[0].rpartition("_")  # the QA loader's check: 1 <= n <= len(session)
        self.assertTrue(sid in sessions and 1 <= int(num) <= len(sessions[sid]))
        turn = int(num) - 1
        self.assertEqual([t["role"] for t in sessions[sid][turn:turn + 2]], ["assistant", "user"])

    def test_blinded_copy_keeps_the_opening_unit(self):
        q = load(entry(True))
        bq, fwd, back = P.blind_question(q)
        self.assertEqual(back[bq.sessions[0].opening_tid or bq.sessions[1].opening_tid], "noans_s1_1")
        self.assertEqual(sum(s.opening_tid is not None for s in bq.sessions), 1)

    def test_assistant_only_session_has_a_turn_unit_but_no_session_key(self):
        e = entry(opening=True)
        e["haystack_sessions"][0] = e["haystack_sessions"][0][:1]
        q = load(e)
        self.assertEqual(q.sessions[0].turns, [("noans_s1_1", "", "opening assistant turn")])
        keys = [(k, tid, sid) for k, _, tid, sid in P.build_keys(q, ["turn", "session"], {}, LLM) if sid == "noans_s1"]
        self.assertEqual(keys, [("turn", "noans_s1_1", "noans_s1")])

    def test_user_first_sessions_are_unchanged(self):
        q = load(entry(False))
        self.assertTrue(all(s.opening_tid is None for s in q.sessions))
        self.assertEqual([t[0] for t in q.sessions[0].turns], ["answer_s1_1", "noans_s1_3"])


if __name__ == "__main__":
    unittest.main()
