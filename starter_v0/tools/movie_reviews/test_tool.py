from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from tools.movie_reviews.tool import search_movie_reviews


def _search_response(movies: list[dict]) -> dict:
    return {"results": movies}


def _reviews_response(reviews: list[dict]) -> dict:
    return {"results": reviews}


def _fake_get(search_response: dict, reviews_response: dict | None = None):
    def handler(url, **kwargs):
        response = MagicMock()
        response.raise_for_status.return_value = None
        response.json.return_value = reviews_response if "/reviews" in url else search_response
        return response

    return handler


@patch.dict(os.environ, {"TMDB_API_KEY": "fake-key"})
class MovieReviewsTests(unittest.TestCase):
    def test_empty_query_returns_error_payload(self):
        result = search_movie_reviews("")
        self.assertEqual(result["tool"], "movie_reviews")
        self.assertIn("error", result)

    def test_missing_api_key_returns_error_payload(self):
        with patch.dict(os.environ, {"TMDB_API_KEY": ""}):
            result = search_movie_reviews("Dune")
            self.assertEqual(result["tool"], "movie_reviews")
            self.assertIn("error", result)

    @patch("tools.movie_reviews.tool.requests.get")
    def test_returns_movie_and_reviews(self, mock_get):
        mock_get.side_effect = _fake_get(
            _search_response([{"id": 438631, "title": "Dune", "release_date": "2021-10-22", "vote_average": 7.8, "vote_count": 12000, "overview": "..."}]),
            _reviews_response([{
                "author": "alice",
                "content": "Great adaptation of the book.",
                "author_details": {"rating": 9},
                "url": "https://www.themoviedb.org/review/abc",
                "created_at": "2021-10-23T00:00:00.000Z",
            }]),
        )

        result = search_movie_reviews("Dune")

        self.assertEqual(result["movie"]["title"], "Dune")
        self.assertEqual(result["movie"]["tmdb_id"], 438631)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0]["author"], "alice")
        self.assertEqual(result["items"][0]["rating"], 9)
        self.assertEqual(result["items"][0]["date"], "2021-10-23")

    @patch("tools.movie_reviews.tool.requests.get")
    def test_no_movie_found_returns_empty_items(self, mock_get):
        mock_get.side_effect = _fake_get(_search_response([]))

        result = search_movie_reviews("asdkjqwoezxpv nonsense title")

        self.assertIsNone(result["movie"])
        self.assertEqual(result["items"], [])
        # Reviews endpoint should never be queried when no movie matched.
        mock_get.assert_called_once()

    @patch("tools.movie_reviews.tool.requests.get")
    def test_max_results_is_respected(self, mock_get):
        many_reviews = [{"author": f"user{i}", "content": "ok"} for i in range(10)]
        mock_get.side_effect = _fake_get(
            _search_response([{"id": 1, "title": "Some Movie"}]),
            _reviews_response(many_reviews),
        )

        result = search_movie_reviews("Some Movie", max_results=3)

        self.assertEqual(len(result["items"]), 3)


if __name__ == "__main__":
    unittest.main()
