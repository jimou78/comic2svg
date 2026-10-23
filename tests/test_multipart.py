from comic2svg.webui import parse_multipart_form


def test_parse_multipart_form():
    boundary = "---------------------------974767299852498929531610575"
    body = (
        f"--{boundary}\r\n"
        "Content-Disposition: form-data; name=\"preset\"\r\n\r\n"
        "vintage-comic\r\n"
        f"--{boundary}\r\n"
        "Content-Disposition: form-data; name=\"file\"; filename=\"sample.png\"\r\n"
        "Content-Type: image/png\r\n\r\n"
        "FAKE_IMAGE_DATA_12345\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    fields = parse_multipart_form(body, boundary)
    assert "preset" in fields
    assert fields["preset"][0] == b"vintage-comic"
    assert "file" in fields
    assert fields["file"][0] == b"FAKE_IMAGE_DATA_12345"
