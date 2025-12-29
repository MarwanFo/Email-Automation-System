"""
Template Engine

Renders email templates with variable substitution using Jinja2.
Supports both HTML and plain text templates with smart fallbacks.
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader, BaseLoader, TemplateNotFound, TemplateSyntaxError

from .validator import TemplateValidator


@dataclass
class RenderedEmail:
    """A template that's been rendered with data."""
    subject: str
    body_html: Optional[str] = None
    body_text: Optional[str] = None


class TemplateError(Exception):
    """Raised when template rendering fails."""
    pass


class TemplateEngine:
    """
    Renders email templates using Jinja2.
    
    Supports:
    - HTML templates with full Jinja2 syntax
    - Plain text templates
    - Variable substitution from dictionaries
    - Template validation before sending
    """
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the template engine.
        
        template_dir: Base directory for templates. Defaults to ./templates
        """
        self.template_dir = Path(template_dir) if template_dir else Path("./templates")
        
        # Set up Jinja2 environment
        if self.template_dir.exists():
            self.env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=True,  # Escape HTML by default for security
                trim_blocks=True,
                lstrip_blocks=True
            )
        else:
            # Use a basic loader if no template directory
            self.env = Environment(autoescape=True)
        
        # Register custom filters
        self._register_filters()
    
    def render_file(
        self,
        template_path: str,
        variables: Dict[str, Any],
        subject: Optional[str] = None
    ) -> RenderedEmail:
        """
        Render a template file with the given variables.
        
        template_path: Path to the template file (relative to template_dir or absolute)
        variables: Dictionary of values to substitute
        subject: Email subject (can also be in template as {{subject}})
        """
        path = Path(template_path)
        
        # Try to resolve relative to template directory
        if not path.is_absolute():
            full_path = self.template_dir / path
            if not full_path.exists():
                full_path = path  # Try as-is
        else:
            full_path = path
        
        # Validate the template file
        validation = TemplateValidator.validate(str(full_path))
        if not validation.is_valid:
            raise TemplateError(validation.message)
        
        # Read and render
        with open(full_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        return self.render_string(template_content, variables, subject)
    
    def render_string(
        self,
        template_content: str,
        variables: Dict[str, Any],
        subject: Optional[str] = None
    ) -> RenderedEmail:
        """
        Render a template string with the given variables.
        
        template_content: The template content as a string
        variables: Dictionary of values to substitute
        subject: Email subject line
        """
        try:
            template = self.env.from_string(template_content)
            rendered = template.render(**variables)
        except TemplateSyntaxError as e:
            raise TemplateError(
                f"Template syntax error on line {e.lineno}: {e.message}\n"
                f"Check your Jinja2 syntax — make sure all {{{{ }}}} are properly closed."
            )
        except Exception as e:
            raise TemplateError(f"Template rendering failed: {str(e)}")
        
        # Determine if this is HTML or plain text
        is_html = self._is_html(rendered)
        
        # Resolve subject — from parameter, from variables, or extract from template
        final_subject = subject or variables.get("subject", "")
        
        if is_html:
            # Generate plain text version from HTML
            plain_text = self._html_to_text(rendered)
            return RenderedEmail(
                subject=final_subject,
                body_html=rendered,
                body_text=plain_text
            )
        else:
            return RenderedEmail(
                subject=final_subject,
                body_html=None,
                body_text=rendered
            )
    
    def get_template_variables(self, template_path: str) -> List[str]:
        """
        Extract all variable names from a template.
        
        Useful for checking if your CSV has all required columns.
        """
        path = Path(template_path)
        
        if not path.is_absolute():
            full_path = self.template_dir / path
            if not full_path.exists():
                full_path = path
        else:
            full_path = path
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self._extract_variables(content)
    
    def validate_template_with_data(
        self,
        template_path: str,
        sample_data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a template can be rendered with given data.
        
        Returns (success, error_message)
        """
        try:
            self.render_file(template_path, sample_data)
            return True, None
        except TemplateError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def list_available_templates(self) -> List[Dict[str, Any]]:
        """
        List all templates in the template directory.
        
        Returns a list of dicts with name, path, and variables.
        """
        templates = []
        
        if not self.template_dir.exists():
            return templates
        
        for ext in [".html", ".htm", ".txt"]:
            for path in self.template_dir.glob(f"*{ext}"):
                variables = self._extract_variables(path.read_text(encoding='utf-8'))
                templates.append({
                    "name": path.stem,
                    "path": str(path),
                    "type": "html" if ext in [".html", ".htm"] else "text",
                    "variables": variables
                })
        
        return templates
    
    def _register_filters(self):
        """Register custom Jinja2 filters for email formatting."""
        
        def format_currency(value, currency="$"):
            """Format a number as currency."""
            try:
                return f"{currency}{float(value):,.2f}"
            except (ValueError, TypeError):
                return value
        
        def format_date(value, format_str="%B %d, %Y"):
            """Format a date string or object."""
            from datetime import datetime
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value)
                except ValueError:
                    return value
            if hasattr(value, 'strftime'):
                return value.strftime(format_str)
            return value
        
        def title_case(value):
            """Convert to title case."""
            return str(value).title()
        
        def first_name(value):
            """Extract first name from a full name."""
            if not value:
                return ""
            parts = str(value).strip().split()
            return parts[0] if parts else ""
        
        self.env.filters['currency'] = format_currency
        self.env.filters['date'] = format_date
        self.env.filters['title'] = title_case
        self.env.filters['first_name'] = first_name
    
    def _is_html(self, content: str) -> bool:
        """Detect if content is HTML."""
        html_indicators = ['<html', '<body', '<div', '<p>', '<table', '<!doctype']
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in html_indicators)
    
    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML to plain text.
        
        A simple implementation — for serious use, consider html2text library.
        """
        import re
        
        # Remove scripts and styles
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        
        # Convert common elements
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</div>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</h[1-6]>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</tr>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</li>', '\n', text, flags=re.IGNORECASE)
        
        # Remove remaining tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Decode HTML entities
        import html
        text = html.unescape(text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        
        return text
    
    def _extract_variables(self, template_content: str) -> List[str]:
        """
        Find all variable placeholders in a template.
        
        Handles both {{variable}} and {{variable|filter}} syntax.
        """
        # Match {{ variable }} or {{ variable|filter }}
        pattern = re.compile(r'\{\{\s*(\w+)(?:\s*\|[^}]+)?\s*\}\}')
        variables = pattern.findall(template_content)
        
        # Also check for variables in control structures like {% for item in items %}
        for_pattern = re.compile(r'\{%\s*for\s+\w+\s+in\s+(\w+)')
        variables.extend(for_pattern.findall(template_content))
        
        if_pattern = re.compile(r'\{%\s*if\s+(\w+)')
        variables.extend(if_pattern.findall(template_content))
        
        # Remove duplicates while preserving order
        seen = set()
        unique = []
        for var in variables:
            if var not in seen:
                seen.add(var)
                unique.append(var)
        
        return unique


# Default template engine instance
_engine: Optional[TemplateEngine] = None


def get_template_engine(template_dir: Optional[str] = None) -> TemplateEngine:
    """Get or create the default template engine."""
    global _engine
    if _engine is None or template_dir is not None:
        _engine = TemplateEngine(template_dir)
    return _engine
