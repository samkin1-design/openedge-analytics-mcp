"""Test OEE query with real data - 2024 only."""
from mcp_server.config import get_config
from mcp_server.db.connection import get_connection

def main():
    cfg = get_config()
    db = get_connection()

    print("=== Checking op_hist table (2024 data only) ===")
    with db.get_connection() as conn:
        cursor = conn.cursor()

        # Get sample Work Centers (op_wkctr) from 2024
        print("\n1. Sample Work Centers (op_wkctr) in 2024:")
        cursor.execute(f"""
            SELECT DISTINCT TOP 10 op_wkctr
            FROM {cfg.analytics_schema}.op_hist
            WHERE op_wkctr IS NOT NULL AND op_wkctr <> ''
              AND op_date >= '2024-01-01' AND op_date < '2025-01-01'
        """)
        wkctrs = cursor.fetchall()
        for row in wkctrs:
            print(f"  - {row[0]}")

        # Get sample sites from 2024
        print("\n2. Sample Sites (op_site) in 2024:")
        cursor.execute(f"""
            SELECT DISTINCT TOP 10 op_site
            FROM {cfg.analytics_schema}.op_hist
            WHERE op_site IS NOT NULL AND op_site <> ''
              AND op_date >= '2024-01-01' AND op_date < '2025-01-01'
        """)
        sites = cursor.fetchall()
        for row in sites:
            print(f"  - {row[0]}")

        # Get a sample record to see available columns
        print("\n3. Sample record with key columns (2024):")
        cursor.execute(f"""
            SELECT TOP 1
                op_wkctr, op_site, op_date, op_wo_nbr, op_part,
                op_act_run, op_std_run, op_qty_comp, op_qty_scrap, op_qty_rjct
            FROM {cfg.analytics_schema}.op_hist
            WHERE op_date >= '2024-01-01' AND op_date < '2025-01-01'
        """)
        sample = cursor.fetchone()
        if sample:
            print(f"  op_wkctr: {sample[0]}")
            print(f"  op_site: {sample[1]}")
            print(f"  op_date: {sample[2]}")
            print(f"  op_wo_nbr: {sample[3]}")
            print(f"  op_part: {sample[4]}")
            print(f"  op_act_run: {sample[5]}")
            print(f"  op_std_run: {sample[6]}")
            print(f"  op_qty_comp: {sample[7]}")
            print(f"  op_qty_scrap: {sample[8]}")
            print(f"  op_qty_rjct: {sample[9]}")

        # Get record count for 2024
        print("\n4. Record count for 2024:")
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {cfg.analytics_schema}.op_hist
            WHERE op_date >= '2024-01-01' AND op_date < '2025-01-01'
        """)
        count = cursor.fetchone()[0]
        print(f"  {count} records")

if __name__ == "__main__":
    main()
