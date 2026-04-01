#!/usr/bin/env python3
"""
Odoo MCP Server for AI Employee

Model Context Protocol (MCP) server for Odoo ERP integration.
Supports Odoo Community Edition via JSON-RPC API (Odoo 19+).

Features:
- Create/manage invoices
- Record payments
- Manage customers/vendors
- Generate financial reports
- Full audit logging

Setup:
    1. Install Odoo Community Edition (local or cloud)
    2. Create database user with appropriate permissions
    3. Configure credentials in .env or credentials.json
    4. Run: python odoo_mcp_server.py --test

Usage:
    # Run as stdio MCP server
    python odoo_mcp_server.py

    # Or with specific config
    python odoo_mcp_server.py --config PATH

Reference:
    Odoo External API: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

# Try to import MCP libraries
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("WARNING: MCP library not installed. Run: pip install mcp")

# Try to import requests for Odoo API
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("WARNING: requests library not installed. Run: pip install requests")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('odoo_mcp_server')


class OdooClient:
    """
    Odoo JSON-RPC API client.

    Supports Odoo 19+ Community Edition.
    """

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Initialize Odoo client.

        Args:
            url: Odoo server URL (e.g., http://localhost:8069)
            db: Database name
            username: Odoo username (email)
            password: Odoo password or API key
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password

        # Session for authentication
        self.session = requests.Session()
        self.uid = None

        # Authenticate
        self._authenticate()

    def _authenticate(self):
        """Authenticate with Odoo and get session."""
        try:
            # For Odoo Community, we use the session-based authentication
            login_url = f"{self.url}/web/session/authenticate"

            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.db,
                    "login": self.username,
                    "password": self.password,
                    "base_context": {}
                }
            }

            response = self.session.post(login_url, json=payload, timeout=30)
            result = response.json()

            if result.get('result', {}).get('uid'):
                self.uid = result['result']['uid']
                logger.info(f'Authenticated with Odoo. UID: {self.uid}')
            else:
                logger.error('Odoo authentication failed')
                raise Exception('Odoo authentication failed')

        except Exception as e:
            logger.error(f'Odoo connection error: {e}')
            raise

    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        """
        Execute a method on an Odoo model.

        Args:
            model: Odoo model name (e.g., 'account.move')
            method: Method to call (e.g., 'create', 'search', 'write')
            *args: Positional arguments for the method
            **kwargs: Keyword arguments for the method

        Returns:
            Method result
        """
        if not self.uid:
            raise Exception('Not authenticated')

        try:
            execute_url = f"{self.url}/web/dataset/call_kw"

            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "model": model,
                    "method": method,
                    "args": list(args),
                    "kwargs": kwargs
                }
            }

            response = self.session.post(execute_url, json=payload, timeout=30)
            result = response.json()

            if 'error' in result:
                error = result['error']
                raise Exception(f"Odoo error: {error.get('message', 'Unknown error')}")

            return result.get('result', {})

        except Exception as e:
            logger.error(f'Odoo execute error: {e}')
            raise

    def search(self, model: str, domain: List, limit: int = 80) -> List[int]:
        """Search for records."""
        return self._execute(model, 'search', domain, limit=limit)

    def search_read(self, model: str, domain: List, fields: List[str] = None,
                    limit: int = 80) -> List[Dict]:
        """Search and read records."""
        return self._execute(model, 'search_read', domain, fields=fields or [], limit=limit)

    def create(self, model: str, values: Dict) -> int:
        """Create a record."""
        return self._execute(model, 'create', [values])

    def write(self, model: str, ids: List[int], values: Dict) -> bool:
        """Update records."""
        return self._execute(model, 'write', ids, values)

    def unlink(self, model: str, ids: List[int]) -> bool:
        """Delete records."""
        return self._execute(model, 'unlink', ids)

    def get_record(self, model: str, record_id: int, fields: List[str] = None) -> Dict:
        """Get a single record."""
        results = self.search_read(model, [('id', '=', record_id)], fields=fields, limit=1)
        return results[0] if results else None

    # Invoice methods
    def create_invoice(self, partner_id: int, invoice_type: str = 'out_invoice',
                       lines: List[Dict] = None, payment_term: int = None) -> int:
        """
        Create a customer invoice.

        Args:
            partner_id: Customer ID
            invoice_type: 'out_invoice' (customer) or 'in_invoice' (vendor)
            lines: Invoice line items [{'product_id': X, 'quantity': Y, 'price_unit': Z}]
            payment_term: Payment term ID

        Returns:
            Invoice ID
        """
        values = {
            'move_type': invoice_type,
            'partner_id': partner_id,
            'invoice_date': datetime.now().strftime('%Y-%m-%d'),
            'invoice_payment_term_id': payment_term,
        }

        invoice_id = self.create('account.move', values)

        # Add invoice lines
        if lines and invoice_id:
            for line in lines:
                line['move_id'] = invoice_id
                self.create('account.move.line', line)

            # Recompute invoice totals
            self._execute('account.move', 'action_post', [invoice_id])

        return invoice_id

    def get_invoices(self, partner_id: int = None, state: str = 'posted',
                     limit: int = 50) -> List[Dict]:
        """
        Get invoices.

        Args:
            partner_id: Filter by customer/vendor
            state: Invoice state (draft, posted, cancel)
            limit: Maximum results

        Returns:
            List of invoice records
        """
        domain = []
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        if state:
            domain.append(('state', '=', state))

        fields = [
            'id', 'name', 'partner_id', 'amount_total', 'amount_due',
            'invoice_date', 'invoice_date_due', 'state', 'move_type'
        ]

        return self.search_read('account.move', domain, fields=fields, limit=limit)

    def register_payment(self, invoice_id: int, amount: float,
                         payment_date: str = None, reference: str = None) -> Dict:
        """
        Register a payment for an invoice.

        Args:
            invoice_id: Invoice ID
            amount: Payment amount
            payment_date: Payment date (YYYY-MM-DD)
            reference: Payment reference

        Returns:
            Payment result
        """
        try:
            # Use Odoo's payment wizard
            wizard_result = self._execute(
                'account.payment.register',
                'create',
                {
                    'invoice_ids': [invoice_id],
                    'amount': amount,
                    'payment_date': payment_date or datetime.now().strftime('%Y-%m-%d'),
                    'payment_reference': reference or f'Payment for {invoice_id}'
                }
            )

            # Create the payment
            payment_id = wizard_result.get('id')
            if payment_id:
                self._execute('account.payment.register', 'create_payments', [payment_id])

            return {
                'success': True,
                'invoice_id': invoice_id,
                'amount': amount,
                'payment_date': payment_date
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    # Partner (Customer/Vendor) methods
    def get_partner(self, name: str = None, email: str = None) -> Optional[Dict]:
        """Find a partner by name or email."""
        domain = []
        if name:
            domain.append(('name', 'ilike', name))
        if email:
            domain.append(('email', '=', email))

        results = self.search_read('res.partner', domain, limit=1)
        return results[0] if results else None

    def create_partner(self, name: str, email: str = None, phone: str = None,
                       is_company: bool = True, customer: bool = True) -> int:
        """Create a customer/vendor."""
        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'is_company': is_company,
            'customer_rank': 1 if customer else 0
        }
        return self.create('res.partner', values)

    # Report methods
    def get_financial_summary(self, period_start: str = None,
                              period_end: str = None) -> Dict:
        """
        Get financial summary.

        Args:
            period_start: Start date (YYYY-MM-DD)
            period_end: End date (YYYY-MM-DD)

        Returns:
            Financial summary dictionary
        """
        today = datetime.now().strftime('%Y-%m-%d')
        period_start = period_start or today.replace(day=1)
        period_end = period_end or today

        # Get invoices
        invoices = self.get_invoices(state='posted')

        total_revenue = sum(
            inv.get('amount_total', 0)
            for inv in invoices
            if inv.get('move_type') == 'out_invoice'
        )

        total_expenses = sum(
            inv.get('amount_total', 0)
            for inv in invoices
            if inv.get('move_type') == 'in_invoice'
        )

        # Get outstanding receivables
        receivables = sum(
            inv.get('amount_due', 0)
            for inv in invoices
            if inv.get('move_type') == 'out_invoice' and inv.get('amount_due', 0) > 0
        )

        return {
            'period_start': period_start,
            'period_end': period_end,
            'total_revenue': total_revenue,
            'total_expenses': total_expenses,
            'net_income': total_revenue - total_expenses,
            'outstanding_receivables': receivables,
            'invoice_count': len(invoices)
        }


class OdooMCPServer:
    """Odoo MCP Server implementation."""

    def __init__(self, vault_path: str, config_path: str = None):
        self.vault_path = Path(vault_path)
        self.config_path = Path(config_path) if config_path else (
            self.vault_path / 'credentials' / 'odoo_config.json'
        )
        self.logs_path = self.vault_path / 'logs'

        # Ensure directories exist
        self.logs_path.mkdir(parents=True, exist_ok=True)
        (self.vault_path / 'credentials').mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.config = self._load_config()
        self.client = None

        # Initialize Odoo client if config available
        if self.config:
            try:
                self.client = OdooClient(
                    url=self.config.get('url', 'http://localhost:8069'),
                    db=self.config.get('database', 'odoo'),
                    username=self.config.get('username', 'admin'),
                    password=self.config.get('password', '')
                )
                logger.info('Odoo client initialized')
            except Exception as e:
                logger.error(f'Failed to initialize Odoo client: {e}')

    def _load_config(self) -> Optional[Dict]:
        """Load Odoo configuration."""
        if self.config_path.exists():
            try:
                config = json.loads(self.config_path.read_text(encoding='utf-8'))
                logger.info(f'Loaded Odoo config from: {self.config_path}')
                return config
            except Exception as e:
                logger.error(f'Error loading config: {e}')

        # Check environment variables
        if os.environ.get('ODOO_URL'):
            return {
                'url': os.environ.get('ODOO_URL', 'http://localhost:8069'),
                'database': os.environ.get('ODOO_DB', 'odoo'),
                'username': os.environ.get('ODOO_USERNAME', 'admin'),
                'password': os.environ.get('ODOO_PASSWORD', '')
            }

        return None

    def save_config(self, config: Dict):
        """Save Odoo configuration."""
        self.config_path.write_text(json.dumps(config, indent=2), encoding='utf-8')
        self.config_path.chmod(0o600)
        logger.info(f'Saved Odoo config to: {self.config_path}')

    def _log_action(self, action_type: str, details: Dict[str, Any]):
        """Log an action to the audit log."""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': 'odoo_mcp_server',
            'parameters': details,
            'result': 'success' if 'error' not in details else 'failed'
        }

        log_file = self.logs_path / f'odoo_mcp_{datetime.now().strftime("%Y%m%d")}.json'

        logs = []
        if log_file.exists():
            try:
                logs = json.loads(log_file.read_text())
            except json.JSONDecodeError:
                logs = []

        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))


# Create MCP server instance
if MCP_AVAILABLE:
    app = Server("odoo-mcp")
else:
    app = None


def setup_mcp_server(odoo_server: OdooMCPServer):
    """Set up MCP server tools."""

    @app.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="odoo_create_invoice",
                description="Create a new invoice in Odoo. Use for billing customers.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "partner_id": {
                            "type": "integer",
                            "description": "Customer ID in Odoo"
                        },
                        "invoice_type": {
                            "type": "string",
                            "enum": ["out_invoice", "in_invoice"],
                            "description": "Customer or vendor invoice"
                        },
                        "lines": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "product_id": {"type": "integer"},
                                    "quantity": {"type": "number"},
                                    "price_unit": {"type": "number"},
                                    "name": {"type": "string"}
                                }
                            },
                            "description": "Invoice line items"
                        }
                    },
                    "required": ["partner_id"]
                }
            ),
            Tool(
                name="odoo_get_invoices",
                description="Search and retrieve invoices from Odoo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "partner_id": {
                            "type": "integer",
                            "description": "Filter by customer ID"
                        },
                        "state": {
                            "type": "string",
                            "enum": ["draft", "posted", "cancel"],
                            "description": "Invoice state"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results",
                            "default": 50
                        }
                    }
                }
            ),
            Tool(
                name="odoo_register_payment",
                description="Register a payment for an invoice in Odoo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "invoice_id": {
                            "type": "integer",
                            "description": "Invoice ID to pay"
                        },
                        "amount": {
                            "type": "number",
                            "description": "Payment amount"
                        },
                        "payment_date": {
                            "type": "string",
                            "description": "Payment date (YYYY-MM-DD)"
                        },
                        "reference": {
                            "type": "string",
                            "description": "Payment reference"
                        }
                    },
                    "required": ["invoice_id", "amount"]
                }
            ),
            Tool(
                name="odoo_get_partner",
                description="Find a customer/vendor in Odoo by name or email.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Partner name to search"
                        },
                        "email": {
                            "type": "string",
                            "description": "Partner email to search"
                        }
                    }
                }
            ),
            Tool(
                name="odoo_create_partner",
                description="Create a new customer/vendor in Odoo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Partner name"
                        },
                        "email": {
                            "type": "string",
                            "description": "Email address"
                        },
                        "phone": {
                            "type": "string",
                            "description": "Phone number"
                        },
                        "is_company": {
                            "type": "boolean",
                            "description": "Is this a company?"
                        },
                        "customer": {
                            "type": "boolean",
                            "description": "Is this a customer?"
                        }
                    },
                    "required": ["name"]
                }
            ),
            Tool(
                name="odoo_financial_summary",
                description="Get financial summary from Odoo.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "period_start": {
                            "type": "string",
                            "description": "Start date (YYYY-MM-DD)"
                        },
                        "period_end": {
                            "type": "string",
                            "description": "End date (YYYY-MM-DD)"
                        }
                    }
                }
            )
        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls."""
        if not odoo_server.client:
            return [TextContent(
                type="text",
                text=json.dumps({"error": "Odoo client not initialized. Configure credentials first."})
            )]

        result = None

        try:
            if name == "odoo_create_invoice":
                result = odoo_server.client.create_invoice(
                    partner_id=arguments.get("partner_id"),
                    invoice_type=arguments.get("invoice_type", "out_invoice"),
                    lines=arguments.get("lines")
                )
                odoo_server._log_action('invoice_created', {'invoice_id': result})

            elif name == "odoo_get_invoices":
                result = odoo_server.client.get_invoices(
                    partner_id=arguments.get("partner_id"),
                    state=arguments.get("state", "posted"),
                    limit=arguments.get("limit", 50)
                )

            elif name == "odoo_register_payment":
                result = odoo_server.client.register_payment(
                    invoice_id=arguments.get("invoice_id"),
                    amount=arguments.get("amount"),
                    payment_date=arguments.get("payment_date"),
                    reference=arguments.get("reference")
                )
                odoo_server._log_action('payment_registered', result)

            elif name == "odoo_get_partner":
                result = odoo_server.client.get_partner(
                    name=arguments.get("name"),
                    email=arguments.get("email")
                )

            elif name == "odoo_create_partner":
                result = odoo_server.client.create_partner(
                    name=arguments.get("name"),
                    email=arguments.get("email"),
                    phone=arguments.get("phone"),
                    is_company=arguments.get("is_company", True),
                    customer=arguments.get("customer", True)
                )
                odoo_server._log_action('partner_created', {'partner_id': result})

            elif name == "odoo_financial_summary":
                result = odoo_server.client.get_financial_summary(
                    period_start=arguments.get("period_start"),
                    period_end=arguments.get("period_end")
                )

            else:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            return [TextContent(
                type="text",
                text=json.dumps({"error": str(e)})
            )]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Odoo MCP Server for AI Employee',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python odoo_mcp_server.py --configure        # Interactive configuration
  python odoo_mcp_server.py --test             # Test connection
  python odoo_mcp_server.py                    # Run as stdio MCP server

