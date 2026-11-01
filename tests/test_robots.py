from geo_check.robots import AI_CRAWLERS, check_crawlers, parse_robots


def status(content, agent):
    return check_crawlers(content, [agent])[agent]


def test_empty_content_allows_all():
    res = check_crawlers("")
    assert set(res) == set(AI_CRAWLERS)
    assert all(v["status"] == "allowed" and v["source"] == "none" for v in res.values())


def test_wildcard_disallow_all_blocks():
    r = status("User-agent: *\nDisallow: /\n", "GPTBot")
    assert r == {"status": "blocked", "source": "wildcard"}


def test_specific_group_overrides_wildcard():
    c = "User-agent: *\nDisallow: /\n\nUser-agent: GPTBot\nAllow: /\n"
    assert status(c, "GPTBot")["status"] == "allowed"
    assert status(c, "GPTBot")["source"] == "specific"
    assert status(c, "ClaudeBot")["status"] == "blocked"


def test_specific_block_only():
    c = "User-agent: GPTBot\nDisallow: /\n"
    assert status(c, "GPTBot")["status"] == "blocked"
    assert status(c, "ClaudeBot")["status"] == "allowed"


def test_empty_disallow_means_allowed():
    assert status("User-agent: *\nDisallow:\n", "CCBot")["status"] == "allowed"


def test_allow_root_beats_disallow_root_tie():
    c = "User-agent: *\nDisallow: /\nAllow: /\n"
    assert status(c, "CCBot")["status"] == "allowed"


def test_partial_when_only_subpaths_disallowed():
    c = "User-agent: *\nDisallow: /admin/\n"
    assert status(c, "CCBot")["status"] == "partial"


def test_multiple_user_agents_share_group_and_case_insensitive():
    c = "user-agent: gptbot\nUser-Agent: CCBot\nDisallow: /\n"
    assert status(c, "GPTBot")["status"] == "blocked"
    assert status(c, "CCBot")["status"] == "blocked"
    assert status(c, "ClaudeBot")["status"] == "allowed"


def test_comments_and_blank_lines_ignored():
    c = "# hi\nUser-agent: GPTBot # inline\n\nDisallow: / # all\n"
    assert status(c, "GPTBot")["status"] == "blocked"


def test_parse_groups():
    g = parse_robots("User-agent: a\nUser-agent: b\nDisallow: /x\nUser-agent: c\nAllow: /\n")
    assert g[0]["agents"] == ["a", "b"] and g[0]["rules"] == [("disallow", "/x")]
    assert g[1]["agents"] == ["c"]
