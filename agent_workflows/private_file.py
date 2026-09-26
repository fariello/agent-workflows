"""Create a file readable and writable by the CURRENT USER ONLY, on every OS. Stdlib only.

WHY. Two files in this package hold secrets: the per-run driver attestation token (whoever can
read it can forge a driver attestation) and the analytics pseudonym salt. Both were created with
``os.open(..., 0o600)``. On POSIX that is owner-only. On Windows the mode argument is IGNORED apart
from the read-only bit, so the file silently inherited its folder's ACL, which in a shared or
redirected folder can grant other local accounts read access.

HOW, ON WINDOWS. The file is created by ``CreateFileW`` with an EXPLICIT security descriptor, built
from the SDDL ``D:P(A;;FA;;;<current user SID>)``:

* ``D:``    the DACL follows;
* ``P``     PROTECTED: it does NOT inherit ACEs from the parent folder;
* ``(A;;FA;;;<SID>)`` one ALLOW entry granting FILE_ALL_ACCESS to the current user, and no other.

Setting it AT CREATION (rather than creating then tightening) matters: there is no window in which
the secret exists under the inherited, possibly broader, ACL. Administrators and SYSTEM keep their
privilege-based ability to take ownership; that is the same boundary root has over a 0600 file.

Everything is plain ``ctypes`` against advapi32/kernel32, so no runtime dependency is added.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union

__all__ = [
    "create_private_file",
    "owner_only_sddl",
    "read_file_sddl",
    "sddl_is_owner_only",
]

PathLike = Union[str, "os.PathLike[str]", Path]


def create_private_file(path: PathLike, data: bytes) -> None:
    """Create ``path`` EXCLUSIVELY (fail if it exists) as owner-only, and write ``data``.

    POSIX: ``O_CREAT | O_EXCL`` with mode 0600. Windows: see the module docstring.
    Raises ``FileExistsError`` if ``path`` exists, and ``OSError`` for any other failure, so a
    caller never ends up with a secret written under a permissive ACL.
    """

    target = os.fspath(path)
    if os.name != "nt":
        fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            os.write(fd, data)
        finally:
            os.close(fd)
        return
    _create_private_file_windows(
        target, data
    )  # pragma: no cover - exercised on Windows CI


def owner_only_sddl() -> str:  # pragma: no cover - Windows only
    """The SDDL of the owner-only DACL for the CURRENT user: ``D:P(A;;FA;;;<SID>)``."""

    return f"D:P(A;;FA;;;{_current_user_sid()})"


def read_file_sddl(path: PathLike) -> Optional[str]:  # pragma: no cover - Windows only
    """The DACL of ``path`` as an SDDL string (``D:...``), or ``None`` off Windows.

    Used by the tests to prove, from the OS rather than from our own bookkeeping, that a private
    file carries exactly one ACE and no inherited ones.
    """

    if os.name != "nt":
        return None
    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    DACL_SECURITY_INFORMATION = 0x00000004
    SDDL_REVISION_1 = 1

    advapi32.GetFileSecurityW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.GetFileSecurityW.restype = wintypes.BOOL
    needed = wintypes.DWORD(0)
    advapi32.GetFileSecurityW(
        os.fspath(path), DACL_SECURITY_INFORMATION, None, 0, ctypes.byref(needed)
    )
    buf = ctypes.create_string_buffer(needed.value)
    if not advapi32.GetFileSecurityW(
        os.fspath(path), DACL_SECURITY_INFORMATION, buf, needed, ctypes.byref(needed)
    ):
        raise ctypes.WinError(ctypes.get_last_error())

    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes = [
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.LPWSTR),
        ctypes.POINTER(wintypes.ULONG),
    ]
    advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW.restype = (
        wintypes.BOOL
    )
    out = wintypes.LPWSTR()
    if not advapi32.ConvertSecurityDescriptorToStringSecurityDescriptorW(
        buf, SDDL_REVISION_1, DACL_SECURITY_INFORMATION, ctypes.byref(out), None
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return out.value
    finally:
        kernel32.LocalFree(out)


def sddl_is_owner_only(sddl: Optional[str], sid: str) -> Optional[str]:
    """``None`` when ``sddl`` is a PROTECTED DACL with exactly one non-inherited ALLOW-FA ACE for
    ``sid``; otherwise a short reason. STRUCTURAL rather than string equality, because Windows
    canonicalizes a descriptor on read-back (e.g. adding the ``AI`` auto-inherited flag)."""

    import re

    m = re.fullmatch(r"D:([A-Z]*)((?:\([^)]*\))*)", sddl or "")
    if not m:
        return f"not a DACL SDDL: {sddl!r}"
    flags, aces = m.group(1), re.findall(r"\(([^)]*)\)", m.group(2))
    if "P" not in flags:
        return f"DACL is not PROTECTED (inherits from its folder): {sddl!r}"
    if len(aces) != 1:
        return f"expected exactly one ACE, got {len(aces)}: {sddl!r}"
    parts = aces[0].split(";")
    if len(parts) != 6:
        return f"unparseable ACE {aces[0]!r}"
    ace_type, ace_flags, rights, _obj, _inh, ace_sid = parts
    if ace_type != "A" or "ID" in ace_flags or rights != "FA" or ace_sid != sid:
        return f"ACE is not a non-inherited ALLOW FA for the current user: {aces[0]!r}"
    return None


def _current_user_sid() -> str:  # pragma: no cover - Windows only
    """The current process token's user SID as a string (``S-1-5-21-...``)."""

    import ctypes
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    TOKEN_QUERY = 0x0008
    TokenUser = 1

    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    advapi32.OpenProcessToken.argtypes = [
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.HANDLE),
    ]
    advapi32.OpenProcessToken.restype = wintypes.BOOL
    advapi32.GetTokenInformation.argtypes = [
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD),
    ]
    advapi32.GetTokenInformation.restype = wintypes.BOOL
    advapi32.ConvertSidToStringSidW.argtypes = [
        ctypes.c_void_p,
        ctypes.POINTER(wintypes.LPWSTR),
    ]
    advapi32.ConvertSidToStringSidW.restype = wintypes.BOOL
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    token = wintypes.HANDLE()
    if not advapi32.OpenProcessToken(
        kernel32.GetCurrentProcess(), TOKEN_QUERY, ctypes.byref(token)
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        needed = wintypes.DWORD(0)
        advapi32.GetTokenInformation(token, TokenUser, None, 0, ctypes.byref(needed))
        buf = ctypes.create_string_buffer(needed.value)
        if not advapi32.GetTokenInformation(
            token, TokenUser, buf, needed, ctypes.byref(needed)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        # TOKEN_USER starts with SID_AND_ATTRIBUTES, whose first member is the PSID.
        psid = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]
        sid_str = wintypes.LPWSTR()
        if not advapi32.ConvertSidToStringSidW(psid, ctypes.byref(sid_str)):
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            return sid_str.value
        finally:
            kernel32.LocalFree(sid_str)
    finally:
        kernel32.CloseHandle(token)


def _create_private_file_windows(target: str, data: bytes) -> None:  # pragma: no cover
    import ctypes
    import msvcrt
    from ctypes import wintypes

    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    GENERIC_WRITE = 0x40000000
    CREATE_NEW = 1
    FILE_ATTRIBUTE_NORMAL = 0x80
    SDDL_REVISION_1 = 1
    INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
    ERROR_FILE_EXISTS = 80
    ERROR_ALREADY_EXISTS = 183

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
            ("nLength", wintypes.DWORD),
            ("lpSecurityDescriptor", ctypes.c_void_p),
            ("bInheritHandle", wintypes.BOOL),
        ]

    advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        ctypes.POINTER(ctypes.c_void_p),
        ctypes.POINTER(wintypes.ULONG),
    ]
    advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW.restype = (
        wintypes.BOOL
    )
    kernel32.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.POINTER(SECURITY_ATTRIBUTES),
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    kernel32.CreateFileW.restype = wintypes.HANDLE
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    psd = ctypes.c_void_p()
    if not advapi32.ConvertStringSecurityDescriptorToSecurityDescriptorW(
        owner_only_sddl(), SDDL_REVISION_1, ctypes.byref(psd), None
    ):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        sa = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), psd, False)
        handle = kernel32.CreateFileW(
            target,
            GENERIC_WRITE,
            0,
            ctypes.byref(sa),
            CREATE_NEW,
            FILE_ATTRIBUTE_NORMAL,
            None,
        )
        if handle == INVALID_HANDLE_VALUE or handle is None:
            err = ctypes.get_last_error()
            if err in (ERROR_FILE_EXISTS, ERROR_ALREADY_EXISTS):
                raise FileExistsError(17, "File exists", target)
            raise ctypes.WinError(err)
    finally:
        kernel32.LocalFree(psd)
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_WRONLY | getattr(os, "O_BINARY", 0))
    except BaseException:
        kernel32.CloseHandle(handle)
        raise
    try:
        os.write(fd, data)
    finally:
        os.close(fd)  # also closes the Win32 handle
