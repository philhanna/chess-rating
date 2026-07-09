import json
import pytest
from unittest.mock import Mock

from rating.adapters.uscf import USCF, AmbiguousUSCFPlayerError
from rating.ports.http_port import HttpPort


class TestUSCFInitialization:
    """Tests for USCF class initialization."""

    def test_uscf_initialization_with_name(self):
        """Test that USCF initializes with the correct player name."""
        player = "John Doe"
        uscf = USCF(player)
        assert uscf.player == player, "Player name should be correctly stored."

    def test_uscf_initialization_with_integer(self):
        """Test that USCF initializes with an integer player ID."""
        player = 12345678
        uscf = USCF(player)
        assert str(uscf.player) == str(player), "Player ID should be stored and converted to string."


class TestUSCFGetURL:
    """Tests for USCF URL generation."""

    def test_uscf_get_url_basic(self):
        """Test that USCF generates the correct API URL for a simple player name."""
        player = "JohnDoe"
        uscf = USCF(player)
        expected_url = "https://ratings-api.uschess.org/api/v1/members/JohnDoe/sections"
        assert uscf.get_url() == expected_url, "URL should be correctly formatted."

    def test_uscf_get_url_with_spaces(self):
        """Test USCF URL generation with spaces in player name."""
        player = "John Doe"
        uscf = USCF(player)
        expected_url = "https://ratings-api.uschess.org/api/v1/members/John+Doe/sections"
        assert uscf.get_url() == expected_url, "Spaces should be URL-encoded as plus signs."

    def test_uscf_get_url_with_special_characters(self):
        """Test USCF URL generation with special characters in player name."""
        player = "John O'Malley"
        uscf = USCF(player)
        url = uscf.get_url()
        assert "https://ratings-api.uschess.org/api/v1/members/" in url
        assert "/sections" in url
        # Verify that special characters are URL-encoded
        assert "'" not in url, "Special characters should be URL-encoded."

    def test_uscf_get_url_with_hyphen(self):
        """Test USCF URL generation with hyphen in player name."""
        player = "Jean-Claude"
        uscf = USCF(player)
        url = uscf.get_url()
        assert "https://ratings-api.uschess.org/api/v1/members/Jean-Claude/sections" == url

    def test_uscf_get_url_with_ampersand(self):
        """Test USCF URL generation with ampersand character."""
        player = "Fish & Chips"
        uscf = USCF(player)
        url = uscf.get_url()
        assert "https://ratings-api.uschess.org/api/v1/members/" in url
        assert "/sections" in url
        assert "&" not in url, "Ampersand should be URL-encoded."

    def test_uscf_get_url_with_integer_player(self):
        """Test USCF URL generation with integer player ID."""
        player = 12345678
        uscf = USCF(player)
        expected_url = "https://ratings-api.uschess.org/api/v1/members/12345678/sections"
        assert uscf.get_url() == expected_url


