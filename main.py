"""
Credit Card Statement Parser
Supports: ICICI Bank, Axis Bank, IDFC FIRST Bank, RBL Bank, American Express

Requirements:
pip install PyPDF2 pdfplumber pandas tabulate

Usage:
python parser.py statement1.pdf statement2.pdf
python parser.py --dir ./statements/
python parser.py statement.pdf --json output.json
"""

import re
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import pdfplumber
    import pandas as pd
    from tabulate import tabulate
except ImportError:
    print("Missing dependencies. Install with:")
    print("pip install pdfplumber pandas tabulate")
    sys.exit(1)


@dataclass
class StatementData:
    """Data structure for parsed statement information"""
    file_name: str
    issuer: str
    card_number: Optional[str] = None
    statement_date: Optional[str] = None
    payment_due_date: Optional[str] = None
    total_amount_due: Optional[str] = None
    minimum_amount_due: Optional[str] = None
    credit_limit: Optional[str] = None
    available_credit: Optional[str] = None
    previous_balance: Optional[str] = None
    parsing_status: str = "success"
    errors: List[str] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


class CreditCardParser:
    """Parser for multiple credit card statement formats"""
    
    # Configuration for each issuer
    PARSERS = {
        'ICICI Bank': {
            'identifier': [
                r'ICICI\s+Bank',
                r'icicibank\.com',
                r'CIN.*L65190GJ1994PLC021012'
            ],
            'patterns': {
                'card_number': [
                    r'(\d{4}[X]{8}\d{4})',
                    r'(\d{16})'
                ],
                'statement_date': [
                    r'STATEMENT\s+DATE[:\s]*(\d{1,2}\s+\w+,?\s+\d{4})',
                    r'Statement\s+period\s*:.*to\s+(\w+\s+\d{1,2},\s+\d{4})'
                ],
                'payment_due_date': [
                    r'PAYMENT\s+DUE\s+DATE[:\s]*(\d{1,2}\s+\w+,?\s+\d{4})',
                    r'Payment\s+Due\s+Date[:\s]*(\w+\s+\d{1,2},\s+\d{4})'
                ],
                'total_amount_due': [
                    r'Total\s+Amount\s+due[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})',
                    r'Total\s+Payment\s+Due[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})'
                ],
                'minimum_amount_due': [
                    r'Minimum\s+Amount\s+due[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})',
                    r'Minimum\s+Payment\s+Due[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})'
                ],
                'credit_limit': [
                    r'Credit\s+Limit\s*\(Including\s+cash\)[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})',
                    r'Credit\s+Limit[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})'
                ],
                'available_credit': [
                    r'Available\s+Credit\s*\(Including\s+cash\)[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})'
                ],
                'previous_balance': [
                    r'Previous\s+Balance[:\s]*[₹`Rs\.?\s]*([0-9,]+\.?\d{0,2})'
                ]
            }
        },
        'Axis Bank': {
            'identifier': [
                r'Axis\s+Bank',
                r'axisbank\.com',
                r'AAACU2414K3ZD'
            ],
            'patterns': {
                'card_number': [
                    r'Card\s+No[:\s]*(\d{8}\*{4}\d{4})',
                    r'Card\s+No[:\s]*(\d{14}\*{4}\d{4})',
                    r'Credit\s+Card\s+Number[:\s]*(\d{8}\*{4}\d{4})'
                ],
                'statement_date': [
                    r'Statement\s+Generation\s+Date[:\s]*(\d{2}[\/\-]\d{2}[\/\-]\d{4})',
                    r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})\s*-\s*(\d{2}[\/\-]\d{2}[\/\-]\d{4})'
                ],
                'payment_due_date': [
                    r'Payment\s+Due\s+Date[:\s]*(\d{2}[\/\-]\d{2}[\/\-]\d{4})'
                ],
                'total_amount_due': [
                    r'Total\s+Payment\s+Due[:\s]*([0-9,]+\.?\d{0,2})\s*Dr',
                    r'Total\s+Amount\s+Due[:\s]*([0-9,]+\.?\d{0,2})'
                ],
                'minimum_amount_due': [
                    r'Minimum\s+Payment\s+Due[:\s]*([0-9,]+\.?\d{0,2})\s*Dr',
                    r'Minimum\s+Amount\s+Due[:\s]*([0-9,]+\.?\d{0,2})'
                ],
                'credit_limit': [
                    r'Credit\s+Limit[:\s]*([0-9,]+\.?\d{0,2})'
                ],
                'available_credit': [
                    r'Available\s+Credit\s+Limit[:\s]*([0-9,]+\.?\d{0,2})'
                ],
                'previous_balance': [
                    r'Previous\s+Balance[:\s]*-?\s*([0-9,]+\.?\d{0,2})\s*Dr'
                ]
            }
        },
        'IDFC FIRST Bank': {
            'identifier': [
                r'IDFC\s+FIRST\s+Bank',
                r'idfcfirstbank\.com',
                r'IDFB0010225'
            ],
            'patterns': {
                'card_number': [
                    r'Card\s+Number[:\s]*XXXX\s*(\d{4})',
                    r'Account\s+Number[:\s]*(\d+)'
                ],
                'statement_date': [
                    r'(\d{2}\/\d{2}\/\d{4})\s*-\s*(\d{2}\/\d{2}\/\d{4})'
                ],
                'payment_due_date': [
                    r'Payment\s+Due\s+Date[:\s]*(\d{2}\/\d{2}\/\d{4})'
                ],
                'total_amount_due': [
                    r'Total\s+Amount\s+Due[:\s]*r([0-9,]+\.?\d{0,2})'
                ],
                'minimum_amount_due': [
                    r'Minimum\s+Amount\s+Due[:\s]*r([0-9,]+\.?\d{0,2})'
                ],
                'credit_limit': [
                    r'Credit\s+Limit[:\s]*r([0-9,]+\.?\d{0,2})'
                ],
                'available_credit': [
                    r'Available\s+Credit\s+Limit[:\s]*r([0-9,]+\.?\d{0,2})'
                ]
            }
        },
        'RBL Bank': {
            'identifier': [
                r'RBL\s+Bank',
                r'rblbank\.com',
                r'L65191PN1943PLC007308'
            ],
            'patterns': {
                'card_number': [
                    r'(\d{4}\s*XXXX\s*XXXX\s*\d{4})',
                    r'(\d{4}\s*X{4}\s*X{4}\s*\d{4})'
                ],
                'statement_date': [
                    r'(\d{2}\/\d{2}\/\d{4})\s*to\s*(\d{2}\/\d{2}\/\d{4})'
                ],
                'payment_due_date': [
                    r'Immediate(\d{2}\/\d{2}\/\d{4})'
                ],
                'total_amount_due': [
                    r'([0-9,]+\.?\d{0,2})\s*\n\s*([0-9,]+\.?\d{0,2})\s*\n\s*0\.00'
                ],
                'minimum_amount_due': [
                    r'Minimum[^0-9]*([0-9,]+\.?\d{0,2})'
                ],
                'credit_limit': [
                    r'([0-9,]+\.?\d{0,2})\s*0\.00\s*0\.00'
                ]
            }
        },
        'American Express': {
            'identifier': [
                r'American\s+Express',
                r'americanexpress\.com',
                r'AMEX'
            ],
            'patterns': {
                'card_number': [
                    r'Account\s+Ending\s*(\d-\d{5})',
                    r'Card\s+Ending\s*(\d-\d{5})'
                ],
                'statement_date': [
                    r'Closing\s+Date[:\s]*(\d{2}\/\d{2}\/\d{2,4})'
                ],
                'payment_due_date': [
                    r'Payment\s+Due\s+Date[:\s]*(\d{2}\/\d{2}\/\d{2,4})'
                ],
                'total_amount_due': [
                    r'New\s+Balance[:\s]*\$([0-9,]+\.?\d{0,2})',
                    r'Total[:\s]*\$([0-9,]+\.?\d{0,2})'
                ],
                'minimum_amount_due': [
                    r'Minimum\s+Payment\s+Due[:\s]*\$([0-9,]+\.?\d{0,2})'
                ],
                'credit_limit': [
                    r'Pay\s+Over\s+Time\s+Limit[:\s]*\$([0-9,]+\.?\d{0,2})',
                    r'Credit\s+Limit[:\s]*\$([0-9,]+\.?\d{0,2})'
                ],
                'available_credit': [
                    r'Available\s+Pay\s+Over\s+Time\s+Limit[:\s]*\$([0-9,]+\.?\d{0,2})'
                ],
                'previous_balance': [
                    r'Previous\s+Balance[:\s]*\$([0-9,]+\.?\d{0,2})'
                ]
            }
        }
    }

    def __init__(self):
        self.results = []

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text from PDF using pdfplumber"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")

    def identify_issuer(self, text: str) -> Optional[str]:
        """Identify the credit card issuer from statement text"""
        for issuer, config in self.PARSERS.items():
            for pattern in config['identifier']:
                if re.search(pattern, text, re.IGNORECASE):
                    return issuer
        return None

    def extract_field(self, text: str, patterns: List[str]) -> Optional[str]:
        """Try multiple patterns to extract a field"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                # Return the last group if multiple groups exist
                groups = match.groups()
                return groups[-1] if groups else match.group(0)
        return None

    def parse_statement(self, pdf_path: Path) -> StatementData:
        """Parse a single credit card statement"""
        file_name = pdf_path.name
        
        try:
            # Extract text
            text = self.extract_text_from_pdf(pdf_path)
            
            # Identify issuer
            issuer = self.identify_issuer(text)
            
            if not issuer:
                return StatementData(
                    file_name=file_name,
                    issuer="Unknown",
                    parsing_status="failed",
                    errors=["Could not identify credit card issuer"]
                )
            
            # Get parser configuration
            config = self.PARSERS[issuer]
            
            # Extract all fields
            data = StatementData(file_name=file_name, issuer=issuer)
            errors = []
            
            for field, patterns in config['patterns'].items():
                value = self.extract_field(text, patterns)
                if value:
                    setattr(data, field, value.strip())
                else:
                    errors.append(f"Could not extract {field}")
            
            # Set errors if any
            if errors:
                data.errors = errors
                # Only mark as failed if no critical fields were extracted
                critical_fields = ['card_number', 'total_amount_due', 'payment_due_date']
                if all(getattr(data, f) is None for f in critical_fields):
                    data.parsing_status = "failed"
                else:
                    data.parsing_status = "partial"
            
            return data
            
        except Exception as e:
            return StatementData(
                file_name=file_name,
                issuer="Error",
                parsing_status="error",
                errors=[str(e)]
            )

    def parse_multiple(self, pdf_paths: List[Path]) -> List[StatementData]:
        """Parse multiple PDF statements"""
        self.results = []
        
        for pdf_path in pdf_paths:
            print(f"Processing: {pdf_path.name}...")
            result = self.parse_statement(pdf_path)
            self.results.append(result)
            
            # Print immediate feedback
            status_symbol = "✓" if result.parsing_status == "success" else "⚠" if result.parsing_status == "partial" else "✗"
            print(f"  {status_symbol} {result.issuer} - {result.parsing_status}")
        
        return self.results

    def to_dict(self) -> List[Dict]:
        """Convert results to dictionary format"""
        return [asdict(r) for r in self.results]

    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to pandas DataFrame"""
        return pd.DataFrame([asdict(r) for r in self.results])

    def to_json(self, output_path: Optional[Path] = None) -> str:
        """Export results as JSON"""
        data = self.to_dict()
        json_str = json.dumps(data, indent=2)
        
        if output_path:
            output_path.write_text(json_str)
            print(f"\nJSON exported to: {output_path}")
        
        return json_str

    def print_summary(self):
        """Print a formatted summary of results"""
        print("\n" + "="*80)
        print("PARSING SUMMARY")
        print("="*80)
        
        for result in self.results:
            print(f"\nFile: {result.file_name}")
            print(f"Issuer: {result.issuer}")
            print(f"Status: {result.parsing_status.upper()}")
            print("-" * 80)
            
            if result.parsing_status in ["success", "partial"]:
                fields = [
                    ("Card Number", result.card_number),
                    ("Statement Date", result.statement_date),
                    ("Payment Due Date", result.payment_due_date),
                    ("Total Amount Due", result.total_amount_due),
                    ("Minimum Amount Due", result.minimum_amount_due),
                    ("Credit Limit", result.credit_limit),
                    ("Available Credit", result.available_credit),
                    ("Previous Balance", result.previous_balance),
                ]
                
                for field_name, value in fields:
                    if value:
                        print(f"  {field_name:20s}: {value}")
            
            if result.errors:
                print(f"\n  Warnings/Errors:")
                for error in result.errors:
                    print(f"    - {error}")

    def print_table(self):
        """Print results as a formatted table"""
        if not self.results:
            print("No results to display")
            return
        
        df = self.to_dataframe()
        
        # Select key columns for display
        display_cols = [
            'file_name', 'issuer', 'card_number', 
            'statement_date', 'payment_due_date',
            'total_amount_due', 'minimum_amount_due', 
            'parsing_status'
        ]
        
        # Filter to existing columns
        display_cols = [col for col in display_cols if col in df.columns]
        
        print("\n" + "="*80)
        print("PARSED DATA TABLE")
        print("="*80 + "\n")
        print(tabulate(df[display_cols], headers='keys', tablefmt='grid', showindex=False))


