from collections import OrderedDict

import gradio as gr
from occultation_detector.difractions import calc_plano, pupilCO, fresnel, spectra, calc_rstar, promedio_PD, add_ruido, extraer_perfil, muestreos, SNR_TAOS2
from occultation_detector.plotter import plot
import pandas as pd


def simulate_lightcurve(mesh_size, earth_translation_speed, object_speed, angle, fps, apparent_magnitude,
                        stellar_classification, d, ua, number_of_wavelengths,
                        toffset, T, b, tno_shape):
    M = int(mesh_size)
    lamb = 600e-9  # Long de onda en [m]
    fps = int(fps)
    nLamb = int(number_of_wavelengths)

    b = d * b
    D = calc_plano(d, lamb, ua)  # Tamano del plano total en [m]
    O1 = pupilCO(M, D, d)  # Objeto 1: circular
    # CALCULAR PATRON CON CONTRIBUCION ESPECTRAL
    z = 1.496e11 * ua  # Distancia del objeto en [m]
    I1 = fresnel(O1, M, D, z, lamb)  # Patron 1 de difraccion monocromatico con fuente puntual
    I1s = spectra(O1, M, D, z, stellar_classification, nLamb)  # Esta funcion calcula el patron cromatico
    # CALCULAR PATRON PARA FUENTE EXTENDIDA
    tipo, R_star = calc_rstar(apparent_magnitude, stellar_classification, ua)  # Funcion para calcular el radio y tipo de la estrella usa estrellas.dat
    I1f = promedio_PD(I1s, R_star, D, M, d)  # Funcion para calcular contribucion de fuente extendida
    # AGREGAR RUIDO DE POISSON
    I1n = add_ruido(I1f, apparent_magnitude)  # Obtener patron de difraccion con ruido
    # EXTRAER PERFIL DE DIFRACCION ojo T--> grados y b --> metros
    xc, yc = extraer_perfil(I1f, M, D, T, b)  # Extraer perfil de difraccion sin ruido
    xb, yb = extraer_perfil(I1n, M, D, T, b)  # Extraer perfil de difraccion con ruido
    # MUESTREAR SEGUN PARAMETROS CONOCIDOS DEFINIDOS AL PRINCIPIO
    x1, y1, x2, y2 = muestreos(yc, D, object_speed, fps, toff=toffset, vE=earth_translation_speed, opangle=angle,
                               ua=ua)  # fUNCION PARA MUESTREAR genera dos tuplas

    return (OrderedDict({
        "D": D,
        "z": z,
        "R_star": R_star,
        "tipo": tipo
    }), OrderedDict({
        "O1": O1,
        "I1": I1,
        "I1s": I1s,
        "I1f": I1f,
        "I1n": I1n,
        "xc": xc,
        "yc": yc,
        "xb": xb,
        "yb": yb,
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
    }))


def update_plot(mesh_size, earth_translation_speed, object_speed, angle, fps, apparent_magnitude,
                stellar_classification, object_diameter, object_distance_au, number_of_wavelengths, offset_pixels,
                reading_direction_degrees, impact_parameter, tno_shape, file):
    snr = SNR_TAOS2(apparent_magnitude)
    if file is not None:
        data = pd.read_csv(file.name, sep=",", header=None)
        print(data)
    response, series = simulate_lightcurve(mesh_size, earth_translation_speed, object_speed, angle, fps,
                                           apparent_magnitude, stellar_classification, object_diameter,
                                           object_distance_au, number_of_wavelengths, offset_pixels,
                                           reading_direction_degrees, impact_parameter, tno_shape)
    return plot(object_diameter, object_distance_au, offset_pixels, reading_direction_degrees, impact_parameter, series,
                response, number_of_wavelengths, apparent_magnitude, snr)


stellar_classifications_choices = [('A0', 0), ('A1', 1), ('A2', 2), ('A3', 3), ('A4', 4), ('A5', 5), ('A7', 6),
                                   ('F0', 7), ('F2', 8), ('F3', 9), ('F5', 10), ('F6', 11), ('F7', 12), ('F8', 13),
                                   ('G0', 14), ('G1', 15), ('G2', 16), ('G5', 17), ('G8', 18), ('K0', 19), ('K1', 20),
                                   ('K2', 21), ('K3', 22), ('K4', 23), ('K5', 24), ('K7', 25), ('M0', 26), ('M1', 27),
                                   ('M2', 28), ('M3', 29), ('M4', 30), ('M5', 31), ('M6', 32), ('M7', 33), ('M8', 34)]
with gr.Blocks() as demo:
    demo.title = "TNO Simulator"
    gr.Markdown("""
        # TNO Simulator
        ## By Joel Castro and sanchezcarlosjr for the TAOS II project.
        """)
    with gr.Row():
        with gr.Column(scale=1, min_width=600):
            mesh_size = gr.Number(label="Mesh size:", value=2 ** 11)
            # velocidad de traslacion de la tierra  en m/s
            earth_translation_speed = gr.Number(label="Earth translation speed:", value=29800)
            # velocidad del cuerpo Pos si va en contra de la direccion de la tierra
            object_speed = gr.Number(label="Object speed:", value=5000)
            # angulo desde oposicion para calcular velocidad tangencial del objeto
            angle = gr.Number(label="Angle:", value=30)
            # frames per second
            fps = gr.Number(label="Fps:", value=20)
            apparent_magnitude = gr.Number(label="Apparent magnitude:", value=12)
            # Seleccion de tipo espectral de estrella # TODO: 1,30
            stellar_classification = gr.Dropdown(choices=stellar_classifications_choices,
                                                 label="Stellar classification:", value=30)
            object_diameter = gr.Number(label="Object diameter (m):", value=3000)
            object_distance_au = gr.Number(label="Object distance (astronomical units):", value=45)
            # nLambs Num de longitudes de onda a considerar para el calculo espectral spectra()
            number_of_wavelengths = gr.Number(label="Number of wavelengths:", value=10)
            # en pixels
            offset_pixels = gr.Number(label="Offset (pixels):", value=0)
            reading_direction_degrees = gr.Slider(label="Reading direction (degrees):", minimum=0, maximum=360, value=0)
            impact_parameter = gr.Number(label="Impact parameter:", value=0)
            file = gr.File(label="File")
            tno_shape = gr.TNOShape(label="Shape")
            btn = gr.Button("Run")
        with gr.Column(scale=2, min_width=600):
            outputs = [*[gr.Plot(label="Plot") for _ in range(0, 8)], gr.JSON()]
    btn.click(fn=update_plot, inputs=[mesh_size, earth_translation_speed, object_speed, angle, fps, apparent_magnitude,
                                      stellar_classification, object_diameter, object_distance_au,
                                      number_of_wavelengths, offset_pixels, reading_direction_degrees, impact_parameter,
                                      tno_shape,file], outputs=outputs)
    demo.launch()