class TestUSCFParseContent:
    """Tests for USCF JSON content parsing."""

    def test_parse_content_valid(self):
        """Test parsing valid USCF API JSON response."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2023-06-15",
                    "ratingRecords": [
                        {
                            "postRating": 1850
                        }
                    ]
                }
            ]
        })
        uscf = USCF("John Doe")
        result = uscf.parse_content(json_content)
        assert result.provider == "uscf"
        assert result.player.id == "John Doe"
        assert result.player.display_name == "John Doe"
        assert result.ratings["standard"] == 1850
        assert result.metadata.as_of == "2023-06-15"

    def test_parse_content_with_different_rating(self):
        """Test parsing JSON with different rating values."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2024-12-10",
                    "ratingRecords": [
                        {
                            "postRating": 2200
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Magnus Player")
        result = uscf.parse_content(json_content)
        assert result.ratings["standard"] == 2200
        assert result.metadata.as_of == "2024-12-10"

    def test_parse_content_with_very_high_rating(self):
        """Test parsing JSON with very high rating."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 2999
                        }
                    ]
                }
            ]
        })
        uscf = USCF("GrandMaster")
        result = uscf.parse_content(json_content)
        assert result.ratings["standard"] == 2999

    def test_parse_content_with_zero_rating(self):
        """Test parsing JSON with zero rating (unrated player)."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 0
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Unrated Player")
        result = uscf.parse_content(json_content)
        assert result.ratings["standard"] == 0

    def test_parse_content_with_special_characters_in_player_name(self):
        """Test parsing with special characters in player name."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1500
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Jean-Claude O'Brien")
        result = uscf.parse_content(json_content)
        assert result.player.id == "Jean-Claude O'Brien"
        assert result.player.display_name == "Jean-Claude O'Brien"


class TestUSCFParseContentErrors:
    """Tests for USCF parsing error handling."""

    def test_parse_content_invalid_json(self):
        """Test parsing with invalid JSON."""
        uscf = USCF("Test Player")
        with pytest.raises(json.JSONDecodeError):
            uscf.parse_content("This is not JSON")

    def test_parse_content_empty_string(self):
        """Test parsing with empty string."""
        uscf = USCF("Test Player")
        with pytest.raises(json.JSONDecodeError):
            uscf.parse_content("")

    def test_parse_content_missing_items(self):
        """Test parsing JSON missing 'items' key."""
        json_content = json.dumps({
            "success": True
        })
        uscf = USCF("Test Player")
        assert uscf.parse_content(json_content) is None

    def test_parse_content_empty_items_list(self):
        """Test parsing JSON with empty items list."""
        json_content = json.dumps({
            "items": []
        })
        uscf = USCF("Test Player")
        assert uscf.parse_content(json_content) is None

    def test_parse_content_missing_endDate(self):
        """Test parsing JSON missing 'endDate' field."""
        json_content = json.dumps({
            "items": [
                {
                    "ratingRecords": [
                        {
                            "postRating": 1500
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Test Player")
        assert uscf.parse_content(json_content) is None

    def test_parse_content_missing_ratingRecords(self):
        """Test parsing JSON missing 'ratingRecords' field."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01"
                }
            ]
        })
        uscf = USCF("Test Player")
        assert uscf.parse_content(json_content) is None

    def test_parse_content_empty_ratingRecords_list(self):
        """Test parsing JSON with empty ratingRecords list."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": []
                }
            ]
        })
        uscf = USCF("Test Player")
        assert uscf.parse_content(json_content) is None

    def test_parse_content_missing_postRating(self):
        """Test parsing JSON missing 'postRating' field."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "preRating": 1400
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Test Player")
        assert uscf.parse_content(json_content) is None


