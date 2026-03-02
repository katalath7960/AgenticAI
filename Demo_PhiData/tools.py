import sqlite3
from typing import Optional
from phi.tools import Toolkit


class CustomSQLTools(Toolkit):
    """Custom SQLite toolkit with analytics helpers for PhiData agents."""

    def __init__(self, db_path: str):
        super().__init__(name="custom_sql_tools")
        self.db_path = db_path
        self.register(self.get_schema)
        self.register(self.run_query)
        self.register(self.get_top_products)
        self.register(self.get_sales_by_region)
        self.register(self.get_monthly_trends)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_schema(self) -> str:
        """Returns the schema of all tables in the database."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        result = []
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = cursor.fetchall()
            col_info = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            result.append(f"Table: {table} ({count} rows)\nColumns: {col_info}")
        conn.close()
        return "\n\n".join(result)

    def run_query(self, query: str) -> str:
        """Executes a SQL query and returns the results as a formatted string.

        Args:
            query: SQL query to execute (SELECT only for safety).
        """
        if not query.strip().upper().startswith("SELECT"):
            return "Error: Only SELECT queries are allowed."
        try:
            conn = self._connect()
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            conn.close()
            if not rows:
                return "Query returned no results."
            headers = list(rows[0].keys())
            lines = [" | ".join(headers)]
            lines.append("-" * len(lines[0]))
            for row in rows:
                lines.append(" | ".join(str(row[h]) for h in headers))
            return "\n".join(lines)
        except Exception as e:
            return f"Query error: {e}"

    def get_top_products(self, limit: int = 5) -> str:
        """Returns the top-selling products by total revenue.

        Args:
            limit: Number of top products to return (default 5).
        """
        query = f"""
            SELECT product, SUM(quantity) AS total_units, SUM(total_revenue) AS total_revenue
            FROM sales
            GROUP BY product
            ORDER BY total_revenue DESC
            LIMIT {limit}
        """
        return self.run_query(query)

    def get_sales_by_region(self) -> str:
        """Returns total revenue and units sold broken down by region."""
        query = """
            SELECT region, SUM(quantity) AS total_units, SUM(total_revenue) AS total_revenue
            FROM sales
            GROUP BY region
            ORDER BY total_revenue DESC
        """
        return self.run_query(query)

    def get_monthly_trends(self) -> str:
        """Returns monthly revenue and transaction count trends."""
        query = """
            SELECT month, COUNT(*) AS transactions, SUM(quantity) AS total_units,
                   SUM(total_revenue) AS total_revenue
            FROM sales
            GROUP BY month
            ORDER BY month
        """
        return self.run_query(query)
