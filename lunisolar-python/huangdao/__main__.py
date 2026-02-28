"""CLI entry point for ``python -m huangdao``."""

import argparse
import io
import sys

from .calculator import HuangdaoCalculator


def main() -> None:
    # Ensure stdout can handle CJK characters on Windows
    if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    parser = argparse.ArgumentParser(
        description='Efficient Huangdao Systems Calculator - Print monthly calendar tables',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --year 2025 --month 10
  %(prog)s -y 2025 -m 1 --timezone Asia/Shanghai
  %(prog)s -y 2024 -m 12 -tz Asia/Tokyo

Legend:
  Construction Stars (十二建星):
    🟨 Yellow: Auspicious (除危定执) - Score 4
    🟩 Green: Moderate (成开) - Score 3
    ⬛ Black: Inauspicious (建满平收) - Score 2
    🟥 Red: Very Inauspicious (破闭) - Score 1

  Great Yellow Path (大黄道):
    🟡 Yellow Path (黄道): Auspicious days
    ⚫ Black Path (黑道): Inauspicious days
        """
    )
    parser.add_argument('--year', '-y', type=int, required=True,
                        help='Gregorian year (e.g., 2025)')
    parser.add_argument('--month', '-m', type=int, required=True,
                        help='Month number (1-12)')
    parser.add_argument('--timezone', '-tz', default='Asia/Ho_Chi_Minh',
                        help='Timezone (IANA format, default: Asia/Ho_Chi_Minh)')

    args = parser.parse_args()

    if not 1 <= args.month <= 12:
        parser.error("Month must be between 1 and 12")

    calculator = HuangdaoCalculator(args.timezone)
    calculator.print_month_calendar(args.year, args.month)


if __name__ == "__main__":
    main()
