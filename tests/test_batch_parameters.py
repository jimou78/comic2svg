from unittest.mock import patch

from comic2svg.core import convert_batch


def test_convert_batch_parameter_forwarding(tmp_path):
    # Create dummy images in folder
    img1 = tmp_path / "page_1.png"
    img2 = tmp_path / "page_2.png"
    img1.write_bytes(b"dummy")
    img2.write_bytes(b"dummy")

    with patch("comic2svg.core.convert_file") as mock_convert:
        mock_convert.return_value = [tmp_path / "out1.svg"]

        results = convert_batch(
            input_paths=[tmp_path],
            output_dir=tmp_path / "out",
            preset="vintage-comic",
            dpi=400,
            adaptive_dpi=True,
            page_range="1-2",
            split_pages=True,
            split_direction="rtl",
            crop_borders=True,
            descreen=True,
            flipbook=False,
            fast=True,
            use_hd=True,
            hd_scale=2.0,
            optimize=True,
            precision=2,
        )

        assert mock_convert.call_count == 2
        # Check that high-level parameters were forwarded
        call_kwargs = mock_convert.call_args_list[0].kwargs
        assert call_kwargs["dpi"] == 400
        assert call_kwargs["adaptive_dpi"] is True
        assert call_kwargs["split_pages"] is True
        assert call_kwargs["split_direction"] == "rtl"
        assert call_kwargs["crop_borders"] is True
        assert call_kwargs["descreen"] is True
        assert call_kwargs["fast"] is True
        assert call_kwargs["use_hd"] is True
        assert call_kwargs["hd_scale"] == 2.0
        assert len(results) == 2