class TestUSCFComplexScenarios:
    """Tests for complex real-world scenarios."""

    def test_parse_content_with_multiple_rating_records(self):
        """Test parsing JSON with multiple rating records (uses first one)."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1850
                        },
                        {
                            "postRating": 1900
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Test Player")
        result = uscf.parse_content(json_content)
        # Should use the first rating record
        assert result.ratings["standard"] == 1850

    def test_parse_content_with_multiple_items(self):
        """Test parsing JSON with multiple items (uses first one)."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1850
                        }
                    ]
                },
                {
                    "endDate": "2024-12-01",
                    "ratingRecords": [
                        {
                            "postRating": 1800
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Test Player")
        result = uscf.parse_content(json_content)
        # Should use the first item
        assert result.metadata.as_of == "2025-02-01"
        assert result.ratings["standard"] == 1850

    def test_uscf_player_attribute_persistence(self):
        """Test that player attribute persists after get_url call."""
        uscf = USCF("Test Player")
        original_player = uscf.player
        _ = uscf.get_url()
        assert uscf.player == original_player

    def test_uscf_player_attribute_persistence_after_parse(self):
        """Test that player attribute persists after parse_content call."""
        uscf = USCF("Test Player")
        original_player = uscf.player
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1500
                        }
                    ]
                }
            ]
        })
        _ = uscf.parse_content(json_content)
        assert uscf.player == original_player

    def test_parse_content_return_type(self):
        """Test that parse_content returns a normalized profile."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1500
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Test Player")
        result = uscf.parse_content(json_content)
        assert result.provider == "uscf"
        assert isinstance(result.ratings, dict)

    def test_parse_content_output_format(self):
        """Test that parse_content populates the normalized schema correctly."""
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1500
                        }
                    ]
                }
            ]
        })
        uscf = USCF("Test Player")
        result = uscf.parse_content(json_content)
        assert result.provider == "uscf"
        assert result.player.id == "Test Player"
        assert result.ratings["standard"] == 1500
        assert result.metadata.as_of == "2025-02-01"
        assert result.metadata.source_url == uscf.get_url()


class TestUSCFFetch:
    """Tests for USCF fetch orchestration."""

    def test_fetch_returns_normalized_profile_from_http_response(self):
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1500
                        }
                    ]
                }
            ]
        })
        http_client = Mock(spec=HttpPort)
        http_client.get.return_value = json_content

        uscf = USCF("12345678", http_client)

        result = uscf.fetch()

        assert result.provider == "uscf"
        assert result.player.id == "12345678"
        assert result.ratings["standard"] == 1500
        assert result.metadata.as_of == "2025-02-01"
        assert result.metadata.source_url == uscf.get_url()
        http_client.get.assert_called_once_with(uscf.get_url())

    def test_fetch_returns_none_when_http_client_returns_none(self):
        http_client = Mock(spec=HttpPort)
        http_client.get.return_value = None

        uscf = USCF("12345678", http_client)

        result = uscf.fetch()

        assert result is None
        http_client.get.assert_called_once_with(uscf.get_url())

    def test_fetch_with_numeric_id_never_calls_fuzzy_endpoint(self):
        json_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1500
                        }
                    ]
                }
            ]
        })
        http_client = Mock(spec=HttpPort)
        http_client.get.return_value = json_content

        uscf = USCF("12345678", http_client)
        uscf.fetch()

        called_urls = [call.args[0] for call in http_client.get.call_args_list]
        assert all("Fuzzy" not in url for url in called_urls)


class TestUSCFFetchByName:
    """Tests for USCF fetch orchestration when given a non-numeric name."""

    def test_fetch_resolves_single_fuzzy_match_then_fetches_sections(self):
        fuzzy_content = json.dumps({
            "items": [
                {"id": "12663913", "firstName": "Dan", "lastName": "Bock", "stateRep": "NC"}
            ]
        })
        sections_content = json.dumps({
            "items": [
                {
                    "endDate": "2025-02-01",
                    "ratingRecords": [
                        {
                            "postRating": 1889
                        }
                    ]
                }
            ]
        })
        http_client = Mock(spec=HttpPort)
        http_client.get.side_effect = [fuzzy_content, sections_content]

        uscf = USCF("Dan Bock", http_client)
        result = uscf.fetch()

        assert result.player.id == "12663913"
        assert result.player.display_name == "Dan Bock"
        assert result.ratings["standard"] == 1889
        assert http_client.get.call_args_list[0].args[0] == uscf.get_fuzzy_url("Dan Bock")
        assert http_client.get.call_args_list[1].args[0] == (
            "https://ratings-api.uschess.org/api/v1/members/12663913/sections"
        )

    def test_fetch_returns_none_when_fuzzy_search_has_no_matches(self):
        http_client = Mock(spec=HttpPort)
        http_client.get.return_value = json.dumps({"items": []})

        uscf = USCF("Nobody Findable", http_client)
        result = uscf.fetch()

        assert result is None
        http_client.get.assert_called_once_with(uscf.get_fuzzy_url("Nobody Findable"))

    def test_fetch_returns_none_when_fuzzy_search_http_call_fails(self):
        http_client = Mock(spec=HttpPort)
        http_client.get.return_value = None

        uscf = USCF("Dan Bock", http_client)
        result = uscf.fetch()

        assert result is None

    def test_fetch_raises_when_fuzzy_search_has_multiple_matches(self):
        fuzzy_content = json.dumps({
            "items": [
                {"id": "12663913", "firstName": "Dan", "lastName": "Bock", "stateRep": "NC"},
                {"id": "13557564", "firstName": "Daniel", "lastName": "Bockelman", "stateRep": "NY"},
            ]
        })
        http_client = Mock(spec=HttpPort)
        http_client.get.return_value = fuzzy_content

        uscf = USCF("Dan Bock", http_client)

        with pytest.raises(AmbiguousUSCFPlayerError) as exc_info:
            uscf.fetch()

        error = exc_info.value
        assert error.query == "Dan Bock"
        assert error.candidates == [
            {"id": "12663913", "name": "Dan Bock", "state": "NC"},
            {"id": "13557564", "name": "Daniel Bockelman", "state": "NY"},
        ]
        # An ambiguous match must not fall through to a sections fetch.
        assert http_client.get.call_count == 1


class TestUSCFGetFuzzyURL:
    """Tests for USCF fuzzy-search URL generation."""

    def test_get_fuzzy_url_encodes_spaces(self):
        uscf = USCF("Dan Bock")
        expected_url = "https://ratings-api.uschess.org/api/v1/members?Fuzzy=Dan+Bock"
        assert uscf.get_fuzzy_url("Dan Bock") == expected_url
