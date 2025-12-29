"""
Tests for the TemplateEngine module.
"""

import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.template_engine import TemplateEngine, TemplateError, RenderedEmail


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def template_engine(tmp_path):
    """Create a template engine with a temporary directory."""
    return TemplateEngine(str(tmp_path))


@pytest.fixture
def html_template():
    """Sample HTML template content."""
    return """
<!DOCTYPE html>
<html>
<head><title>{{subject}}</title></head>
<body>
    <h1>Hello {{first_name}}!</h1>
    <p>Welcome to {{company}}.</p>
</body>
</html>
"""


@pytest.fixture
def text_template():
    """Sample plain text template content."""
    return """
Hello {{first_name}},

Welcome to {{company}}!

Best regards,
{{sender_name}}
"""


# ═══════════════════════════════════════════════════════════════════════════════
# String Rendering Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRenderString:
    """Tests for rendering template strings."""
    
    def test_simple_variable_substitution(self, template_engine):
        """Should substitute simple variables."""
        template = "Hello {{name}}!"
        result = template_engine.render_string(template, {"name": "Maya"})
        
        assert result.body_text == "Hello Maya!"
    
    def test_multiple_variables(self, template_engine):
        """Should substitute multiple variables."""
        template = "Hi {{first_name}}, your order #{{order_id}} is ready."
        result = template_engine.render_string(template, {
            "first_name": "James",
            "order_id": "12345"
        })
        
        assert "James" in result.body_text
        assert "12345" in result.body_text
    
    def test_html_detected(self, template_engine, html_template):
        """Should detect HTML content and set body_html."""
        result = template_engine.render_string(html_template, {
            "subject": "Welcome",
            "first_name": "Lisa",
            "company": "TechForge"
        })
        
        assert result.body_html is not None
        assert "Hello Lisa!" in result.body_html
        assert result.body_text is not None  # Also generates plain text
    
    def test_plain_text_detected(self, template_engine, text_template):
        """Should detect plain text content."""
        result = template_engine.render_string(text_template, {
            "first_name": "David",
            "company": "Artisan Co",
            "sender_name": "Sarah"
        })
        
        assert result.body_html is None
        assert result.body_text is not None
        assert "David" in result.body_text
    
    def test_missing_variable_renders_empty(self, template_engine):
        """Should render missing variables as empty."""
        template = "Hello {{name}}, welcome!"
        result = template_engine.render_string(template, {})
        
        assert result.body_text == "Hello , welcome!"
    
    def test_subject_from_parameter(self, template_engine):
        """Should use subject from parameter."""
        template = "Hello {{name}}!"
        result = template_engine.render_string(
            template, 
            {"name": "Test"}, 
            subject="My Subject"
        )
        
        assert result.subject == "My Subject"
    
    def test_subject_from_variables(self, template_engine):
        """Should use subject from variables if not in parameter."""
        template = "Hello!"
        result = template_engine.render_string(
            template, 
            {"subject": "Variable Subject"}
        )
        
        assert result.subject == "Variable Subject"


# ═══════════════════════════════════════════════════════════════════════════════
# File Rendering Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRenderFile:
    """Tests for rendering template files."""
    
    def test_render_html_file(self, template_engine, html_template, tmp_path):
        """Should render an HTML template file."""
        template_path = tmp_path / "newsletter.html"
        template_path.write_text(html_template)
        
        result = template_engine.render_file(str(template_path), {
            "subject": "Welcome",
            "first_name": "Emma",
            "company": "Nordic Living"
        })
        
        assert "Emma" in result.body_html
        assert "Nordic Living" in result.body_html
    
    def test_render_text_file(self, template_engine, text_template, tmp_path):
        """Should render a plain text template file."""
        template_path = tmp_path / "notification.txt"
        template_path.write_text(text_template)
        
        result = template_engine.render_file(str(template_path), {
            "first_name": "Raj",
            "company": "CloudPeak",
            "sender_name": "Support"
        })
        
        assert "Raj" in result.body_text
        assert result.body_html is None
    
    def test_nonexistent_file_raises_error(self, template_engine):
        """Should raise error for missing template file."""
        with pytest.raises(TemplateError):
            template_engine.render_file("/path/to/nonexistent.html", {})


# ═══════════════════════════════════════════════════════════════════════════════
# Variable Extraction Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestVariableExtraction:
    """Tests for extracting variables from templates."""
    
    def test_extract_simple_variables(self, template_engine, tmp_path):
        """Should extract simple variable names."""
        template = tmp_path / "test.html"
        template.write_text("Hello {{first_name}} from {{company}}!")
        
        variables = template_engine.get_template_variables(str(template))
        
        assert "first_name" in variables
        assert "company" in variables
    
    def test_extract_variables_with_filters(self, template_engine, tmp_path):
        """Should extract variables even with filters."""
        template = tmp_path / "test.html"
        template.write_text("Amount: {{price|currency}}")
        
        variables = template_engine.get_template_variables(str(template))
        
        assert "price" in variables
    
    def test_extract_unique_variables(self, template_engine, tmp_path):
        """Should return unique variable names."""
        template = tmp_path / "test.html"
        template.write_text("{{name}} and {{name}} again")
        
        variables = template_engine.get_template_variables(str(template))
        
        assert variables.count("name") == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Filter Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFilters:
    """Tests for custom Jinja2 filters."""
    
    def test_title_filter(self, template_engine):
        """Should convert to title case."""
        template = "Hello {{name|title}}!"
        result = template_engine.render_string(template, {"name": "john doe"})
        
        assert "John Doe" in result.body_text
    
    def test_first_name_filter(self, template_engine):
        """Should extract first name."""
        template = "Hi {{full_name|first_name}}!"
        result = template_engine.render_string(template, {"full_name": "Maya Patel"})
        
        assert "Maya" in result.body_text
    
    def test_currency_filter(self, template_engine):
        """Should format as currency."""
        template = "Total: {{amount|currency}}"
        result = template_engine.render_string(template, {"amount": 1234.50})
        
        assert "$1,234.50" in result.body_text


# ═══════════════════════════════════════════════════════════════════════════════
# Error Handling Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestErrorHandling:
    """Tests for template error handling."""
    
    def test_syntax_error_in_template(self, template_engine):
        """Should raise TemplateError for syntax errors."""
        invalid_template = "Hello {{name"  # Missing closing braces
        
        with pytest.raises(TemplateError):
            template_engine.render_string(invalid_template, {"name": "Test"})
    
    def test_invalid_filter(self, template_engine):
        """Should raise error for invalid filter."""
        template = "{{name|nonexistent_filter}}"
        
        with pytest.raises(TemplateError):
            template_engine.render_string(template, {"name": "Test"})


# ═══════════════════════════════════════════════════════════════════════════════
# HTML to Text Conversion Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestHTMLToText:
    """Tests for HTML to plain text conversion."""
    
    def test_html_renders_plain_text_version(self, template_engine):
        """Should generate plain text from HTML."""
        html = "<html><body><h1>Hello</h1><p>World</p></body></html>"
        result = template_engine.render_string(html, {})
        
        assert result.body_html is not None
        assert result.body_text is not None
        assert "Hello" in result.body_text
        assert "World" in result.body_text
    
    def test_strips_html_tags(self, template_engine):
        """Should strip HTML tags in plain text version."""
        html = "<html><body><p>Test</p></body></html>"
        result = template_engine.render_string(html, {})
        
        assert "<p>" not in result.body_text
        assert "</p>" not in result.body_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
