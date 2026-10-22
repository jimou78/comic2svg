from comic2svg.pdf import parse_page_range


def test_parse_page_range_none():
    pages = parse_page_range(None, 10)
    assert pages == list(range(10))


def test_parse_page_range_single():
    pages = parse_page_range("1, 3, 5", 10)
    assert pages == [0, 2, 4]


def test_parse_page_range_span():
    pages = parse_page_range("2-5", 10)
    assert pages == [1, 2, 3, 4]


def test_parse_page_range_mixed():
    pages = parse_page_range("1, 4-6, 9", 10)
    assert pages == [0, 3, 4, 5, 8]


def test_parse_page_range_out_of_bounds():
    pages = parse_page_range("1, 15, 20", 5)
    assert pages == [0]
