from django.conf import settings
from fpdf import FPDF

import datetime

from tms.commons import show_exc
from django.db.models.query import QuerySet
from gestion.models import Employee
from decimal import Decimal

class MonthlyReportPDF(FPDF):
    worker_list = []
    start_date = datetime.date.today()
    end_date = datetime.date.today()
    row_height = 6
    worker = None

    def __init__(self, worker, start_date, end_date):
        try:
            if settings.DEBUG:
                print("Initializing MonthlyReportPDF with worker:", worker, "start_date:", start_date, "end_date:", end_date)
            super().__init__()
            if not isinstance(worker, QuerySet):
                self.worker_list = Employee.objects.filter(uuid=worker.uuid)
            else:
                self.worker_list = worker
            self.start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            self.end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

            self.set_auto_page_break(auto=True, margin=15)
            for w in self.worker_list:
                self.worker = w
                self.add_page()
                self.datos_trabajador()
                self.tabla_jornada()
                self.totales_y_firmas()
        except Exception as e:
            print(show_exc(e))
            raise e

    @staticmethod
    def local_time(mydate, tz =None ):
        try:
            from datetime import datetime
            from zoneinfo import ZoneInfo
            if mydate != "":
                utc_now = mydate.replace(tzinfo=ZoneInfo("UTC"))
                canary_time = utc_now.astimezone(ZoneInfo("Atlantic/Canary"))
                canary_time = canary_time.replace(tzinfo=ZoneInfo("UTC"))
                return canary_time
            return mydate
        except Exception as e:
            print(show_exc(e))
            return mydate
        

    def write_cell(self, text, cell, numcells, border=1, padding=5, align='L', fill=False, bg_color=(255, 255, 255), rowspan=1):
        
        page_width = self.w - self.r_margin - self.l_margin
        col_width = page_width / numcells
        if isinstance(cell, list):
            cell_width = sum(page_width / numcells for cell in cell)
            cell = cell[0]
            start_position = self.l_margin + (cell -1) * col_width
        else:
            start_position = self.l_margin + (cell - 1) * col_width
            cell_width = col_width
        self.set_x(start_position)
        if fill:
            self.set_fill_color(*bg_color)
        else:
            self.set_fill_color(255, 255, 255)
        self.cell(cell_width, self.row_height * rowspan, text, border=border, align=align, ln=0, fill=fill)




    def footer(self):
        # Go to 1.5 cm from bottom
        self.set_y(-25)
        self.set_font("Helvetica", "B", size=9)
        self.multi_cell(0, 5, "Registro realizado en cumplimiento de los Art. 12.4 c, 34.9 y 35.5 del texto refundido del Estatuto de los Trabajadores.\n La empresa conservará los registros a que se refiere este precepto durante cuatro años y permanecerán a disposición de las personas trabajadoras, de sus representantes legales y de la Inspección de Trabajo y Seguridad Social.", "T", "C")
        self.ln(2)

    def datos_trabajador(self):
        try:

            self.set_font("Helvetica", "B", 11)
            self.cell(0, 6, "Listado Resumen mensual del registro de jornada (detalle horario)", 0, 1, "C")
            self.ln(4)
            self.set_font("Helvetica", "", 10)
            worker = self.worker

            self.write_cell(f'Empresa: {worker.comp.name.upper()}', 1, 2, 1)
            self.write_cell(f'Trabajador: {self.worker.name.upper()}', 2,2,1)
            self.ln()

            # CIF
            self.write_cell(f'C.I.F.: {worker.comp.nif}', 1, 2, 1)
            self.write_cell(f'N.I.F.: {worker.dni}', 2, 2, 1)
            self.ln()

            self.write_cell(f'Centro de trabajo: {worker.comp.name}', 1, 2, 1)
            self.write_cell(f'N° Afiliación: {worker.affiliation_number}', 2, 2, 1)
            self.ln()

            self.write_cell(f'C.C.C.: {worker.comp.ccc}', 1, 2, 1)
            self.write_cell(f'Mes y año: {self.start_date.strftime("%m/%Y")}', 2, 2, 1)
            self.ln(8)
        except Exception as e:
            print(show_exc(e))
            raise e



    def tabla_jornada(self):
        try:

            grid = [1,[2,3,4,5],[6,7,8,9],[10,11,12,13],[14,15,16,17],[18,19,20]]

            self.set_font("Helvetica", "B", 9)
            self.write_cell("DÍA", grid[0], 20, 1, align='C', rowspan=2, bg_color=(200, 200, 200), fill=True)
            self.write_cell("MAÑANAS", grid[1], 20, 1, align='C', rowspan=1, bg_color=(200, 200, 200), fill=True)
            self.write_cell("TARDES", grid[2], 20, 1, align='C', rowspan=1, bg_color=(200, 200, 200), fill=True)
            self.write_cell("HORAS ORDINARIAS", grid[3], 20, 1, align='C', rowspan=2, bg_color=(200, 200, 200), fill=True)
            self.write_cell("HORAS EXTRA", grid[4], 20, "LTR", align='C', rowspan=1, bg_color=(200, 200, 200), fill=True)
            self.write_cell("FIRMA DE", grid[5], 20, "LTR", align='C', rowspan=1, bg_color=(200, 200, 200), fill=True)
            self.ln()
            # self.set_y(self.get_y() - self.row_height)
            self.write_cell("ENTRADA", [2, 3], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)
            self.write_cell("SALIDA", [4, 5], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)
            self.write_cell("ENTRADA", [6, 7], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)
            self.write_cell("SALIDA", [8, 9], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)

            self.write_cell("COMPLEMENTARIAS", grid[4], 20, "LBR", align='C', rowspan=1, bg_color=(200, 200, 200), fill=True)
            self.write_cell("TRABAJADOR/A", grid[5], 20, "LBR", align='C', rowspan=1, bg_color=(200, 200, 200), fill=True)
            self.ln()

            workdays = self.worker.workdays.filter(ini_date__range = [self.start_date, self.end_date], finish=True).order_by('ini_date')

            self.set_font("Helvetica", "", 9)
            total_seconds = 0
            total_seconds_extra = 0
            total_by_day = {}
            daily_limit = float(self.worker.weekly_hours) / 5. * 3600
            for workday in workdays:
                key_day = workday.ini_date.strftime("%Y%m%d")
                if key_day not in total_by_day:
                    total_by_day[key_day] = 0

                diff_seconds = (workday.end_date - workday.ini_date).total_seconds()
                diff_seconds_extra = 0
                if total_by_day[key_day] + diff_seconds > daily_limit:
                    diff_seconds = daily_limit - total_by_day[key_day]
                    diff_seconds_extra = (workday.end_date - workday.ini_date).total_seconds() - diff_seconds
                    total_by_day[key_day] = daily_limit
                else:
                    total_by_day[key_day] += diff_seconds





                self.write_cell(workday.ini_date.strftime("%d"), 1, 20, 1, align='C')
                if workday.in_morning:
                    self.write_cell(MonthlyReportPDF.local_time(workday.ini_date).strftime("%H:%M"), [2, 3], 20, 1, align='C')
                    self.write_cell(MonthlyReportPDF.local_time(workday.end_date).strftime("%H:%M"), [4, 5], 20, 1, align='C')
                    self.write_cell("", [6, 7], 20, 1, align='C')
                    self.write_cell("", [8, 9], 20, 1, align='C')
                elif workday.in_afternoon:
                    self.write_cell("", [2, 3], 20, 1, align='C')
                    self.write_cell("", [4, 5], 20, 1, align='C')
                    self.write_cell(MonthlyReportPDF.local_time(workday.ini_date).strftime("%H:%M"), [6, 7], 20, 1, align='C')
                    self.write_cell(MonthlyReportPDF.local_time(workday.end_date).strftime("%H:%M"), [8, 9], 20, 1, align='C')
                # diff_seconds = (workday.end_date - workday.ini_date).total_seconds()
                diff_hours = diff_seconds // 3600
                diff_minutes = (diff_seconds % 3600) // 60
                if (diff_seconds_extra > 0) and (diff_seconds < daily_limit):
                    diff_minutes += 1
                total_seconds += (diff_hours * 3600 + diff_minutes * 60)
                self.write_cell(f"{int(diff_hours):02}:{int(diff_minutes):02}", [10, 11, 12, 13], 20, 1, align='C')

                diff_hours_extra = diff_seconds_extra // 3600
                diff_minutes_extra = (diff_seconds_extra % 3600) // 60
                total_seconds_extra += (diff_hours_extra * 3600 + diff_minutes_extra * 60)
                if (diff_seconds_extra > 0):
                    self.write_cell(f"{int(diff_hours_extra):02}:{int(diff_minutes_extra):02}", [14, 15, 16, 17], 20, 1, align='C')
                else:
                    self.write_cell("", [14, 15, 16, 17], 20, 1, align='C')

                self.write_cell("", [18, 19, 20], 20, 1, align='C')
                self.ln()
            
            total_hours = total_seconds // 3600
            total_minutes = (total_seconds % 3600) // 60
            total_hours_extra = total_seconds_extra // 3600
            total_minutes_extra = (total_seconds_extra % 3600) // 60
            self.set_font("Helvetica", "B", 9)
            self.write_cell("TOTAL HORAS", [1,2,3,4,5,6,7,8,9], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)
            self.write_cell(f"{int(total_hours):02}:{int(total_minutes):02}", [10, 11, 12, 13], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)
            self.write_cell(f"{int(total_hours_extra):02}:{int(total_minutes_extra):02}", [14, 15, 16, 17], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)
            self.write_cell("", [18, 19, 20], 20, 1, align='C', bg_color=(200, 200, 200), fill=True)
        except Exception as e:
            print(show_exc(e))
            raise e
            



    def totales_y_firmas(self):
  

        self.ln(10)
        self.write_cell("Firma de la empresa:", [1,2,3,4], 9, '', align="C")
        self.write_cell("Firma del trabajador/a:", [6,7,8,9], 9, '', align="C")
        self.ln()
        self.write_cell("", [1,2,3,4], 9, 'B', align="C", rowspan=4)
        self.write_cell("", [6,7,8,9], 9, 'B', align="C", rowspan=4)
        self.ln(6*4)


        # last_day in format "25 de octubre de 2023" in Spanish
        months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        last_day = f"{self.end_date.day} de {months[self.end_date.month - 1]} de {self.end_date.year}"
        self.ln(20)
        self.write_cell(f"En", 1, 20, "")
        self.write_cell("", list(range(2,16)), 20, "B")
        self.write_cell(f", a {last_day}", 16, 20, 0, align="L")

    def output(self, name):
        super().output(name)

    def output_to_memory(self):
        try:
            return super().output(dest='S').encode('latin1')
        except Exception as e:
            return super().output(dest='S')
        


# if __name__ == "__main__":
#     pdf = MonthlyReportPDF()
#     pdf.add_page()
#     pdf.datos_trabajador()
#     pdf.tabla_jornada()
#     pdf.totales_y_firmas()

#     pdf.output("registro_jornada.pdf")
