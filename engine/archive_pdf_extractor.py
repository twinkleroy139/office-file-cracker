import os
import re
import struct
import zipfile
import subprocess
import shutil


def detect_archive_or_pdf_type(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if ext in ("zip", "pdf", "7z"):
        return ext

    try:
        with open(file_path, "rb") as f:
            header = f.read(16)
        if header.startswith(b"PK\x03\x04") or header.startswith(b"PK\x05\x06"):
            return "zip"
        if header.startswith(b"%PDF-"):
            return "pdf"
        if header.startswith(b"7z\xbc\xaf\x27\x1c"):
            return "7z"
    except Exception:
        pass

    return ext or "unknown"


def _extract_zip_hashcat_hash(file_path: str):
    """Builds a $zip2$* hash string for PKZIP/WinZip AES/traditional entries when possible."""
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            infos = [i for i in zf.infolist() if not i.is_dir()]
            if not infos:
                raise ValueError("ZIP archive contains no files.")
            encrypted_infos = [i for i in infos if (i.flag_bits & 0x1) != 0]
            if not encrypted_infos:
                raise ValueError("ZIP archive is not password-encrypted.")

            info = encrypted_infos[0]
            with open(file_path, "rb") as raw_f:
                raw_bytes = raw_f.read()

            # Locate local file header for info.filename
            fname_bytes = info.filename.encode("utf-8", errors="ignore")
            magic = b"PK\x03\x04"
            pos = raw_bytes.find(magic)
            target_offset = -1
            while pos != -1:
                if pos + 30 <= len(raw_bytes):
                    fn_len, extra_len = struct.unpack_from("<HH", raw_bytes, pos + 26)
                    fn_start = pos + 30
                    fn_end = fn_start + fn_len
                    if raw_bytes[fn_start:fn_end] == fname_bytes:
                        target_offset = pos
                        break
                pos = raw_bytes.find(magic, pos + 1)

            if target_offset == -1:
                return None, "ZIP encrypted entry detected (using direct Python verifier)"

            _, _, _, comp_method, _, _, crc32_val, comp_size, uncomp_size, fn_len, extra_len = struct.unpack_from(
                "<HHHHHIIIHHH", raw_bytes, target_offset + 4
            )
            data_start = target_offset + 30 + fn_len + extra_len
            enc_data = raw_bytes[data_start : data_start + comp_size]
            if not enc_data:
                return None, "ZIP encrypted payload empty"

            # Hashcat -m 17200 / 17220 / 17225 / 17230 format helper
            magic_type = 0 if comp_method != 99 else 3
            magic_str = f"000{magic_type}"
            # Standard $zip2$* structure: $zip2$*MAGIC*MODE*...
            # Keep format clean and only return when structure is well-formed
            if magic_type == 0 and len(enc_data) >= 12:
                header_12 = enc_data[:12].hex()
                tail_len = min(len(enc_data), 32)
                tail_hex = enc_data[-tail_len:].hex()
                hc_str = (
                    f"$zip2$*{magic_str}*0*{len(enc_data)}*{header_12}*"
                    f"{crc32_val:08x}*{comp_method}*{uncomp_size}*{tail_hex}*$/zip2$"
                )
                return 17200, hc_str

            return None, "ZIP encryption variant routed to Python/CLI verifier"
    except ValueError:
        raise
    except Exception as e:
        return None, f"ZIP inspection note: {e}"


def _extract_pdf_hashcat_hash(file_path: str):
    """Checks PDF encryption dictionary and extracts standard PDF hash lines if available."""
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        if b"/Encrypt" not in content:
            raise ValueError("PDF document does not contain a /Encrypt dictionary.")

        # Try pdf2john if installed in PATH
        for tool in ("pdf2john.pl", "pdf2john", "pdf2john.py"):
            tool_path = shutil.which(tool)
            if tool_path:
                proc = subprocess.run([tool_path, file_path], capture_output=True, text=True, timeout=15)
                for line in (proc.stdout or "").splitlines():
                    if "$pdf$" in line:
                        hash_part = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                        return 10500, hash_part

        return None, "PDF /Encrypt detected (using Python/CLI verifier)"
    except ValueError:
        raise
    except Exception as e:
        return None, f"PDF inspection note: {e}"


def _extract_7z_hashcat_hash(file_path: str):
    """Checks 7z signature and tries 7z2hashcat if installed."""
    try:
        with open(file_path, "rb") as f:
            sig = f.read(6)
        if sig != b"7z\xbc\xaf\x27\x1c":
            raise ValueError("Invalid 7z archive header.")

        for tool in ("7z2hashcat.pl", "7z2hashcat", "7z2hashcat.py"):
            tool_path = shutil.which(tool)
            if tool_path:
                proc = subprocess.run([tool_path, file_path], capture_output=True, text=True, timeout=15)
                for line in (proc.stdout or "").splitlines():
                    if "$7z$" in line:
                        hash_part = line.split(":", 1)[1].strip() if ":" in line else line.strip()
                        return 11600, hash_part

        return None, "7z archive header verified (using 7z/Python verifier)"
    except ValueError:
        raise
    except Exception as e:
        return None, f"7z inspection note: {e}"


def extract_multi_format_target(file_path: str):
    """
    Returns dict:
      {
        "format": "zip" | "pdf" | "7z",
        "hashcat_mode": int | None,
        "hash_line": str | None,
        "info": str
      }
    """
    fmt = detect_archive_or_pdf_type(file_path)
    if fmt == "zip":
        mode, hline = _extract_zip_hashcat_hash(file_path)
        return {
            "format": "zip",
            "hashcat_mode": mode,
            "hash_line": hline if mode is not None else None,
            "info": hline if mode is None else f"Hashcat mode {mode} target prepared",
        }
    if fmt == "pdf":
        mode, hline = _extract_pdf_hashcat_hash(file_path)
        return {
            "format": "pdf",
            "hashcat_mode": mode,
            "hash_line": hline if mode is not None else None,
            "info": hline if mode is None else f"Hashcat mode {mode} target prepared",
        }
    if fmt == "7z":
        mode, hline = _extract_7z_hashcat_hash(file_path)
        return {
            "format": "7z",
            "hashcat_mode": mode,
            "hash_line": hline if mode is not None else None,
            "info": hline if mode is None else f"Hashcat mode {mode} target prepared",
        }
    raise ValueError(f"Unsupported format '{fmt}' for multi-format engine (expected zip, pdf, or 7z).")


def verify_password_for_format(file_path: str, fmt: str, password: str, extract_dir: str | None = None) -> bool:
    """Verifies a candidate password against ZIP, PDF, or 7z."""
    if fmt == "zip":
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                infos = [i for i in zf.infolist() if not i.is_dir()]
                if not infos:
                    return False
                target_info = next((i for i in infos if (i.flag_bits & 0x1) != 0), infos[0])
                pwd_bytes = password.encode("utf-8", errors="ignore")
                with zf.open(target_info, pwd=pwd_bytes) as entry:
                    entry.read(64)
                if extract_dir:
                    os.makedirs(extract_dir, exist_ok=True)
                    zf.extractall(path=extract_dir, pwd=pwd_bytes)
                return True
        except Exception:
            return False

    if fmt == "pdf":
        # Try pypdf / PyPDF2 first if available
        try:
            import pypdf  # type: ignore
            reader = pypdf.PdfReader(file_path)
            if not reader.is_encrypted:
                return False
            res = reader.decrypt(password)
            return bool(res)
        except Exception:
            pass

        try:
            import PyPDF2  # type: ignore
            reader = PyPDF2.PdfReader(file_path)
            if not reader.is_encrypted:
                return False
            res = reader.decrypt(password)
            return bool(res)
        except Exception:
            pass

        # Fallback to qpdf if installed
        qpdf_bin = shutil.which("qpdf")
        if qpdf_bin:
            out_probe = os.path.join(extract_dir or "/tmp", "pdf_probe_unlocked.pdf")
            if extract_dir:
                os.makedirs(extract_dir, exist_ok=True)
            proc = subprocess.run(
                [qpdf_bin, f"--password={password}", "--decrypt", file_path, out_probe],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return proc.returncode == 0
        return False

    if fmt == "7z":
        # Try py7zr if installed
        try:
            import py7zr  # type: ignore
            with py7zr.SevenZipFile(file_path, mode="r", password=password) as sz:
                if extract_dir:
                    os.makedirs(extract_dir, exist_ok=True)
                    sz.extractall(path=extract_dir)
                else:
                    _ = sz.getnames()
            return True
        except Exception:
            pass

        # Fallback to 7z / 7zz CLI if installed
        seven_bin = shutil.which("7z") or shutil.which("7zz")
        if seven_bin:
            out_dir = extract_dir or os.path.join("/tmp", f"sz_probe_{os.getpid()}")
            os.makedirs(out_dir, exist_ok=True)
            proc = subprocess.run(
                [seven_bin, "t", f"-p{password}", file_path],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if proc.returncode == 0 and extract_dir:
                subprocess.run(
                    [seven_bin, "x", "-y", f"-p{password}", f"-o{extract_dir}", file_path],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
            return proc.returncode == 0
        return False

    return False