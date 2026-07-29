"""Interactive smoke test for the CGV tools.

Run from starter_v0:
    python scripts/test_cgv.py

This script never prints the CGV password or access token.
"""

from __future__ import annotations

from getpass import getpass
from pathlib import Path
from pprint import pprint
import sys


# Let beginners run `python scripts/test_cgv.py` from either this folder or its
# parent, without having to configure PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.cgv.movies.tool import cgv_movie_list
from tools.cgv.profile.tool import cgv_profile
from tools.cgv.session import authenticate, session_scope


def test_public_movies() -> None:
    """Confirm a public CGV endpoint works without an account."""
    print("\nĐang lấy tối đa 3 phim CGV...")
    pprint(cgv_movie_list(limit=3), sort_dicts=False)


def test_authenticated_profile() -> None:
    """Login server-side, then call an authenticated tool in one request scope."""
    email = input("Email CGV: ").strip()
    password = getpass("Mật khẩu CGV (sẽ không hiện khi gõ): ")

    print("\nĐang đăng nhập vào CGV...")
    session = authenticate(email, password)
    print("Đăng nhập thành công. Đang lấy hồ sơ thành viên...")

    # This is the same boundary the web backend uses for one agent request.
    # The token stays in this process and is never passed to the CGV tool.
    with session_scope(session.customer_id, session.u_token):
        pprint(cgv_profile(), sort_dicts=False)


def test_unauthenticated_error() -> None:
    """Confirm protected tools refuse calls when no web session is installed."""
    print("\nGọi profile khi chưa có phiên đăng nhập...")
    pprint(cgv_profile(), sort_dicts=False)


def main() -> None:
    print("CGV tool test")
    print("1. Test danh sách phim công khai (không cần đăng nhập)")
    print("2. Test đăng nhập và xem profile")
    print("3. Test bị chặn khi chưa đăng nhập")
    choice = input("Chọn 1, 2 hoặc 3: ").strip()

    if choice == "1":
        test_public_movies()
    elif choice == "2":
        test_authenticated_profile()
    elif choice == "3":
        test_unauthenticated_error()
    else:
        print("Lựa chọn không hợp lệ. Hãy chạy lại và chọn 1, 2 hoặc 3.")


if __name__ == "__main__":
    main()
