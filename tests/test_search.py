from utils.search import SmartSearch

ITEMS = [
    ("Как получить стипендию?", "Стипендия назначается по итогам сессии.", "Стипендии"),
    ("Как записаться в общежитие?", "Подайте заявление в отдел общежитий.", "Общежитие"),
    ("Где находится библиотека?", "Библиотека в корпусе Б, 1 этаж.", "Библиотека"),
]


def test_exact_question_is_top_result():
    result = SmartSearch(threshold=50).find_best_match("Где находится библиотека?", ITEMS)
    assert result["question"] == "Где находится библиотека?"


def test_synonym_expansion():
    engine = SmartSearch(threshold=50)
    assert "общежитие" in engine.expand_query("где общага")
    best = engine.find_best_match("общага", ITEMS)
    assert best is not None and best["category"] == "Общежитие"


def test_typo_tolerance():
    best = SmartSearch(threshold=50).find_best_match("стипендея", ITEMS)
    assert best is not None and best["category"] == "Стипендии"


def test_no_items_and_garbage_query():
    engine = SmartSearch(threshold=70)
    assert engine.search("что угодно", []) == []
    assert engine.find_best_match("zzzzqqqq", ITEMS) is None


def test_results_limited_and_sorted():
    results = SmartSearch(threshold=0).search("студент", ITEMS * 5)
    assert len(results) <= 5
    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)
