from mcp_server.config import get_config
from mcp_server.db.connection import get_connection

def main():
    cfg = get_config()
    print("Config:", cfg.database)

    db = get_connection()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        # OpenEdge doesn't support "SELECT 1", use sysprogress.syscalctable instead
        cursor.execute("SELECT 1 AS test_value FROM sysprogress.syscalctable")
        row = cursor.fetchone()
        print("DB test result:", row)

if __name__ == "__main__":
    main()
