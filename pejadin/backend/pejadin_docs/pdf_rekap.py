import io

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from xml.sax.saxutils import escape


def buat_pdf_rekap(
    *,
    organization: str,
    address: str,
    period: str,
    status_label: str,
    report_date: str,
    status_counts: list[tuple[str, int]],
    total_reports: int,
    total_staff: int,
    total_cost: str,
    flagged_count: int,
    columns: list[str],
    rows: list[list[object]],
) -> bytes:
    output = io.BytesIO()
    page_width, _ = landscape(A3)
    document = SimpleDocTemplate(
        output,
        pagesize=landscape(A3),
        rightMargin=12 * mm,
        leftMargin=12 * mm,
        topMargin=15 * mm,
        bottomMargin=16 * mm,
        title="Laporan Rekapitulasi Surat Tugas",
        author="PEJADIN",
    )

    base = getSampleStyleSheet()
    organization_style = ParagraphStyle(
        "Organization",
        parent=base["Normal"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#20386f"),
    )
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=base["Title"],
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#20386f"),
        spaceBefore=5,
        spaceAfter=3,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=base["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#52627d"),
    )
    label_style = ParagraphStyle(
        "SummaryLabel",
        parent=base["Normal"],
        fontSize=7,
        leading=9,
        textColor=colors.HexColor("#52627d"),
    )
    value_style = ParagraphStyle(
        "SummaryValue",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#243047"),
    )
    header_style = ParagraphStyle(
        "TableHeader",
        parent=base["Normal"],
        fontName="Helvetica-Bold",
        fontSize=6.5,
        leading=8,
        textColor=colors.white,
        alignment=TA_LEFT,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=base["Normal"],
        fontSize=6.5,
        leading=8,
        textColor=colors.HexColor("#243047"),
        splitLongWords=True,
    )
    center_style = ParagraphStyle(
        "TableCellCenter",
        parent=cell_style,
        alignment=TA_CENTER,
    )

    story = [
        Paragraph(escape(organization), organization_style),
        Paragraph(escape(address), subtitle_style),
        Paragraph("LAPORAN REKAPITULASI SURAT TUGAS", title_style),
        Paragraph(
            "Monitoring pelaksanaan perjalanan dinas dan realisasi biaya",
            subtitle_style,
        ),
        Spacer(1, 5 * mm),
    ]

    summary = [
        ("Periode laporan", period),
        ("Status", status_label),
        ("Jumlah Surat Tugas", str(total_reports)),
        ("Jumlah pelaksana", str(total_staff)),
        ("Akumulasi biaya", total_cost),
        ("Perlu pemeriksaan biaya", str(flagged_count)),
        ("Tanggal dan waktu cetak", report_date),
    ]
    summary_cells = []
    for index in range(0, len(summary), 2):
        first = summary[index]
        second = summary[index + 1] if index + 1 < len(summary) else ("", "")
        summary_cells.append([
            Paragraph(escape(first[0]), label_style),
            Paragraph(escape(first[1]), value_style),
            Paragraph(escape(second[0]), label_style),
            Paragraph(escape(second[1]), value_style),
        ])
    summary_table = Table(
        summary_cells,
        colWidths=[37 * mm, 54 * mm, 37 * mm, 54 * mm],
        hAlign="LEFT",
    )
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f7fb")),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#ccd5e4")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d7deea")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([summary_table, Spacer(1, 4 * mm)])

    status_data = [[
        Paragraph("Rekapitulasi status", value_style),
        *[
            Paragraph(
                f"<b>{escape(label)}</b>: {count}",
                label_style,
            )
            for label, count in status_counts
        ],
    ]]
    status_table = Table(status_data, hAlign="LEFT")
    status_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#d9e1ed")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([
        status_table,
        Spacer(1, 5 * mm),
        Paragraph("RINCIAN SURAT TUGAS", value_style),
        Spacer(1, 2 * mm),
    ])

    table_width = page_width - document.leftMargin - document.rightMargin
    column_widths = [
        20, 58, 72, 76, 67, 67, 70, 24, 48, 112, 46, 48, 72, 52, 54, 66, 108,
    ]
    scale = table_width / sum(column_widths)
    widths = [width * scale for width in column_widths]
    table_data = [[Paragraph(escape(label), header_style) for label in columns]]
    for row in rows:
        table_data.append([
            Paragraph(escape(str(value)), center_style if index in (0, 7, 10) else cell_style)
            for index, value in enumerate(row)
        ])
    if not rows:
        table_data.append([
            Paragraph(
                "Tidak ada data Surat Tugas untuk kriteria laporan ini.",
                cell_style,
            ),
            *[Paragraph("", cell_style) for _ in columns[1:]],
        ])

    detail_table = Table(
        table_data,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
        splitByRow=1,
    )
    detail_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20386f")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
            colors.white,
            colors.HexColor("#f7f9fc"),
        ]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7deea")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if not rows:
        detail_styles.append(("SPAN", (0, 1), (-1, 1)))
    detail_table.setStyle(TableStyle(detail_styles))
    story.append(detail_table)

    def draw_page(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#d7deea"))
        canvas.line(doc.leftMargin, 10 * mm, page_width - doc.rightMargin, 10 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(
            doc.leftMargin,
            6.5 * mm,
            f"PEJADIN - Laporan {period} - Dicetak {report_date}",
        )
        canvas.drawRightString(
            page_width - doc.rightMargin,
            6.5 * mm,
            f"Halaman {doc.page}",
        )
        canvas.restoreState()

    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    return output.getvalue()
