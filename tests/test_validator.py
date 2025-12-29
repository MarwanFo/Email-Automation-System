"""
Tests for the Validator module.
"""

import pytest
import tempfile
import csv
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validator import (
    EmailValidator,
    CSVValidator,
    TemplateValidator,
    AttachmentValidator,
    ValidationResult
)


# ═══════════════════════════════════════════════════════════════════════════════
# Email Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestEmailValidator:
    """Tests for email address validation."""
    
    def test_valid_email(self):
        """Should accept valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@gmail.com",
            "first.last@subdomain.domain.org",
            "maya.patel@riverside-cafe.com"
        ]
        
        for email in valid_emails:
            result = EmailValidator.validate(email)
            assert result.is_valid, f"Expected {email} to be valid"
    
    def test_invalid_email_missing_at(self):
        """Should reject email without @ symbol."""
        result = EmailValidator.validate("notanemail.com")
        
        assert result.is_valid is False
        assert "@" in result.message.lower()
    
    def test_invalid_email_multiple_at(self):
        """Should reject email with multiple @ symbols."""
        result = EmailValidator.validate("user@@domain.com")
        
        assert result.is_valid is False
        assert "too many @" in result.message.lower()
    
    def test_invalid_email_with_spaces(self):
        """Should reject email with spaces and suggest fix."""
        result = EmailValidator.validate("user @domain.com")
        
        assert result.is_valid is False
        assert "spaces" in result.message.lower()
        assert result.suggestion is not None
    
    def test_empty_email(self):
        """Should reject empty email."""
        result = EmailValidator.validate("")
        
        assert result.is_valid is False
        assert "empty" in result.message.lower()
    
    def test_common_typo_detection(self):
        """Should detect common domain typos."""
        typos = [
            ("user@gamil.com", "gmail.com"),
            ("user@gmail.con", "gmail.com"),
            ("user@outlok.com", "outlook.com"),
            ("user@hotmal.com", "hotmail.com"),
        ]
        
        for typo_email, correct_domain in typos:
            result = EmailValidator.validate(typo_email)
            assert result.is_valid is False
            assert result.suggestion is not None
            assert correct_domain in result.suggestion
    
    def test_validate_list(self):
        """Should validate a list of emails."""
        emails = [
            "valid@example.com",
            "also.valid@test.co",
            "invalid-email",
            "another@good.org"
        ]
        
        valid, invalid = EmailValidator.validate_list(emails)
        
        assert len(valid) == 3
        assert len(invalid) == 1
        assert invalid[0][0] == "invalid-email"


# ═══════════════════════════════════════════════════════════════════════════════
# CSV Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestCSVValidator:
    """Tests for CSV file validation."""
    
    def test_valid_csv(self, tmp_path):
        """Should accept valid CSV with email column."""
        csv_path = tmp_path / "valid.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['email', 'first_name', 'company'])
            writer.writeheader()
            writer.writerow({'email': 'test@example.com', 'first_name': 'Test', 'company': 'Test Co'})
        
        result = CSVValidator.validate(str(csv_path))
        
        assert result.is_valid
    
    def test_missing_email_column(self, tmp_path):
        """Should reject CSV without email column."""
        csv_path = tmp_path / "no_email.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'company'])
            writer.writeheader()
            writer.writerow({'name': 'Test', 'company': 'Test Co'})
        
        result = CSVValidator.validate(str(csv_path))
        
        assert result.is_valid is False
        assert "email" in result.message.lower()
    
    def test_empty_csv(self, tmp_path):
        """Should reject empty CSV file."""
        csv_path = tmp_path / "empty.csv"
        csv_path.write_text("")
        
        result = CSVValidator.validate(str(csv_path))
        
        assert result.is_valid is False
    
    def test_nonexistent_file(self):
        """Should reject nonexistent file."""
        result = CSVValidator.validate("/path/to/nonexistent.csv")
        
        assert result.is_valid is False
        assert "not found" in result.message.lower()
    
    def test_load_recipients(self, tmp_path):
        """Should load and validate recipients from CSV."""
        csv_path = tmp_path / "recipients.csv"
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['email', 'first_name'])
            writer.writeheader()
            writer.writerow({'email': 'valid@example.com', 'first_name': 'Valid'})
            writer.writerow({'email': 'invalid-email', 'first_name': 'Invalid'})
            writer.writerow({'email': 'also.valid@test.com', 'first_name': 'Also'})
        
        recipients, errors = CSVValidator.load_recipients(str(csv_path))
        
        assert len(recipients) == 2
        assert len(errors) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# Template Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestTemplateValidator:
    """Tests for template file validation."""
    
    def test_valid_template(self, tmp_path):
        """Should accept valid template file."""
        template_path = tmp_path / "template.html"
        template_path.write_text("<html><body>Hello {{name}}</body></html>")
        
        result = TemplateValidator.validate(str(template_path))
        
        assert result.is_valid
    
    def test_empty_template(self, tmp_path):
        """Should reject empty template file."""
        template_path = tmp_path / "empty.html"
        template_path.write_text("")
        
        result = TemplateValidator.validate(str(template_path))
        
        assert result.is_valid is False
        assert "empty" in result.message.lower()
    
    def test_nonexistent_template(self):
        """Should reject nonexistent template file."""
        result = TemplateValidator.validate("/path/to/nonexistent.html")
        
        assert result.is_valid is False
        assert "not found" in result.message.lower()
    
    def test_extract_variables(self, tmp_path):
        """Should extract variable names from template."""
        template_path = tmp_path / "template.html"
        template_path.write_text("""
            <h1>Hello {{first_name}}</h1>
            <p>Welcome to {{company}}</p>
            <p>Your role: {{role}}</p>
        """)
        
        variables = TemplateValidator.extract_variables(template_path.read_text())
        
        assert "first_name" in variables
        assert "company" in variables
        assert "role" in variables


# ═══════════════════════════════════════════════════════════════════════════════
# Attachment Validation Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAttachmentValidator:
    """Tests for attachment file validation."""
    
    def test_valid_attachment(self, tmp_path):
        """Should accept valid file."""
        file_path = tmp_path / "document.pdf"
        file_path.write_bytes(b"PDF content here")
        
        result = AttachmentValidator.validate(str(file_path))
        
        assert result.is_valid
    
    def test_blocked_extension(self, tmp_path):
        """Should reject dangerous file extensions."""
        blocked_extensions = [".exe", ".bat", ".js", ".vbs"]
        
        for ext in blocked_extensions:
            file_path = tmp_path / f"file{ext}"
            file_path.write_bytes(b"content")
            
            result = AttachmentValidator.validate(str(file_path))
            
            assert result.is_valid is False
            assert "blocked" in result.message.lower()
    
    def test_empty_file(self, tmp_path):
        """Should reject empty files."""
        file_path = tmp_path / "empty.pdf"
        file_path.write_bytes(b"")
        
        result = AttachmentValidator.validate(str(file_path))
        
        assert result.is_valid is False
        assert "empty" in result.message.lower()
    
    def test_nonexistent_file(self):
        """Should reject nonexistent file."""
        result = AttachmentValidator.validate("/path/to/nonexistent.pdf")
        
        assert result.is_valid is False
        assert "not found" in result.message.lower()
    
    def test_directory_instead_of_file(self, tmp_path):
        """Should reject directories."""
        dir_path = tmp_path / "subdir"
        dir_path.mkdir()
        
        result = AttachmentValidator.validate(str(dir_path))
        
        assert result.is_valid is False
        assert "directory" in result.message.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# ValidationResult Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidationResult:
    """Tests for the ValidationResult dataclass."""
    
    def test_valid_result(self):
        """Should create a valid result."""
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid
        assert result.message == ""
        assert result.suggestion is None
    
    def test_invalid_result_with_suggestion(self):
        """Should create invalid result with suggestion."""
        result = ValidationResult(
            is_valid=False,
            message="Something is wrong",
            suggestion="Try this instead"
        )
        
        assert not result.is_valid
        assert result.message == "Something is wrong"
        assert result.suggestion == "Try this instead"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
