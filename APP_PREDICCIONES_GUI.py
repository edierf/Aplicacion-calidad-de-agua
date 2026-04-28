from pathlib import Path
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox

from PREDICCIONES_CON_MODELO import predecir_desde_excel

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except Exception:
    DND_FILES = None
    TkinterDnD = None


class _BaseVentana(TkinterDnD.Tk if TkinterDnD else tk.Tk):
    pass


class AppPredicciones(_BaseVentana):
    def __init__(self):
        super().__init__()
        self.title("Predicciones de Calidad de Agua")
        self.geometry("780x420")
        self.minsize(720, 360)

        self.ruta_entrada = tk.StringVar()
        self.ruta_salida = tk.StringVar()

        self._crear_interfaz()

    def _crear_interfaz(self):
        frame = tk.Frame(self, padx=18, pady=18)
        frame.pack(fill="both", expand=True)

        titulo = tk.Label(
            frame,
            text="Predicciones de Agua desde Excel",
            font=("Segoe UI", 17, "bold"),
        )
        titulo.pack(anchor="w", pady=(0, 10))

        descripcion = tk.Label(
            frame,
            text=(
                "Arrastra y suelta tu archivo Excel (.xlsx) en la zona inferior. "
                "La salida se guarda automaticamente en la misma carpeta."
            ),
            justify="left",
            fg="#333333",
        )
        descripcion.pack(anchor="w", pady=(0, 10))

        self.zona_drop = tk.Label(
            frame,
            text="Suelta aqui tu archivo Excel",
            relief="ridge",
            borderwidth=2,
            font=("Segoe UI", 13, "bold"),
            bg="#f4f7fb",
            fg="#1f3d63",
            pady=30,
        )
        self.zona_drop.pack(fill="x", pady=(4, 14))

        if DND_FILES is not None:
            self.zona_drop.drop_target_register(DND_FILES)
            self.zona_drop.dnd_bind("<<Drop>>", self._on_drop)
        else:
            self.zona_drop.config(text="Arrastre no disponible. Use el boton Seleccionar Excel")

        fila_btn = tk.Frame(frame)
        fila_btn.pack(fill="x", pady=(0, 10))

        tk.Button(
            fila_btn,
            text="Seleccionar Excel",
            command=self._seleccionar_entrada,
            padx=10,
        ).pack(side="left")

        self.btn_ejecutar = tk.Button(
            fila_btn,
            text="Generar predicciones",
            command=self._ejecutar,
            font=("Segoe UI", 11, "bold"),
            padx=14,
            pady=6,
        )
        self.btn_ejecutar.pack(side="left", padx=(10, 0))

        self.lbl_entrada = tk.Label(frame, text="Entrada: (sin seleccionar)", anchor="w")
        self.lbl_entrada.pack(fill="x", pady=(6, 2))

        self.lbl_salida = tk.Label(frame, text="Salida: (se definira al seleccionar archivo)", anchor="w")
        self.lbl_salida.pack(fill="x", pady=(2, 2))

        self.estado = tk.Label(frame, text="Estado: esperando archivo.", fg="#333333", anchor="w")
        self.estado.pack(fill="x", pady=(8, 0))

    @staticmethod
    def _normalizar_drop_data(data):
        data = data.strip()
        if data.startswith("{") and data.endswith("}"):
            data = data[1:-1]
        return data

    def _on_drop(self, event):
        ruta = self._normalizar_drop_data(event.data)
        self._establecer_entrada(ruta)

    def _seleccionar_entrada(self):
        ruta = filedialog.askopenfilename(
            title="Selecciona el Excel de entrada",
            filetypes=[("Excel", "*.xlsx")],
        )
        if ruta:
            self._establecer_entrada(ruta)

    def _establecer_entrada(self, ruta):
        ruta_path = Path(ruta)
        if not ruta_path.exists() or ruta_path.suffix.lower() != ".xlsx":
            messagebox.showerror("Archivo invalido", "Debes seleccionar un archivo .xlsx existente.")
            return

        self.ruta_entrada.set(str(ruta_path))
        ruta_salida = ruta_path.with_name(f"{ruta_path.stem}_predicciones.xlsx")
        self.ruta_salida.set(str(ruta_salida))

        self.lbl_entrada.config(text=f"Entrada: {self.ruta_entrada.get()}")
        self.lbl_salida.config(text=f"Salida: {self.ruta_salida.get()}")
        self.estado.config(text="Estado: archivo listo para procesar.")

    def _validar_campos(self):
        entrada = self.ruta_entrada.get().strip()
        salida = self.ruta_salida.get().strip()

        if not entrada:
            raise ValueError("Primero arrastra o selecciona un archivo de entrada.")
        if not Path(entrada).exists():
            raise ValueError("El archivo de entrada no existe.")
        if not entrada.lower().endswith(".xlsx"):
            raise ValueError("El archivo de entrada debe ser .xlsx")
        if not salida.lower().endswith(".xlsx"):
            raise ValueError("El archivo de salida debe ser .xlsx")

    def _ejecutar(self):
        try:
            self._validar_campos()
        except Exception as e:
            messagebox.showerror("Datos invalidos", str(e))
            return

        entrada = self.ruta_entrada.get().strip()
        salida = self.ruta_salida.get().strip()

        self.btn_ejecutar.config(state="disabled")
        self.estado.config(text="Estado: ejecutando prediccion...")
        self.update_idletasks()

        try:
            predecir_desde_excel(entrada, salida, verbose=False)
            self.estado.config(text="Estado: prediccion finalizada correctamente.")
            messagebox.showinfo(
                "Proceso finalizado",
                f"Predicciones generadas en:\n{salida}",
            )
        except Exception as e:
            self.estado.config(text="Estado: error durante la prediccion.")
            detalle = f"{e}\n\nDetalle tecnico:\n{traceback.format_exc(limit=2)}"
            messagebox.showerror("Error", detalle)
        finally:
            self.btn_ejecutar.config(state="normal")


def main():
    app = AppPredicciones()
    app.mainloop()


if __name__ == "__main__":
    main()
