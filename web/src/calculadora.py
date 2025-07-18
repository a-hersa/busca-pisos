import numpy_financial as npf
from src.precios import PreciosAlquiler
from unidecode import unidecode

class DatosCalculadora:
    def __init__(self, nombre, precio, metros, poblacion):
            precioMetroAlquiler = PreciosAlquiler()
            self.nombre = str(nombre)
            self.precio = int(precio)
            self.metros = int(metros)
            self.poblacion = str(poblacion)
            self.poblacion = unidecode(self.poblacion.lower().split(", ")[-1].replace(" ", "").replace("'", ""))
            self.p_compra = int(precio)
            self.itp = int(float(precio) * 0.1)
            self.reforma = 6000
            self.notaria = 1000
            self.registro = 0
            self.agencia = 0
            self.tasacion = 200
            self.total_compra = self.p_compra+self.itp+self.notaria+self.registro+self.reforma+self.agencia+self.tasacion
            self.ibi = 450
            self.basuras = 0
            self.comunidad = 400
            self.seguros = 400
            self.total_gastos = self.ibi+self.basuras+self.seguros+self.comunidad
            self.alquiler = int(float(self.metros) * float(getattr(precioMetroAlquiler, self.poblacion, 12)))
            self.financiado = 80
            self.hipoteca = int((self.financiado/100)*self.p_compra)
            self.a_aportar = int(self.p_compra+self.itp+self.reforma+self.notaria+self.registro+self.agencia+self.tasacion-self.hipoteca)
            self.plazo = 30
            self.interes_anuales = 2.5/100
            self.interes_mensuales = self.interes_anuales/12
            self.cuota = -1*npf.pmt(self.interes_mensuales, nper=self.plazo*12, pv=self.hipoteca, fv=0)
            self.cuota_intereses = ((self.cuota*12*self.plazo)-self.hipoteca)/(self.plazo*12)
            self.cuota_amortizacion = self.cuota-self.cuota_intereses
            self.r_bruta = ((self.alquiler*12)/self.total_compra)
            self.r_neta = ((self.alquiler*12)-self.total_gastos-(self.cuota_intereses*12))/self.total_compra
            self.c_flow = self.alquiler-self.cuota-self.total_gastos/12
            self.c_oncash = (self.c_flow*12)/self.a_aportar
            self.roce = 12*(self.c_flow+self.cuota_amortizacion)/self.a_aportar

def calculadora(nombre, precio, metros, poblacion):
        resultados = []
        poblacion = unidecode(poblacion.lower().split(", ")[-1].replace(" ", "").replace("'", ""))

        precioMetroAlquiler = PreciosAlquiler()
        resultados.append(precioMetroAlquiler)

        nombre = str(nombre)
        resultados.append(nombre)

        precio = int(precio)
        resultados.append(precio)

        metros = int(metros)
        resultados.append(metros)

        poblacion = str(poblacion)
        resultados.append(poblacion)

        p_compra = int(precio)
        resultados.append(p_compra)


        itp = int(float(precio) * 0.1)
        resultados.append(itp)

        reforma = 6000
        resultados.append(reforma)

        notaria = 1000
        resultados.append(notaria)

        registro = 0
        resultados.append(registro)

        agencia = 0
        resultados.append(agencia)


        tasacion = 200
        resultados.append(tasacion)

        total_compra = p_compra+itp+notaria+registro+reforma+agencia+tasacion
        resultados.append(total_compra)

        ibi = 450
        resultados.append(ibi)

        basuras = 0
        resultados.append(basuras)

        comunidad = 400
        resultados.append(comunidad)

        seguros = 400
        resultados.append(seguros)

        total_gastos = ibi+basuras+seguros+comunidad
        resultados.append(total_gastos)

        alquiler = int(float(metros) * float(getattr(precioMetroAlquiler, poblacion, 12)))
        resultados.append(alquiler)

        financiado = 80
        resultados.append(financiado)

        hipoteca = int((financiado/100)*p_compra)
        resultados.append(hipoteca)

        a_aportar = int(p_compra+itp+reforma+notaria+registro+agencia+tasacion-hipoteca)
        resultados.append(a_aportar)

        plazo = 30
        resultados.append(plazo)

        interes_anuales = 2.5/100
        resultados.append(interes_anuales)

        interes_mensuales = interes_anuales/12
        resultados.append(interes_mensuales)

        cuota = -1*npf.pmt(interes_mensuales, nper=plazo*12, pv=hipoteca, fv=0)
        resultados.append(cuota)

        cuota_intereses = ((cuota*12*plazo)-hipoteca)/(plazo*12)
        resultados.append(cuota_intereses)

        cuota_amortizacion = cuota-cuota_intereses
        resultados.append(cuota_amortizacion)

        r_bruta = ((alquiler*12)/total_compra)
        resultados.append(r_bruta)

        r_neta = ((alquiler*12)-total_gastos-(cuota_intereses*12))/total_compra
        resultados.append(r_neta)

        c_flow = alquiler-cuota-total_gastos/12
        resultados.append(c_flow)

        c_oncash = (c_flow*12)/a_aportar
        resultados.append(c_oncash)

        roce = 12*(c_flow+cuota_amortizacion)/a_aportar
        resultados.append(roce)

        return resultados