def main():
    parser = argparse.ArgumentParser(
        description='Parse credit card statements from multiple issuers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parser.py statement1.pdf statement2.pdf
  python parser.py --dir ./statements/
  python parser.py *.pdf --json output.json
  python parser.py statement.pdf --format table
        """
    )
    
    parser.add_argument('files', nargs='*', help='PDF files to parse')
    parser.add_argument('--dir', '-d', help='Directory containing PDF files')
    parser.add_argument('--json', '-j', help='Export results to JSON file')
    parser.add_argument('--format', '-f', choices=['summary', 'table', 'both'], 
                       default='both', help='Output format (default: both)')
    
    args = parser.parse_args()
    
    # Collect PDF files
    pdf_files = []
    
    if args.dir:
        dir_path = Path(args.dir)
        if not dir_path.exists():
            print(f"Error: Directory not found: {args.dir}")
            sys.exit(1)
        pdf_files.extend(dir_path.glob("*.pdf"))
        pdf_files.extend(dir_path.glob("*.PDF"))
    
    if args.files:
        for file in args.files:
            path = Path(file)
            if path.exists():
                pdf_files.append(path)
            else:
                print(f"Warning: File not found: {file}")
    
    if not pdf_files:
        print("No PDF files found. Use --help for usage information.")
        sys.exit(1)
    
    # Initialize parser
    cc_parser = CreditCardParser()
    
    # Parse statements
    print(f"\nParsing {len(pdf_files)} statement(s)...\n")
    cc_parser.parse_multiple(pdf_files)
    
    # Output results
    if args.format in ['summary', 'both']:
        cc_parser.print_summary()
    
    if args.format in ['table', 'both']:
        cc_parser.print_table()
    
    # Export to JSON if requested
    if args.json:
        cc_parser.to_json(Path(args.json))
    
    # Print statistics
    total = len(cc_parser.results)
    success = sum(1 for r in cc_parser.results if r.parsing_status == "success")
    partial = sum(1 for r in cc_parser.results if r.parsing_status == "partial")
    failed = sum(1 for r in cc_parser.results if r.parsing_status == "failed")
    
    print("\n" + "="*80)
    print(f"Total: {total} | Success: {success} | Partial: {partial} | Failed: {failed}")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()