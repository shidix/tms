from fpdf import FPDF

class MonthlyReportPDF(FPDF):
    journeys = {}
    worker = []

    def __init__(self, journeys, worker):
        super().__init__()
        self.journeys = journeys
        self.worker = worker
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        self.datos_trabajador()
        self.tabla_jornada()
        self.totales_y_firmas()

    def footer(self):
        self.set_font("Helvetica", size=9)
        self.multi_cell(0, 5, "Registro realizado en cumplimiento de los Art. 12.4 c, 34.9 y 35.5 del texto refundido del Estatuto de los Trabajadores.\n"
                              "La empresa conservará los registros ...", 0, 1)
        self.ln(2)

    def datos_trabajador(self, worker=[]):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 6, "Listado Resumen mensual del registro de jornada (detalle horario)", 0, 1, "C")
        self.ln(4)
        self.set_font("Helvetica", "", 10)
        for row in worker:
            self.cell(35, 6, row[0], 0)
            self.cell(60, 6, row[1], 0)
            self.cell(35, 6, row[2], 0)
            self.cell(60, 6, row[3], 0)
            self.ln()

        self.ln(4)

    def tabla_jornada(self):
        self.set_font("Helvetica", "B", 9)
        headers = ["DÍA", "ENTRADA", "SALIDA", "ENTRADA", "SALIDA", "ENTRADA", "SALIDA", "H. ORDIN.", "H. EXTRA", "FIRMA"]
        widths = [10, 20, 20, 20, 20, 20, 20, 22, 25, 40]
        for i in range(len(headers)):
            self.cell(widths[i], 6, headers[i], border=1, align='C')
        self.ln()
        self.set_font("Helvetica", "", 9)
        for day, data in self.journeys.items():
            self.cell(widths[0], 6, str(day), border=1, align='C')
            self.cell(widths[1], 6, str(data['morning'][0]), border=1)
            self.cell(widths[2], 6, str(data['morning'][1]), border=1)
            self.cell(widths[3], 6, str(data['afternoon'][0]), border=1)
            self.cell(widths[4], 6, str(data['afternoon'][1]), border=1)
            self.cell(widths[5], 6, str(data['night'][0]), border=1)
            self.cell(widths[6], 6, str(data['night'][1]), border=1)
            self.cell(widths[7], 6, str(data['ordinary']), border=1, align='C')
            self.cell(widths[8], 6, str(data['extras']), border=1, align='C')
            self.cell(widths[9], 6, "", border=1)

            self.ln()

    def totales_y_firmas(self):
        # Get last day in journeys
        last_day = max(self.journeys.keys()) if self.journeys else 0
        self.ln(5)
        self.cell(0, 6, "TOTAL HRAS.:", 0, 1)

        self.ln(10)
        self.cell(100, 6, "Firma de la empresa:", 0, 0)
        self.cell(80, 6, "Firma del trabajador:", 0, 1)

        self.ln(10)
        self.cell(0, 6, f"A {last_day}", 0, 1)

    def output(self, name):
        super().output(name)

if __name__ == "__main__":
    pdf = MonthlyReportPDF()
    pdf.add_page()
    pdf.datos_trabajador()
    pdf.tabla_jornada()
    pdf.totales_y_firmas()

    pdf.output("registro_jornada.pdf")
