from rapidfuzz import fuzz, process
from typing import List, Tuple


class SmartSearch:
    def __init__(self, threshold: int = 50):
        self.threshold = threshold

        # Словарь синонимов для улучшения поиска
        self.synonyms = {
            'стипендия': ['выплата', 'деньги', 'оплата', 'получить деньги'],
            'общежитие': ['общага', 'жильё', 'комната', 'заселение', 'проживание'],
            'библиотека': ['книги', 'учебники', 'читалка', 'литература'],
            'студенческий билет': ['студак', 'билет', 'пропуск'],
            'деканат': ['декан', 'учебная часть'],
            'расписание': ['пары', 'занятия', 'уроки'],
            'экзамен': ['сессия', 'зачёт', 'тест'],
            'справка': ['документ', 'бумага'],
        }

    def expand_query(self, query: str) -> List[str]:
        """Расширяет запрос синонимами"""
        query_lower = query.lower()
        expanded = [query_lower]

        for key, synonyms in self.synonyms.items():
            if key in query_lower:
                expanded.extend(synonyms)
            for syn in synonyms:
                if syn in query_lower:
                    expanded.append(key)
                    expanded.extend(synonyms)
                    break

        return list(set(expanded))

    def search(self, query: str, items: List[Tuple[str, str, str]]) -> List[dict]:
        """
        Поиск по FAQ с нечётким совпадением.

        Args:
            query: Поисковый запрос пользователя
            items: Список кортежей (question, answer, category) из БД

        Returns:
            Список словарей с результатами, отсортированных по релевантности
        """
        if not items:
            return []

        query_lower = query.lower()
        expanded_queries = self.expand_query(query)

        # Собираем результаты с разными алгоритмами
        scored_items = []

        for idx, item in enumerate(items):
            question = item[0]
            answer = item[1]
            category = item[2]

            max_score = 0

            # Проверяем оригинальный запрос и все синонимы
            for q in expanded_queries:
                scores = []

                # 1. Token set ratio - игнорирует порядок слов
                scores.append(fuzz.token_set_ratio(q, question.lower()))

                # 2. Partial ratio - ищет подстроки
                scores.append(fuzz.partial_ratio(q, question.lower()))

                # 3. Token sort ratio - учитывает все слова
                scores.append(fuzz.token_sort_ratio(q, question.lower()))

                # 4. Поиск по ответу (с меньшим весом)
                answer_score = fuzz.partial_ratio(q, answer.lower()) * 0.7
                scores.append(answer_score)

                # 5. Поиск по категории
                if category:
                    category_score = fuzz.partial_ratio(q, category.lower()) * 0.6
                    scores.append(category_score)

                max_score = max(max_score, max(scores))

            if max_score >= self.threshold:
                scored_items.append({
                    "question": question,
                    "answer": answer,
                    "category": category,
                    "score": max_score,
                    "idx": idx
                })

        # Сортируем по score (от большего к меньшему)
        scored_items.sort(key=lambda x: x["score"], reverse=True)

        # Возвращаем топ-5
        return scored_items[:5]

    def find_best_match(self, query: str, items: List[Tuple[str, str, str]]) -> dict:
        """Возвращает лучшее совпадение или None"""
        results = self.search(query, items)
        return results[0] if results else None
