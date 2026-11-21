import sys
import os
import struct
import base64
import binascii
import xml.etree.ElementTree as ET
import msoffcrypto
import io

sys.stdout.reconfigure(line_buffering=True)

OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
ENDOFCHAIN = 0xFFFFFFFE
FREESECT = 0xFFFFFFFF


class OleReader:
    def __init__(self, data: bytes):
        if len(data) < 512 or data[:8] != OLE_MAGIC:
            raise ValueError("Not a valid OLE compound file.")
        self.data = data
        self.sector_size = 1 << struct.unpack_from("<H", data, 30)[0]
        self.mini_sector_size = 1 << struct.unpack_from("<H", data, 32)[0]
        self.mini_cutoff = struct.unpack_from("<I", data, 56)[0]
        self.first_dir_sect = struct.unpack_from("<I", data, 48)[0]
        self.first_mini_fat_sect = struct.unpack_from("<I", data, 60)[0]
        self.num_fat_sects = struct.unpack_from("<I", data, 44)[0]

        difat = list(struct.unpack_from("<109I", data, 76))
        first_difat_sect = struct.unpack_from("<I", data, 68)[0]
        num_difat_sects = struct.unpack_from("<I", data, 72)[0]

        cur_difat = first_difat_sect
        for _ in range(num_difat_sects):
            if cur_difat >= ENDOFCHAIN:
                break
            sec = self._read_sector(cur_difat)
            entries_per_sec = (self.sector_size // 4) - 1
            words = struct.unpack_from(f"<{self.sector_size // 4}I", sec, 0)
            difat.extend(words[:entries_per_sec])
            cur_difat = words[-1]

        self.fat = []
        for s in difat:
            if s < FREESECT and len(self.fat) * 4 < self.num_fat_sects * self.sector_size:
                sec = self._read_sector(s)
                self.fat.extend(struct.unpack_from(f"<{self.sector_size // 4}I", sec, 0))

        self.mini_fat = []
        cur_m = self.first_mini_fat_sect
        while cur_m < ENDOFCHAIN:
            sec = self._read_sector(cur_m)
            self.mini_fat.extend(struct.unpack_from(f"<{self.sector_size // 4}I", sec, 0))
            cur_m = self.fat[cur_m] if cur_m < len(self.fat) else ENDOFCHAIN

        dir_bytes = self._read_chain(self.fat, self.first_dir_sect)
        self.entries = []
        for offset in range(0, len(dir_bytes), 128):
            entry = dir_bytes[offset:offset + 128]
            if len(entry) < 128:
                break
            name_len = struct.unpack_from("<H", entry, 64)[0]
            obj_type = entry[66]
            start_sec = struct.unpack_from("<I", entry, 116)[0]
            size = struct.unpack_from("<Q", entry, 120)[0]
            name = entry[:max(0, name_len - 2)].decode("utf-16-le", errors="ignore")
            self.entries.append((name, obj_type, start_sec, size))

        self.mini_stream = b""
        if self.entries:
            _, _, root_start, root_size = self.entries[0]
            if root_start < ENDOFCHAIN and root_size > 0:
                self.mini_stream = self._read_chain(self.fat, root_start)[:root_size]

    def _read_sector(self, sect_id: int) -> bytes:
        pos = 512 + sect_id * self.sector_size
        return self.data[pos:pos + self.sector_size]

    def _read_chain(self, table, start_sect: int) -> bytes:
        chunks = []
        cur = start_sect
        seen = set()
        while cur < ENDOFCHAIN and cur not in seen:
            seen.add(cur)
            if table is self.fat:
                if cur >= len(self.fat):
                    break
                chunks.append(self._read_sector(cur))
                cur = self.fat[cur]
            else:
                if cur >= len(self.mini_fat):
                    break
                m_pos = cur * self.mini_sector_size
                chunks.append(self.mini_stream[m_pos:m_pos + self.mini_sector_size])
                cur = self.mini_fat[cur]
        return b"".join(chunks)

    def get_stream(self, target_name: str):
        target_lower = target_name.lower()
        for name, obj_type, start_sec, size in self.entries:
            if obj_type == 2 and name.lower() == target_lower:
                if size < self.mini_cutoff:
                    return self._read_chain(self.mini_fat, start_sec)[:size]
                return self._read_chain(self.fat, start_sec)[:size]
        return None


def _local_name(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _attr_ci(attrib: dict, *candidates: str, default: str = "") -> str:
    lower_map = {k.lower(): v for k, v in attrib.items()}
    for cand in candidates:
        val = lower_map.get(cand.lower())
        if val is not None and str(val).strip() != "":
            return str(val).strip()
    return default


def extract_office_hash(file_path: str):
    with open(file_path, "rb") as f:
        raw = f.read()

    # Quick check via msoffcrypto so non-encrypted files are reported clearly
    try:
        probe = msoffcrypto.OfficeFile(io.BytesIO(raw))
        if not probe.is_encrypted():
            raise ValueError("Document is not password-encrypted.")
    except ValueError:
        raise
    except Exception:
        pass

    ole = OleReader(raw)
    enc_info = ole.get_stream("EncryptionInfo")
    if not enc_info or len(enc_info) < 8:
        raise ValueError("Missing EncryptionInfo stream; unsupported or unencrypted format.")

    major, minor, _ = struct.unpack_from("<HHI", enc_info, 0)
    payload = enc_info[8:]

    # Standard (ECMA-376) encryption -> hashcat mode 9400
    if major in (2, 3, 4) and minor == 2 and len(payload) >= 12:
        _, header_size = struct.unpack_from("<II", payload, 0)
        hdr_bytes = payload[8:8 + header_size]
        if len(hdr_bytes) >= 32:
            _, _, _, _, _, size_extra = struct.unpack_from("<6I", hdr_bytes, 0)
            salt_offset = 24 + size_extra
            salt_size = 16
            salt = hdr_bytes[salt_offset:salt_offset + salt_size]
            verifier_start = 8 + header_size
            verifier_bytes = payload[verifier_start:]
            if len(verifier_bytes) >= 44 and len(salt) == 16:
                enc_verifier = verifier_bytes[4:20]
                enc_verifier_hash = verifier_bytes[20:20 + 32]
                h_str = (
                    f"$office$*2007*{size_extra}*128*16*"
                    f"{binascii.hexlify(salt).decode()}*"
                    f"{binascii.hexlify(enc_verifier).decode()}*"
                    f"{binascii.hexlify(enc_verifier_hash).decode()}"
                )
                return 9400, h_str

    # Agile encryption (major == 4, minor == 4) -> XML EncryptionInfo (modes 9500 / 9600)
    xml_start = payload.find(b"<")
    if xml_start != -1:
        xml_text = payload[xml_start:].decode("utf-8", errors="ignore")
        end_idx = xml_text.rfind(">")
        if end_idx != -1:
            xml_text = xml_text[:end_idx + 1]
        root = ET.fromstring(xml_text)

        key_data_salt = ""
        pass_salt = ""
        spin_count = "100000"
        block_size = "16"
        key_bits = "256"
        hash_alg = "SHA512"
        enc_verifier_b64 = ""
        enc_verifier_hash_b64 = ""
        enc_key_b64 = ""

        for elem in root.iter():
            tag = _local_name(elem.tag).lower()
            if tag == "keydata":
                key_data_salt = _attr_ci(elem.attrib, "saltValue", default=key_data_salt)
                block_size = _attr_ci(elem.attrib, "blockSize", default=block_size)
            elif tag == "passwordkey":
                pass_salt = _attr_ci(elem.attrib, "saltValue", default=pass_salt)
                spin_count = _attr_ci(elem.attrib, "spinCount", default=spin_count)
                block_size = _attr_ci(elem.attrib, "blockSize", default=block_size)
                key_bits = _attr_ci(elem.attrib, "keyBits", default=key_bits)
                hash_alg = _attr_ci(elem.attrib, "hashAlgorithm", default=hash_alg).upper()
            elif tag == "encryptedkey":
                pass_salt = _attr_ci(elem.attrib, "saltValue", default=pass_salt)
                spin_count = _attr_ci(elem.attrib, "spinCount", default=spin_count)
                block_size = _attr_ci(elem.attrib, "blockSize", default=block_size)
                key_bits = _attr_ci(elem.attrib, "keyBits", default=key_bits)
                hash_alg = _attr_ci(elem.attrib, "hashAlgorithm", default=hash_alg).upper()
                enc_verifier_b64 = _attr_ci(
                    elem.attrib,
                    "encryptedVerifierHashInput",
                    "encryptedVerifier",
                    default=enc_verifier_b64
                )
                enc_verifier_hash_b64 = _attr_ci(
                    elem.attrib,
                    "encryptedVerifierHashValue",
                    default=enc_verifier_hash_b64
                )
                enc_key_b64 = _attr_ci(
                    elem.attrib,
                    "encryptedKeyValue",
                    default=enc_key_b64
                )

        if pass_salt and enc_verifier_b64 and enc_verifier_hash_b64 and enc_key_b64:
            salt_hex = binascii.hexlify(base64.b64decode(pass_salt)).decode()
            ev_hex = binascii.hexlify(base64.b64decode(enc_verifier_b64)).decode()
            evh_hex = binascii.hexlify(base64.b64decode(enc_verifier_hash_b64)).decode()
            ek_hex = binascii.hexlify(base64.b64decode(enc_key_b64)).decode()
            kd_salt_hex = binascii.hexlify(base64.b64decode(key_data_salt)).decode() if key_data_salt else salt_hex

            mode = 9600 if "SHA512" in hash_alg else 9500
            version_tag = "2013" if mode == 9600 else "2010"
            h_str = (
                f"$office$*{version_tag}*{spin_count}*{key_bits}*{block_size}*"
                f"{salt_hex}*{ev_hex}*{evh_hex}*{ek_hex}*{kd_salt_hex}"
            )
            return mode, h_str

        raise ValueError(
            f"Agile XML parsed (major={major}, minor={minor}) but missing expected key attributes "
            f"(salt={bool(pass_salt)}, verifier_in={bool(enc_verifier_b64)}, "
            f"verifier_hash={bool(enc_verifier_hash_b64)}, enc_key={bool(enc_key_b64)})."
        )

    raise ValueError(f"Unsupported Office encryption header format (major={major}, minor={minor}).")


def main():
    if len(sys.argv) < 2:
        print("[-] Usage: hash_extractor.py <locked_file> [output_hash_file]", file=sys.stderr)
        sys.exit(1)

    locked_file = sys.argv[1]
    out_hash_file = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] else ""

    if not os.path.exists(locked_file):
        print(f"[-] File not found: {locked_file}", file=sys.stderr)
        sys.exit(1)

    try:
        mode, hash_str = extract_office_hash(locked_file)
        if out_hash_file:
            os.makedirs(os.path.dirname(os.path.abspath(out_hash_file)), exist_ok=True)
            with open(out_hash_file, "w", encoding="utf-8") as f:
                f.write(hash_str + "\n")
        print(f"MODE={mode}")
        print(f"HASH={hash_str}")
        sys.exit(0)
    except Exception as exc:
        print(f"[-] Hash extraction failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()