Setup:
  1. Install Odoo Community Edition
  2. Create database user
  3. Run: python odoo_mcp_server.py --configure
        '''
    )

    parser.add_argument(
        '--vault-path',
        type=str,
        default=None,
        help='Path to Obsidian vault'
    )

    parser.add_argument(
        '--config',
        type=str,
        help='Path to config file'
    )

    parser.add_argument(
        '--configure',
        action='store_true',
        help='Interactive configuration'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test Odoo connection'
    )

    args = parser.parse_args()

    # Determine vault path
    if args.vault_path:
        vault_path = args.vault_path
    else:
        vault_path = str(Path(__file__).parent.parent)

    # Create server
    if not REQUESTS_AVAILABLE:
        print("ERROR: requests library required. Install with: pip install requests")
        sys.exit(1)

    odoo_server = OdooMCPServer(vault_path, args.config)

    # Interactive configuration
    if args.configure:
        print("Odoo Configuration")
        print("=" * 40)
        config = {
            'url': input("Odoo URL (http://localhost:8069): ") or 'http://localhost:8069',
            'database': input("Database name (odoo): ") or 'odoo',
            'username': input("Username (admin): ") or 'admin',
            'password': input("Password: ")
        }
        odoo_server.save_config(config)
        print("✓ Configuration saved")
        return

    # Test connection
    if args.test:
        if not odoo_server.client:
            print("✗ Odoo client not initialized. Run --configure first.")
            sys.exit(1)

        print("Testing Odoo connection...")
        try:
            summary = odoo_server.client.get_financial_summary()
            print("✓ Connection successful!")
            print(f"  Financial Summary: {json.dumps(summary, indent=2)}")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            sys.exit(1)
        return

    # Check MCP availability
    if not MCP_AVAILABLE:
        print("ERROR: MCP library required. Install with: pip install mcp")
        sys.exit(1)

    # Check if configured
    if not odoo_server.client:
        print("ERROR: Odoo not configured. Run: python odoo_mcp_server.py --configure")
        sys.exit(1)

    # Set up MCP server
    setup_mcp_server(odoo_server)

    print("Odoo MCP Server starting...")
    print("Ready to handle Odoo tools via MCP protocol.")

    # Run the server using stdio
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    import asyncio
    asyncio.run(run())


if __name__ == '__main__':
    main()
