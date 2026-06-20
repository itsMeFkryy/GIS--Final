/**
 * pdf-export.js — Generate PDF Laporan Stunting
 * Uses jsPDF + jspdf-autotable (loaded via CDN in index.html)
 */
const PDFExport = (() => {

    function formatDate() {
        return new Date().toLocaleDateString('id-ID', {
            day: '2-digit', month: 'long', year: 'numeric'
        });
    }

    function exportPDF() {
        if (typeof window.jspdf === 'undefined' && typeof jsPDF === 'undefined') {
            alert('Library PDF belum dimuat. Coba beberapa saat lagi.');
            return;
        }

        const { jsPDF } = window.jspdf || window;
        const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

        const W = doc.internal.pageSize.getWidth();
        const accentR = 37, accentG = 130, accentB = 246;

        // ── HEADER BAND ──────────────────────────────────────
        doc.setFillColor(accentR, accentG, accentB);
        doc.rect(0, 0, W, 38, 'F');

        doc.setTextColor(255, 255, 255);
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.text('PEMERINTAH KABUPATEN PRINGSEWU', W / 2, 10, { align: 'center' });

        doc.setFontSize(16);
        doc.setFont('helvetica', 'bold');
        doc.text('LAPORAN DATA STUNTING', W / 2, 19, { align: 'center' });

        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text('Pekon Kresnomulyo Barat, Kec. Ambarawa, Kab. Pringsewu, Lampung', W / 2, 27, { align: 'center' });

        doc.setFontSize(8);
        doc.text(`Dicetak: ${formatDate()}`, W / 2, 34, { align: 'center' });

        // ── SUMMARY CARDS ─────────────────────────────────────
        let Y = 46;
        doc.setTextColor(30, 41, 59);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text('RINGKASAN DATA', 14, Y);
        Y += 6;

        const features = window.wilayahData?.features || [];
        const totBal  = features.reduce((s,f) => s + (f.properties.jml_balita||0), 0);
        const totStunt = features.reduce((s,f) => s + (f.properties.jml_stunt||0),  0);
        const prevTot = totBal > 0 ? ((totStunt/totBal)*100).toFixed(1) : '0';
        const totWil  = features.length;

        const cards = [
            { label: 'Total Balita',  value: totBal.toString() },
            { label: 'Total Stunting', value: totStunt.toString() },
            { label: 'Prevalensi',    value: prevTot + '%' },
            { label: 'Jumlah Wilayah', value: totWil.toString() },
        ];

        const cw = (W - 28) / 4;
        cards.forEach((c, i) => {
            const x = 14 + i * (cw + 2);
            doc.setFillColor(239, 246, 255);
            doc.roundedRect(x, Y, cw, 20, 2, 2, 'F');
            doc.setDrawColor(accentR, accentG, accentB);
            doc.setLineWidth(0.8);
            doc.line(x, Y, x, Y + 20);

            doc.setTextColor(accentR, accentG, accentB);
            doc.setFontSize(14);
            doc.setFont('helvetica', 'bold');
            doc.text(c.value, x + cw/2, Y + 11, { align: 'center' });

            doc.setTextColor(100, 116, 139);
            doc.setFontSize(7);
            doc.setFont('helvetica', 'normal');
            doc.text(c.label, x + cw/2, Y + 17, { align: 'center' });
        });
        Y += 28;

        // ── DATA TABLE ────────────────────────────────────────
        doc.setTextColor(30, 41, 59);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text('DATA PER WILAYAH', 14, Y);
        Y += 4;

        const rows = features.map(f => {
            const p = f.properties;
            return [
                p.nama_wil || '-',
                p.jml_balita?.toString() || '0',
                p.jml_stunt?.toString()  || '0',
                (p.prev_stunt?.toString() || '0') + '%',
                p.kat_stunt   || '-',
                (p.air_bersih?.toString() || '0') + '%',
                (p.sanitasi?.toString()   || '0') + '%',
                p.kat_rentan  || '-',
            ];
        });

        doc.autoTable({
            startY: Y,
            head: [['Wilayah','Balita','Stunting','Prevalensi','Kategori','Air Bersih','Sanitasi','Kerentanan']],
            body: rows,
            theme: 'striped',
            headStyles: {
                fillColor: [accentR, accentG, accentB],
                textColor: 255,
                fontSize: 8,
                fontStyle: 'bold',
            },
            bodyStyles: { fontSize: 8, textColor: [30, 41, 59] },
            alternateRowStyles: { fillColor: [248, 250, 252] },
            columnStyles: {
                0: { cellWidth: 32 },
                4: { cellWidth: 22 },
                7: { cellWidth: 22 },
            },
            margin: { left: 14, right: 14 },
            didParseCell(data) {
                if (data.section === 'body' && data.column.index === 4) {
                    const v = data.cell.raw;
                    if (v === 'Sangat Tinggi') data.cell.styles.textColor = [189, 0, 38];
                    else if (v === 'Tinggi')   data.cell.styles.textColor = [234, 88, 12];
                    else if (v === 'Sedang')   data.cell.styles.textColor = [180, 100, 0];
                    else                        data.cell.styles.textColor = [21, 128, 61];
                }
            }
        });

        // ── FOOTER ────────────────────────────────────────────
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
            doc.setPage(i);
            const ph = doc.internal.pageSize.getHeight();
            doc.setFillColor(248, 250, 252);
            doc.rect(0, ph - 12, W, 12, 'F');
            doc.setDrawColor(226, 232, 240);
            doc.setLineWidth(0.3);
            doc.line(0, ph - 12, W, ph - 12);
            doc.setFontSize(7);
            doc.setTextColor(148, 163, 184);
            doc.setFont('helvetica', 'normal');
            doc.text('WebGIS Stunting — Pekon Kresnomulyo Barat, Kab. Pringsewu', 14, ph - 4);
            doc.text(`Halaman ${i} / ${pageCount}`, W - 14, ph - 4, { align: 'right' });
        }

        doc.save(`laporan_stunting_kresnomulyo_${new Date().toISOString().slice(0,10)}.pdf`);
    }

    return { exportPDF };
})();
