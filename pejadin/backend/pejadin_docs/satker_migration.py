import datetime as dt

SATKER_TRANSITION_YEAR = 2026
SATKER_PROFILE_FIELDS = (
    "nama_kementerian",
    "nama_ditjen",
    "nama_satker",
    "nama_satker_panjang",
    "alamat",
    "kode_satker",
    "nomor_dipa",
    "tanggal_dipa",
    "dipa_raw",
    "klasifikasi_anggaran",
    "kode_akun_belanja",
    "rekening_bendahara",
    "nomor_sptjb",
    "akun_default",
    "kota",
    "kota_kedudukan",
)
SATKER_PROFILE_COLUMN_TYPES = {
    "nama_kementerian": "varchar(150)",
    "nama_ditjen": "varchar(150)",
    "nama_satker": "varchar(200)",
    "nama_satker_panjang": "varchar(250)",
    "alamat": "text",
    "kode_satker": "varchar(10)",
    "nomor_dipa": "varchar(100)",
    "tanggal_dipa": "date",
    "dipa_raw": "text",
    "klasifikasi_anggaran": "varchar(100)",
    "kode_akun_belanja": "varchar(10)",
    "rekening_bendahara": "varchar(100)",
    "nomor_sptjb": "varchar(100)",
    "akun_default": "varchar(50)",
    "kota": "varchar(50)",
    "kota_kedudukan": "varchar(50)",
}


def migrate_legacy_satker(connection):
    fields_sql = ", ".join(
        f"{field} {SATKER_PROFILE_COLUMN_TYPES[field]}"
        for field in SATKER_PROFILE_FIELDS
    )
    connection.execute(
        "create table if not exists satker_tahunan("
        "tahun_anggaran int primary key,"
        f"{fields_sql},"
        "created_at timestamptz not null default now(),"
        "updated_at timestamptz not null default now())"
    )
    for field in SATKER_PROFILE_FIELDS:
        connection.execute(
            "alter table satker_tahunan add column if not exists "
            f"{field} {SATKER_PROFILE_COLUMN_TYPES[field]}"
        )
    field_list = ", ".join(SATKER_PROFILE_FIELDS)
    projections = ", ".join(
        (
            f"nullif(max(v) filter (where k = '{field}'), '')::date"
            if field == "tanggal_dipa"
            else f"max(v) filter (where k = '{field}')"
        )
        for field in SATKER_PROFILE_FIELDS
    )
    connection.execute(
        "insert into satker_tahunan(tahun_anggaran,"
        f"{field_list}) select %s,{projections} from satker "
        "having count(*) > 0 on conflict(tahun_anggaran) do nothing",
        (SATKER_TRANSITION_YEAR,),
    )


def sync_legacy_satker(connection, values):
    fields = [field for field in SATKER_PROFILE_FIELDS if field in values]
    if not fields:
        return
    columns = ["tahun_anggaran", *fields]
    placeholders = ",".join("%s" for _ in columns)
    updates = ",".join(f"{field}=excluded.{field}" for field in fields)
    profile_values = []
    for field in fields:
        value = values[field]
        if field == "tanggal_dipa":
            if value in (None, ""):
                value = None
            elif not isinstance(value, dt.date):
                value = dt.date.fromisoformat(str(value))
        elif value is not None:
            value = str(value)
        profile_values.append(value)
    connection.execute(
        "insert into satker_tahunan("
        f"{','.join(columns)}) values({placeholders}) "
        f"on conflict(tahun_anggaran) do update set {updates}",
        (SATKER_TRANSITION_YEAR, *profile_values),
    )


def ensure_spd_pegawai_foreign_key(connection):
    orphaned = connection.execute(
        "select count(*) as total from spd p "
        "left join pegawai g on g.id=p.pegawai_id "
        "where p.pegawai_id is not null and g.id is null"
    ).fetchone()
    connection.execute(
        "do $$ begin "
        "if not exists (select 1 from pg_constraint "
        "where conrelid='spd'::regclass and conname='fk_spd_pegawai') then "
        "alter table spd add constraint fk_spd_pegawai "
        "foreign key (pegawai_id) references pegawai(id) not valid; "
        "end if; end $$"
    )
    return orphaned["total"] if orphaned else 0
