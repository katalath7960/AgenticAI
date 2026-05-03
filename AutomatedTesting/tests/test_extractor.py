"""Tests for the DOM extractor."""

from crawler.extractor import extract_page_data


SAMPLE_HTML = """\
<html>
<head><title>Test Page</title><meta name="description" content="A test page"></head>
<body>
  <h1>Welcome</h1>
  <h2>Subtitle</h2>
  <form action="/submit" method="POST">
    <label for="email">Email</label>
    <input id="email" name="email" type="email" required placeholder="you@example.com" minlength="5" maxlength="100">
    <label for="password">Password</label>
    <input id="password" name="password" type="password" required>
    <button type="submit">Sign In</button>
  </form>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
  <div class="error">This field is required</div>
</body>
</html>
"""


def test_extract_title():
    page = extract_page_data(SAMPLE_HTML, "http://test.com")
    assert page.title == "Test Page"


def test_extract_headings():
    page = extract_page_data(SAMPLE_HTML, "http://test.com")
    assert "Welcome" in page.headings
    assert "Subtitle" in page.headings


def test_extract_meta():
    page = extract_page_data(SAMPLE_HTML, "http://test.com")
    assert page.meta_description == "A test page"


def test_extract_form():
    page = extract_page_data(SAMPLE_HTML, "http://test.com")
    assert len(page.forms) == 1
    form = page.forms[0]
    assert form.method == "POST"
    assert len(form.fields) == 2
    email_field = form.fields[0]
    assert email_field.name == "email"
    assert email_field.required is True
    assert email_field.min_length == 5
    assert email_field.max_length == 100


def test_extract_links():
    page = extract_page_data(SAMPLE_HTML, "http://test.com")
    assert "http://test.com/about" in page.links
    assert "http://test.com/contact" in page.links


def test_extract_error_containers():
    page = extract_page_data(SAMPLE_HTML, "http://test.com")
    assert "This field is required" in page.error_containers
