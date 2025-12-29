"""
Input Validation with Personality

We validate user input thoroughly and provide actually helpful
error messages when things don't look right.
"""

import re
import csv
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass


# Email regex — we're not trying to be RFC 5322 compliant, just practical.
# This catches 99% of typos while not being overly strict.
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Common email domain typos people make
COMMON_DOMAIN_TYPOS = {
    "gamil.com": "gmail.com",
    "gmal.com": "gmail.com",
    "gmial.com": "gmail.com",
    "gmail.con": "gmail.com",
    "gmail.co": "gmail.com",
    "outlok.com": "outlook.com",
    "outloo.com": "outlook.com",
    "outlook.con": "outlook.com",
    "hotmal.com": "hotmail.com",
    "hotmail.con": "hotmail.com",
    "yaho.com": "yahoo.com",
    "yahoo.con": "yahoo.com",
}


@dataclass
class ValidationResult:
    """
    Result of a validation check.
    
    is_valid: whether the input passed validation
    message: human-friendly description of the issue (if any)
    suggestion: optional fix suggestion
    """
    is_valid: bool
    message: str = ""
    suggestion: Optional[str] = None


class EmailValidator:
    """
    Validates email addresses with helpful feedback.
    
    We go beyond just regex matching — we check for common typos
    and provide suggestions when we spot likely mistakes.
    """
    
    @staticmethod
    def validate(email: str) -> ValidationResult:
        """
        Check if an email address looks valid.
        
        Returns a ValidationResult with suggestions for common typos.
        """
        if not email:
            return ValidationResult(
                is_valid=False,
                message="Email address can't be empty."
            )
        
        email = email.strip().lower()
        
        # Check for missing @
        if "@" not in email:
            return ValidationResult(
                is_valid=False,
                message=f'"{email}" is missing the @ symbol.',
                suggestion=f"Did you mean something like: name@domain.com?"
            )
        
        # Check for spaces (common copy-paste issue)
        if " " in email:
            cleaned = email.replace(" ", "")
            return ValidationResult(
                is_valid=False,
                message=f'Email addresses can\'t contain spaces.',
                suggestion=f"Maybe you meant: {cleaned}"
            )
        
        # Check for multiple @ symbols
        if email.count("@") > 1:
            return ValidationResult(
                is_valid=False,
                message=f'"{email}" has too many @ symbols.',
                suggestion="An email should have exactly one @ symbol."
            )
        
        # Check against our pattern
        if not EMAIL_PATTERN.match(email):
            return ValidationResult(
                is_valid=False,
                message=f'"{email}" doesn\'t look like a valid email format.',
                suggestion="Expected format: name@domain.com"
            )
        
        # Check for common domain typos
        domain = email.split("@")[1]
        if domain in COMMON_DOMAIN_TYPOS:
            correct_domain = COMMON_DOMAIN_TYPOS[domain]
            corrected_email = email.replace(domain, correct_domain)
            return ValidationResult(
                is_valid=False,  # Treat as invalid to prevent sending to wrong address
                message=f'Possible typo in "{domain}"',
                suggestion=f"Did you mean: {corrected_email}?"
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def validate_list(emails: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Validate a list of email addresses.
        
        Returns:
            (valid_emails, invalid_emails_with_reasons)
        """
        valid = []
        invalid = []
        
        for email in emails:
            result = EmailValidator.validate(email)
            if result.is_valid:
                valid.append(email.strip().lower())
            else:
                reason = result.message
                if result.suggestion:
                    reason += f" {result.suggestion}"
                invalid.append((email, reason))
        
        return valid, invalid


class CSVValidator:
    """
    Validates CSV files for bulk sending.
    
    Makes sure the file exists, has the right structure, and contains
    valid email addresses.
    """
    
    REQUIRED_COLUMNS = ["email"]  # At minimum, we need emails
    OPTIONAL_COLUMNS = ["first_name", "last_name", "name", "company", "role"]
    
    @staticmethod
    def validate(file_path: str) -> ValidationResult:
        """
        Check if a CSV file is valid for bulk sending.
        """
        path = Path(file_path)
        
        # Does the file exist?
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                message=f"File not found: {file_path}",
                suggestion="Double-check the path. Use absolute paths if unsure."
            )
        
        # Is it actually a file (not a directory)?
        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                message=f"'{file_path}' is a directory, not a file."
            )
        
        # Can we read it as CSV?
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                
                if not headers:
                    return ValidationResult(
                        is_valid=False,
                        message="CSV file appears to be empty or has no headers.",
                        suggestion="First row should be column headers: email,first_name,company"
                    )
                
                # Check for required columns
                headers_lower = [h.lower().strip() for h in headers]
                if "email" not in headers_lower:
                    return ValidationResult(
                        is_valid=False,
                        message="CSV is missing an 'email' column.",
                        suggestion=f"Found columns: {', '.join(headers)}"
                    )
                
                # Try to read first row to verify structure
                try:
                    first_row = next(reader)
                except StopIteration:
                    return ValidationResult(
                        is_valid=False,
                        message="CSV has headers but no data rows."
                    )
                
        except UnicodeDecodeError:
            return ValidationResult(
                is_valid=False,
                message="Couldn't read the file. It might not be UTF-8 encoded.",
                suggestion="Try saving the CSV as UTF-8 in your spreadsheet app."
            )
        except csv.Error as e:
            return ValidationResult(
                is_valid=False,
                message=f"CSV parsing error: {str(e)}",
                suggestion="Make sure it's a properly formatted CSV file."
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def load_recipients(file_path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        """
        Load and validate recipients from a CSV file.
        
        Returns:
            (valid_recipients, error_messages)
        """
        path = Path(file_path)
        recipients = []
        errors = []
        
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is headers
                # Normalize keys to lowercase
                normalized = {k.lower().strip(): v.strip() for k, v in row.items()}
                
                # Validate email
                email = normalized.get("email", "")
                validation = EmailValidator.validate(email)
                
                if validation.is_valid:
                    recipients.append(normalized)
                else:
                    errors.append(f"Row {row_num}: {validation.message}")
        
        return recipients, errors


class TemplateValidator:
    """
    Validates email template files.
    """
    
    @staticmethod
    def validate(file_path: str) -> ValidationResult:
        """
        Check if a template file is valid.
        """
        path = Path(file_path)
        
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                message=f"Template file not found: {file_path}",
                suggestion="Check the path. Available templates are in templates/"
            )
        
        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                message=f"'{file_path}' is not a file."
            )
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                if not content.strip():
                    return ValidationResult(
                        is_valid=False,
                        message="Template file is empty."
                    )
                
        except UnicodeDecodeError:
            return ValidationResult(
                is_valid=False,
                message="Couldn't read the template file (encoding issue).",
                suggestion="Save the file as UTF-8."
            )
        except IOError as e:
            return ValidationResult(
                is_valid=False,
                message=f"Couldn't read the file: {str(e)}"
            )
        
        return ValidationResult(is_valid=True)
    
    @staticmethod
    def extract_variables(template_content: str) -> List[str]:
        """
        Find all {{variable}} placeholders in a template.
        
        Useful for checking if the CSV has all needed columns.
        """
        pattern = re.compile(r'\{\{\s*(\w+)\s*\}\}')
        variables = pattern.findall(template_content)
        return list(set(variables))  # Remove duplicates


class AttachmentValidator:
    """
    Validates attachment files.
    """
    
    # Some email providers reject these extensions
    BLOCKED_EXTENSIONS = {
        ".exe", ".bat", ".cmd", ".msi", ".js", ".vbs", 
        ".scr", ".pif", ".com", ".jar"
    }
    
    # Reasonable size limit (25 MB is common email attachment limit)
    MAX_SIZE_BYTES = 25 * 1024 * 1024
    
    @staticmethod
    def validate(file_path: str) -> ValidationResult:
        """
        Check if a file can be attached to an email.
        """
        path = Path(file_path)
        
        if not path.exists():
            return ValidationResult(
                is_valid=False,
                message=f"Attachment file not found: {file_path}"
            )
        
        if not path.is_file():
            return ValidationResult(
                is_valid=False,
                message=f"'{file_path}' is a directory, not a file."
            )
        
        # Check extension
        extension = path.suffix.lower()
        if extension in AttachmentValidator.BLOCKED_EXTENSIONS:
            return ValidationResult(
                is_valid=False,
                message=f"'{extension}' files are blocked by most email providers.",
                suggestion="Try compressing it into a .zip file."
            )
        
        # Check file size
        size = path.stat().st_size
        if size > AttachmentValidator.MAX_SIZE_BYTES:
            size_mb = size / (1024 * 1024)
            return ValidationResult(
                is_valid=False,
                message=f"File is too large ({size_mb:.1f} MB). Maximum is 25 MB.",
                suggestion="Try compressing the file or using a file sharing service."
            )
        
        if size == 0:
            return ValidationResult(
                is_valid=False,
                message="File is empty (0 bytes)."
            )
        
        return ValidationResult(is_valid=True)
