from monolith import *


def test_strings():
    assert slugify("Hello, World!") == "hello-world"
    assert titlecase("a quick fox") == "A Quick Fox"


def test_maths():
    assert clamp(15, 0, 10) == 10 and clamp(-1, 0, 10) == 0
    assert mean([1, 2, 3]) == 2.0 and mean([]) == 0.0


def test_files(tmp_path):
    p = tmp_path / "x.txt"; p.write_text("a\nb\n")
    assert read_lines(p) == ["a", "b"] and file_size(p) == 4
