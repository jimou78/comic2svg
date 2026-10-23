from comic2svg.flipbook import generate_flipbook


def test_generate_flipbook(tmp_path):
    svg1 = tmp_path / "page_001.svg"
    svg2 = tmp_path / "page_002.svg"
    svg1.write_text('<svg viewBox="0 0 100 100"><circle cx="50" cy="50" r="40"/></svg>', encoding="utf-8")
    svg2.write_text('<svg viewBox="0 0 100 100"><rect width="80" height="80"/></svg>', encoding="utf-8")

    out_html = tmp_path / "flipbook.html"
    result = generate_flipbook([svg1, svg2], out_html, title="Test Lianhuanhua")

    assert result.is_file()
    content = result.read_text(encoding="utf-8")
    assert "Test Lianhuanhua" in content
    assert "totalPages = 2" in content
    assert "<circle" in content
    assert "<rect" in content
