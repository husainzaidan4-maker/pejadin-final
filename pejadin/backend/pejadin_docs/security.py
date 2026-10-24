_PLACEHOLDER_SECRETS = {
    "ganti-rahasia-ini",
    "ganti-dengan-teks-acak-panjang",
}


def validate_token_secret(secret: str | None) -> str:
    value = (secret or "").strip()
    if len(value) < 32 or value.lower() in _PLACEHOLDER_SECRETS:
        raise RuntimeError(
            "SECRET harus diisi dengan nilai acak minimal 32 karakter."
        )
    return value


def filter_spd_for_user(spd_rows: list[dict], user: dict) -> list[dict]:
    if user["role"] != "PEGAWAI":
        return spd_rows
    pegawai_id = user.get("pegawai_id")
    if pegawai_id is None:
        return []
    return [row for row in spd_rows if row["pegawai_id"] == pegawai_id]
