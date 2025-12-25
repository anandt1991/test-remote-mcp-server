from fastmcp import FastMCP
import os
import tempfile
import sqlite3
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import base64




class ExpenseInput(BaseModel):
    date: str = Field(..., description="The date of the expense in YYYY-MM-DD format")
    amount: float = Field(..., description="The amount of the expense")
    category: str = Field(..., description="The category of the expense")
    subcategory: Optional[str] = Field(None, description="The subcategory of the expense")
    note: Optional[str] = Field(None, description="Any additional notes about the expense")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")

# Use temporary directory which should be writable
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")

print(f"Database path: {DB_PATH}")

#DB_PATH = os.path.join(os.path.dirname(__file__), "expense.db")

mcp = FastMCP("Expense Tracker")

def init_db():
        with sqlite3.connect(DB_PATH) as c:
            c.execute("PRAGMA journal_mode=WAL")
            c.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)


init_db()

@mcp.tool
def add_expense(expense: ExpenseInput):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("INSERT INTO expenses (date, amount, category, subcategory, note) VALUES (?, ?, ?, ?, ?)"
                              , (expense.date, expense.amount, expense.category, expense.subcategory, expense.note))
        return{"status": "success", "message": f"Expense added with ID {cursor.lastrowid}"}

@mcp.tool
def list_expenses() -> list:
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT * FROM expenses order by ID")
        cols = [column[0] for column in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

@mcp.tool
def delete_expense(expense_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return {"status": "success", "message": f"Expense with ID {expense_id} deleted"}
    
@mcp.tool
def summarize_expenses(summarize_sql: str):
    """
    This function summarizes expenses based on user columns. The function takes only select clause
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(summarize_sql)
        cols = [column[0] for column in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]




@mcp.tool
def export_database():
    """Export the SQLite database as base64"""
    with open(DB_PATH, "rb") as f:
        data = f.read()
    return {
        "filename": "expense.db",
        "base64": base64.b64encode(data).decode("utf-8")
    }


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)