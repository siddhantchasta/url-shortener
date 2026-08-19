from app.utils import generate_short_code


def test_generate_short_code_length():
    code = generate_short_code(6)
    assert len(code) == 6


def test_generate_short_code_is_alphanumeric():
    code = generate_short_code(10)
    assert code.isalnum()


def test_generate_short_code_is_reasonably_unique():
    codes = {generate_short_code(6) for _ in range(1000)}
    assert len(codes) > 990
